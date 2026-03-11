# Conversations Module

> Module: `climate/modules/conversations`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [Data Model](#data-model)
3. [Conversation Lifecycle](#conversation-lifecycle)
4. [Conversation Types](#conversation-types)
5. [Priority Classification](#priority-classification)
6. [Disposition Statuses](#disposition-statuses)
7. [Lead Sources](#lead-sources)
8. [Follow-up System](#follow-up-system)
9. [Conversation Closure](#conversation-closure)
10. [Frontend Components](#frontend-components)
11. [Backend Controllers](#backend-controllers)
12. [Queue Integration](#queue-integration)
13. [Cross-References](#cross-references)

---

## Overview

Conversations are the central CRM entity representing an ongoing engagement with a customer. They track the lifecycle of a lead from initial contact through qualification or disqualification, and serve as the container for messages, notes, follow-ups, and assignments.

---

## Data Model

### tbl_open_conversations

```
Conversation
├── Identity: conversation_id (PK), contact_id (handle), account_id
├── Assignment: user_id (agent), source_id (lead source)
├── Classification: conversation_type, conversation_stage, priority
├── Status: status (open/closed), disposition_status
├── Tracking: call_attempts, opportunity_id
├── Timeline: opened_at, closed_at, last_activity_at
└── Related:
    ├── tbl_whatsapp_messages (conversation_id)
    ├── tbl_call_logs (conversation_id)
    └── tbl_contact_assignment_history (conversation_id)
```

---

## Conversation Lifecycle

### Stage Progression

```
┌─────────┐    Agent tries     ┌───────────┐    Successful    ┌───────────┐
│   NEW   │────to reach out───►│ ATTEMPTED │────contact──────►│ CONTACTED │
└─────────┘                    └───────────┘                  └─────┬─────┘
                                                                    │
                                                                    │ Ongoing
                                                                    │ engagement
                                                                    ▼
                                                              ┌───────────┐
                                                              │ NURTURING │
                                                              └─────┬─────┘
                                                                    │
                                                         ┌──────────┴──────────┐
                                                         ▼                     ▼
                                                   ┌───────────┐        ┌────────────┐
                                                   │ QUALIFIED │        │UNQUALIFIED │
                                                   │           │        │            │
                                                   │ → Create  │        │ Requires   │
                                                   │   Order   │        │ disposition│
                                                   │ → Create  │        │ reason     │
                                                   │   Opp.    │        │            │
                                                   │ → Close   │        │ → Close    │
                                                   │   convo   │        │   convo    │
                                                   └───────────┘        └────────────┘
```

### Stage Definitions

| Stage | Description | Trigger |
|-------|-------------|---------|
| `new` | Lead just arrived, no agent action yet | Auto on conversation creation |
| `attempted` | Agent tried to reach out (call, message) | Agent marks manually |
| `contacted` | Successful first communication | Agent marks after response |
| `nurturing` | Ongoing engagement, building relationship | Agent marks during follow-up |
| `qualified` | Ready for order/opportunity | Auto on order creation, or manual |
| `unqualified` | Lead disqualified | Agent marks with disposition reason |

### Stage Transitions

```
Valid transitions:
new → attempted
new → contacted (skip attempted)
attempted → contacted
contacted → nurturing
nurturing → qualified
nurturing → unqualified
contacted → qualified (fast track)
contacted → unqualified
any → new (reopen on new inbound message)
```

The `OpenConversations::updateStage()` method handles stage transitions with real-time queue notification:

```php
public function updateStage()
{
    $request = json_decode(file_get_contents('php://input'), true);

    $conversationId = $request['conversation_id'];
    $stage = $request['stage'];
    $dispositionStatus = $request['disposition_status'] ?? null;

    $CI = &get_instance();
    $authData = $CI->AuthData ?? [];
    $agentId = $authData['agent_id'] ?? null;

    $success = $this->_conversations->updateConversationStage(
        $conversationId, $stage, $dispositionStatus, $agentId
    );

    if ($success) {
        // If marked as unqualified, close the conversation
        if ($stage === 'unqualified') {
            $this->_conversations->closeConversation($conversationId);
        }

        // Push to queue for real-time updates
        $stageData = [
            'chatType' => 'conversation_stage_updated',
            'conversation_id' => $conversationId,
            'stage' => $stage,
            'disposition_status' => $dispositionStatus,
            'timestamp' => time()
        ];
        $this->queue->push($stageData, 'conversation_stage_update');
    }
}
```

---

## Conversation Types

| Type | Description | Lifecycle |
|------|-------------|-----------|
| `lead` | Initial contact, not yet a customer | Start here |
| `opportunity` | Qualified lead with potential deal | Promoted from lead |
| `customer` | Existing customer engagement | For repeat customers |

---

## Priority Classification

| Priority | Description | UI Treatment |
|----------|-------------|-------------|
| `hot` | High priority, immediate action needed | Red indicator |
| `warm` | Active engagement, moderate priority | Orange indicator |
| `cold` | Low priority, needs nurturing | Blue indicator |

---

## Disposition Statuses

When a conversation is marked as `unqualified`, a disposition reason is required:

### RNR (Reach Not Responding)

| Status | Description |
|--------|-------------|
| `rnr1` | First attempt — no response |
| `rnr2` | Second attempt — no response |
| `rnr3` | Third attempt — no response (auto-close) |

### Rejection Reasons

| Status | Description |
|--------|-------------|
| `not_interested` | Customer explicitly declined |
| `price_too_high` | Price objection |
| `wrong_timing` | Bad timing for purchase |
| `need_approval` | Customer needs internal approval |
| `competitor_chosen` | Chose a competing vendor |
| `budget_issues` | Budget constraints |
| `decision_maker_unavailable` | Can't reach the decision maker |
| `need_discount` | Requires discount to proceed |
| `credit_needed` | Requires credit terms |
| `need_more_time` | Wants to decide later |
| `customer_need_cod` | Requires cash on delivery |
| `non_contact` | Unable to establish contact at all |
| `invalid` | Invalid lead data (wrong number, spam, etc.) |
| `other` | Other reasons (free text) |

---

## Lead Sources

Conversations track their origin via `source_id` → `tbl_contact_sources`:

| Source | Channel | Entry Method |
|--------|---------|-------------|
| WhatsApp | WhatsApp Business API | Webhook (automatic) |
| Phone Call | Telephony | Manual / call log |
| JustDial | JustDial API | Webhook (automatic) |
| IndiaMart | IndiaMart | Cron sync |
| Facebook | Facebook Lead Forms | Webhook (automatic) |
| Email | Email | Manual |
| Instagram | Instagram | Manual |
| Offline | In-person | Manual entry |

---

## Follow-up System

### Scheduling Follow-ups

```
Agent schedules follow-up
    │
    ├── Date/time
    ├── Follow-up notes
    └── Priority
        │
        ▼
Stored in database
        │
        ▼
Cron: processScheduledFollowups()
    │
    ├── Check for due follow-ups
    ├── Send FCM notification to agent
    └── Update pendingFollowupsTrigger
        │
        ▼
Agent sees reminder in UI
    │
    ├── Take action
    └── Mark follow-up complete
        POST /whatsapp/setFollowUpCompleted
```

---

## Conversation Closure

### Qualified Closure

When a conversation results in a sale:
1. Agent creates an order → `Orders::save()` auto-closes
2. Or agent manually marks as `qualified`
3. Opportunity created/updated in `tbl_opportunities`
4. `closed_at` timestamp recorded
5. `status = 'closed'`, `conversation_stage = 'qualified'`

### Unqualified Closure

When a lead is disqualified:
1. Agent updates stage to `unqualified`
2. Must provide `disposition_status` (reason)
3. Conversation closed automatically
4. `closed_at` timestamp recorded

### Reopening

If a new inbound message arrives on a closed conversation:
- System can reopen the conversation
- Stage resets to `new`
- Agent re-engaged

---

## Frontend Components

### Conversation List (`conversations-list/`)

```
┌─────────────────────────────────────┐
│ Filters: [Stage] [Priority] [Agent] │
│         [Date Range] [Search]       │
├─────────────────────────────────────┤
│ ● Abhay Singh          Hot    New   │
│   Last: "Interested in turmeric"    │
│   2 min ago                         │
├─────────────────────────────────────┤
│ ● Priya Reddy          Warm  Nurt. │
│   Last: "Please send quote"        │
│   15 min ago                        │
├─────────────────────────────────────┤
│ ● Rajesh Kumar          Cold  Att. │
│   Last: Missed call                 │
│   2 hours ago                       │
└─────────────────────────────────────┘
```

The component uses `OnPush` change detection and manages multiple subscriptions:

```typescript
@Component({
  selector: 'app-conversations-list',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ConversationsListComponent implements OnInit, OnDestroy {
  conversations: WhatsAppContact[] = [];
  filters: any;
  start = 0;
  limit = 50;

  // Mandatory followup queue management
  pendingFollowupQueue: PendingFollowupConversation[] = [];
  private readonly MAX_QUEUE_SIZE = 20;
  private processedFollowupConversations = new Set<number>();
}
```

**Features**:
- Real-time updates via WebSocket
- Unread message count badges
- Filter state persisted to localStorage
- Sort by last activity
- Debounced search with animated placeholder

### Stage Update UI

Agent can update conversation stage via dropdown or quick actions. Each stage transition may trigger additional prompts (e.g., disposition reason for unqualified). Stage changes are immediate with optimistic UI updates.

---

## Backend Controllers

### OpenConversations Controller

| Method | HTTP | Capability | Description |
|--------|------|------------|-------------|
| `updateStage()` | POST | `user` | Update stage with validation |
| `checkFollowupRequired()` | GET | `user` | Check pending follow-ups |

### ConversationTransfer Controller

| Method | HTTP | Capability | Description |
|--------|------|------------|-------------|
| `transfer()` | POST | `conversations.transfer` | Transfer between agents |

### Related Models

| Model | Purpose |
|-------|---------|
| `OpenConversationsModel` | Conversation CRUD and queries |
| `ConversationMessagesModel` | Message operations |
| `ConversationTransferModel` | Transfer operations |
| `ContactSourcesModel` | Lead source management |

---

## Queue Integration

Conversation updates push to Redis queue for real-time notifications:

```
Stage change / New message / Transfer
    │
    ▼
Queue_helper::push('conversation_update', {
    conversation_id: 123,
    event: 'stage_change',
    data: { new_stage: 'contacted' }
})
    │
    ▼
WebSocket broadcast → All connected agents
    │
    ▼
Frontend: conversationUpdatedTrigger → Refresh list
```

---

## Cross-References

| Document | Path |
|----------|------|
| CRM Tables (Conversations schema) | `03-database-design/crm-tables.md` |
| WhatsApp Integration | `04-core-modules/whatsapp-integration.md` |
| Assignment Management | `04-core-modules/assignment-management.md` |
| Conversations API | `05-api-documentation/conversations-api.md` |
| Conversation Lifecycle Flow | `06-data-flow/conversation-lifecycle.md` |
| Communication Patterns | `01-system-architecture/communication-patterns.md` |
