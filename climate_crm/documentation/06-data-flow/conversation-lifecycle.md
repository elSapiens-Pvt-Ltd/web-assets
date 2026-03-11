> Module: climate/data-flow/conversation-lifecycle
> Last updated: 2026-03-11

# Conversation Lifecycle Flow

## Table of Contents

- [Overview](#overview)
- [Complete Lifecycle Diagram](#complete-lifecycle-diagram)
- [Stage 1: NEW](#stage-1-new)
- [Stage 2: ATTEMPTED](#stage-2-attempted)
- [Stage 3: CONTACTED](#stage-3-contacted)
- [Stage 4: NURTURING](#stage-4-nurturing)
- [Stage 5a: QUALIFIED](#stage-5a-qualified)
- [Stage 5b: UNQUALIFIED](#stage-5b-unqualified)
- [Stage 6: CONVERTED (Order Created)](#stage-6-converted-order-created)
- [Conversation Reopening](#conversation-reopening)
- [Follow-Up System](#follow-up-system)
- [Stage Transition Summary](#stage-transition-summary)
- [Database Fields (tbl_open_conversations)](#database-fields-tbl_open_conversations)
- [Cross-References](#cross-references)

---

## Overview

This document traces a conversation from lead capture through qualification, covering every stage transition and the data changes at each step.

---

## Complete Lifecycle Diagram

```
                    ┌──────────────┐
                    │  NEW MESSAGE │ (WhatsApp, JustDial, etc.)
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │     NEW      │ conversation_stage = 'new'
                    │              │ status = 'open'
                    └──────┬───────┘
                           │ Agent sends first message
                    ┌──────▼───────┐
                    │  ATTEMPTED   │ conversation_stage = 'attempted'
                    └──────┬───────┘
                           │ Customer replies
                    ┌──────▼───────┐
                    │  CONTACTED   │ conversation_stage = 'contacted'
                    └──────┬───────┘
                           │ Agent continues engagement
                    ┌──────▼───────┐
                    │  NURTURING   │ conversation_stage = 'nurturing'
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼                         ▼
    ┌──────────────┐          ┌──────────────────┐
    │  QUALIFIED   │          │  UNQUALIFIED     │
    │              │          │                  │
    │ Ready for    │          │ Not interested   │
    │ order        │          │ (with reason)    │
    └──────┬───────┘          └──────────────────┘
           │ Order created
    ┌──────▼───────┐
    │  CONVERTED   │ status = 'closed'
    │              │ conversation_stage = 'converted'
    └──────────────┘
```

---

## Stage 1: NEW

### Trigger
A new message arrives from an unknown or known contact without an open conversation.

### Data Flow

```
Incoming message
    │
    ├── ContactMessageModel::processIncomingMessage()
    │
    ├── Handle lookup (temp_tbl_contact_handles)
    │   ├── Known → get contact_id, account_id
    │   └── Unknown → create contact + handle
    │
    ├── Agent assignment (AgentAssignmentHelper)
    │   → Priority: account owner > open convo > previous > round-robin
    │
    └── Create tbl_open_conversations:
        ├── status = 'open'
        ├── conversation_stage = 'new'
        ├── conversation_type = 'contact'
        ├── agent_id = assigned agent
        ├── contact_id = contact
        ├── handle_value = normalized phone
        ├── source_id = lead source
        ├── allocated_at = NOW()
        └── last_activity_at = NOW()
```

### Frontend
- Conversation appears in agent's **New** tab
- Shows unread badge
- Contact name from WhatsApp profile or "Unknown"

---

## Stage 2: ATTEMPTED

### Trigger
Agent sends the first outbound message to the customer.

### Data Flow

```
Agent sends message via ChatWindowComponent
    │
    ├── POST /Whatsapp/sendTextMessage
    │
    ├── Message stored in tbl_whatsapp_messages
    │   sender = 'agent'
    │
    └── Stage transition (if stage = 'new'):
        ├── UPDATE tbl_open_conversations
        │   SET conversation_stage = 'attempted'
        ├── Insert system message:
        │   "Stage changed to Attempted"
        └── Push stage update via WebSocket
```

### Key Rule
This transition happens **automatically** when the agent sends the first message. No manual action required.

---

## Stage 3: CONTACTED

### Trigger
Customer replies to an agent message (conversation was in 'attempted' stage).

### Data Flow

```
Customer message received
    │
    ├── ContactMessageModel::processIncomingMessage()
    │
    ├── Find existing open conversation
    │
    └── Stage transition (if stage = 'attempted'):
        ├── UPDATE tbl_open_conversations
        │   SET conversation_stage = 'contacted'
        ├── Clear any RNR (Reached Not Reachable) disposition
        ├── Insert system message:
        │   "Stage changed to Contacted"
        └── Push stage update via WebSocket
```

### Key Rule
This transition is **automatic** — triggered by the customer's first reply to an agent message.

---

## Stage 4: NURTURING

### Trigger
Agent manually sets the stage to 'nurturing' when the lead shows interest but isn't ready to buy.

### Data Flow

```
Agent clicks "Nurturing" in conversation actions
    │
    ├── POST /openconversations/updateStage
    │   { conversation_id, stage: 'nurturing' }
    │
    └── Backend:
        ├── UPDATE tbl_open_conversations
        │   SET conversation_stage = 'nurturing'
        ├── Insert system message
        └── Push stage update
```

---

## Stage 5a: QUALIFIED

### Trigger
Agent marks the conversation as qualified — the customer is ready for an order.

### Data Flow

```
Agent marks as "Qualified"
    │
    ├── POST /openconversations/updateStage
    │   { conversation_id, stage: 'qualified' }
    │
    └── Backend:
        ├── UPDATE tbl_open_conversations
        │   SET conversation_stage = 'qualified'
        ├── Create/update tbl_opportunities
        │   opportunity_status = 'qualified'
        └── Insert system message
```

---

## Stage 5b: UNQUALIFIED

### Trigger
Agent marks the conversation as unqualified with a disposition reason.

### Data Flow

```
Agent marks as "Unqualified" + selects reason
    │
    ├── POST /openconversations/updateStage
    │   { conversation_id, stage: 'unqualified',
    │     disposition: 'price_too_high' }
    │
    └── Backend:
        ├── UPDATE tbl_open_conversations
        │   SET conversation_stage = 'unqualified'
        │   SET disposition = reason
        │   SET status = 'closed'
        │   SET closed_at = NOW()
        ├── Update tbl_opportunities (if exists)
        │   opportunity_status = 'lost'
        └── Insert system message with reason
```

### Disposition Reasons

| Disposition | Description |
|-------------|-------------|
| `price_too_high` | Customer finds pricing too expensive |
| `not_interested` | General disinterest |
| `rnr_1` / `rnr_2` / `rnr_3` | Reached Not Reachable (multiple attempts) |
| `competitor_chosen` | Customer chose a competitor |
| `budget_issues` | Budget constraints |
| `wrong_number` | Invalid contact |
| `duplicate` | Duplicate lead |
| `test_lead` | Test/spam lead |
| `location_issue` | Geographic mismatch |
| `quality_concern` | Product quality concerns |
| `moq_issue` | Minimum order quantity too high |
| `already_customer` | Existing customer |
| `other` | Other reason (with notes) |

---

## Stage 6: CONVERTED (Order Created)

### Trigger
An order is created for the customer, either from the conversation or directly.

### Data Flow

```
Order created via Orders::save()
    │
    ├── If conversation_id provided:
    │   ├── UPDATE tbl_open_conversations
    │   │   SET status = 'closed'
    │   │   SET conversation_stage = 'converted'
    │   │   SET closed_at = NOW()
    │   │
    │   ├── Create/update tbl_opportunities
    │   │   ├── Link to order_id
    │   │   ├── Set opportunity_status = 'won'
    │   │   └── Set order_value
    │   │
    │   └── Insert system message:
    │       "🛒 Order Created - Order #: {id}"
    │
    └── If no conversation_id:
        ├── Find open conversation by contact_id
        ├── If found → close as 'converted' (same as above)
        └── Create opportunity for CRM tracking
```

---

## Conversation Reopening

Closed conversations can be reopened when a customer sends a new message:

```
New message from customer with closed conversation
    │
    ├── ContactMessageModel::processIncomingMessage()
    │
    ├── No open conversation found for contact
    │
    └── Create NEW conversation:
        ├── conversation_stage = 'new'
        ├── status = 'open'
        ├── Links to same contact_id/account_id
        └── Agent assignment runs again

Note: The old conversation remains closed.
A new conversation_id is created.
```

---

## Follow-Up System

Follow-ups interact with the conversation lifecycle:

```
Agent schedules follow-up
    │
    ├── POST /whatsapp/createFollowup
    │   { conversation_id, followup_date, notes }
    │
    ├── Insert tbl_conversation_followups
    │   status = 'pending'
    │
    └── Cron: processScheduledFollowups()
        (runs every 5-10 minutes)
        │
        ├── Find due follow-ups
        ├── Push notification to agent
        └── Show in "Scheduled" tab on frontend
```

### Mandatory Follow-Up Queue

The frontend enforces follow-up scheduling for certain stages:

```
Agent processes conversation
    │
    ├── If stage = 'contacted' or 'nurturing':
    │   └── Must schedule follow-up before moving to next conversation
    │       (mandatory follow-up queue forces this)
    │
    └── If stage = 'new' or 'attempted':
        └── Follow-up optional
```

---

## Stage Transition Summary

| From | To | Trigger | Method |
|------|-----|---------|--------|
| — | `new` | New message, no open conversation | Automatic |
| `new` | `attempted` | Agent sends first message | Automatic |
| `attempted` | `contacted` | Customer replies | Automatic |
| `contacted` | `nurturing` | Agent sets manually | Manual |
| Any | `qualified` | Agent marks as qualified | Manual |
| Any | `unqualified` | Agent marks with reason | Manual |
| `qualified` | `converted` | Order created | Automatic |

---

## Database Fields (tbl_open_conversations)

| Field | Description |
|-------|-------------|
| `conversation_id` | Primary key |
| `status` | 'open' or 'closed' |
| `conversation_stage` | Current lifecycle stage |
| `conversation_type` | 'contact' or 'opportunity' |
| `disposition` | Unqualified reason (if applicable) |
| `agent_id` | Currently assigned agent |
| `contact_id` | Linked contact |
| `account_id` | Linked account |
| `handle_value` | Contact phone/email |
| `source_id` | Lead source reference |
| `unread` | Unread message count |
| `allocated_at` | When agent was assigned |
| `last_activity_at` | Last message timestamp |
| `closed_at` | When conversation was closed |
| `transferred_at` | Last transfer timestamp |

---

## Cross-References

**Core Modules**
- [`04-core-modules/conversations.md`](../04-core-modules/conversations.md) — Stage update logic, disposition handling, and conversation state management
- [`04-core-modules/whatsapp-integration.md`](../04-core-modules/whatsapp-integration.md) — Automatic stage transitions triggered by inbound messages
- [`04-core-modules/order-management.md`](../04-core-modules/order-management.md) — Order creation that triggers the converted stage transition

**API Documentation**
- [`05-api-documentation/conversations-api.md`](../05-api-documentation/conversations-api.md) — Stage update, disposition, and follow-up scheduling endpoints
- [`05-api-documentation/orders-api.md`](../05-api-documentation/orders-api.md) — Order save endpoint that closes and converts the conversation

**Database Design**
- [`03-database-design/crm-tables.md`](../03-database-design/crm-tables.md) — `tbl_open_conversations` field definitions and stage values

**Related Data Flows**
- [`06-data-flow/message-flow.md`](./message-flow.md) — Message events that drive automatic stage transitions
- [`06-data-flow/assignment-flow.md`](./assignment-flow.md) — Agent assignment that occurs when a new conversation is created
- [`06-data-flow/order-flow.md`](./order-flow.md) — Order creation flow that closes conversations as converted
