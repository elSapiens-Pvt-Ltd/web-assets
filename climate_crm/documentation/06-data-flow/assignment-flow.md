> Module: climate/data-flow/assignment-flow
> Last updated: 2026-03-11

# Assignment Flow

## Table of Contents

- [Overview](#overview)
- [Agent Assignment Priority System](#agent-assignment-priority-system)
- [Leave Status Logic](#leave-status-logic)
- [Transfer Flow](#transfer-flow)
  - [Agent-to-Agent Transfer](#agent-to-agent-transfer)
  - [Transfer Scope Options](#transfer-scope-options)
- [Account-Level Transfer](#account-level-transfer)
- [Initial Assignment Recording](#initial-assignment-recording)
- [Assignment History Timeline](#assignment-history-timeline)
- [Lifecycle Assignment Events](#lifecycle-assignment-events)
- [Workload Tracking](#workload-tracking)
- [Database Tables](#database-tables)
- [Cross-References](#cross-references)

---

## Overview

This document describes how contacts and conversations are assigned to agents — covering initial assignment, transfers, reassignment, and the round-robin distribution system.

---

## Agent Assignment Priority System

When a new message arrives and needs agent assignment, the system follows a 4-level priority:

```
AgentAssignmentHelper::getAgentForHandle($handle_value)
    │
    ▼
┌──────────────────────────────────────────────────┐
│ Priority 1: ACCOUNT OWNER                        │
│                                                  │
│ Check: temp_tbl_contact_handles → contact_id     │
│        → temp_tbl_accounts.account_owner_id      │
│        → tbl_users (active, not deleted)         │
│                                                  │
│ If account has an active owner → assign to owner │
└──────────┬───────────────────────────────────────┘
           │ not found
           ▼
┌──────────────────────────────────────────────────┐
│ Priority 2: OPEN CONVERSATION AGENT              │
│                                                  │
│ Check: tbl_open_conversations                    │
│        WHERE status='open' AND contact_id        │
│        AND agent is active                       │
│                                                  │
│ Sort: last_activity_at DESC                      │
│ If found → assign to most recently active agent  │
└──────────┬───────────────────────────────────────┘
           │ not found
           ▼
┌──────────────────────────────────────────────────┐
│ Priority 3: PREVIOUS CONVERSATION AGENT          │
│                                                  │
│ Check: tbl_open_conversations                    │
│        WHERE status='closed' AND contact_id      │
│        AND agent is active                       │
│                                                  │
│ Sort: closed_at DESC (most recent)               │
│ If found → assign to last agent who handled      │
└──────────┬───────────────────────────────────────┘
           │ not found
           ▼
┌──────────────────────────────────────────────────┐
│ Priority 4: ROUND-ROBIN                          │
│                                                  │
│ 1. Load agent rotation from tbl_settings         │
│    setting_name='agent_allocation'               │
│    field_value = JSON [{agent_id, order_no}]     │
│                                                  │
│ 2. Start from last_assigned + 1                  │
│                                                  │
│ 3. For each agent in rotation:                   │
│    ├── Check tbl_telecommunication_agents        │
│    │   (is_active = 1)                           │
│    ├── Check tbl_users (not deleted)             │
│    ├── Check tbl_user_leaves:                    │
│    │   ├── full_day → skip                       │
│    │   ├── first_half → skip if before cutoff    │
│    │   └── second_half → skip if after cutoff    │
│    └── Check tbl_company_work_hours              │
│        (within working hours)                    │
│                                                  │
│ 4. First available agent gets assignment         │
│ 5. Update tbl_settings.last_assigned             │
│                                                  │
│ If no agent available → agent_id = 0             │
│ (unassigned, shows in unassigned queue)          │
└──────────────────────────────────────────────────┘
```

---

## Leave Status Logic

```
Agent leave check for today:

tbl_user_leaves WHERE user_id AND leave_date = TODAY AND status = 'approved'
    │
    ├── leave_type = 'full_day'
    │   → Agent unavailable all day
    │
    ├── leave_type = 'first_half'
    │   → Unavailable until tbl_company_work_hours.first_half_end
    │   → Available after that time
    │
    └── leave_type = 'second_half'
        → Available until tbl_company_work_hours.second_half_start
        → Unavailable after that time
```

---

## Transfer Flow

### Agent-to-Agent Transfer

```
┌─────────────────┐
│ Agent A opens    │
│ transfer dialog  │
│ in ChatWindow    │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────────────┐
│ Frontend: Select target agent + reason           │
│                                                  │
│ POST /conversationtransfer/execute               │
│ {                                                │
│   conversation_id: 123,                          │
│   to_agent_id: 8,                                │
│   transfer_reason: "Customer prefers Hindi",     │
│   transfer_notes: "Language preference"          │
│ }                                                │
└────────┬─────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────┐
│ Backend: ConversationTransfer::execute()          │
│                                                  │
│ START TRANSACTION                                │
│                                                  │
│ 1. Validate target agent exists and is active    │
│                                                  │
│ 2. Update tbl_open_conversations:                │
│    SET agent_id = to_agent_id                    │
│    SET transferred_at = NOW()                    │
│                                                  │
│ 3. Insert tbl_unified_transfer_log:              │
│    ├── conversation_id                           │
│    ├── from_agent_id, to_agent_id                │
│    ├── account_id                                │
│    ├── transfer_reason, transfer_notes           │
│    └── created_by_user_id                        │
│                                                  │
│ 4. Insert tbl_contact_assignment_history:        │
│    ├── contact_id                                │
│    ├── assigned_to_user_id = to_user_id          │
│    ├── previous_user_id = from_user_id           │
│    ├── assignment_type = 'transfer'              │
│    ├── assignment_method = 'manual'              │
│    ├── transfer_reason, transfer_notes           │
│    └── source_system = 'open_conversations'      │
│                                                  │
│ COMMIT TRANSACTION                               │
└────────┬─────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────┐
│ Real-Time Notification                           │
│                                                  │
│ 1. Redis queue::pushTransferUpdate()             │
│ 2. WebSocket → Agent A: conversation removed     │
│ 3. WebSocket → Agent B: new conversation added   │
│ 4. FCM push notification to Agent B              │
└──────────────────────────────────────────────────┘
```

### Transfer Scope Options

| Scope | What Gets Transferred |
|-------|----------------------|
| `conversation_id` | Single conversation |
| `account_id` | All open conversations for an account |
| `opportunity_id` | Specific opportunity |

---

## Account-Level Transfer

```
Manager selects "Transfer All" for an account
    │
    ▼
ConversationTransfer::execute()
    │
    ├── Find all open conversations WHERE account_id
    ├── For each conversation:
    │   ├── Update agent_id
    │   ├── Record in unified_transfer_log
    │   └── Record in assignment_history
    └── Batch WebSocket notifications
```

---

## Initial Assignment Recording

When a new conversation is created, the assignment is recorded:

```
ContactMessageModel::processIncomingMessage()
    │
    ├── AgentAssignmentHelper assigns agent
    │
    ├── Create tbl_open_conversations:
    │   agent_id = assigned_agent
    │
    └── Record in tbl_contact_assignment_history:
        ├── assignment_type = 'initial'
        ├── assignment_method = 'automatic' / 'round_robin'
        ├── assigned_to_user_id = agent's user_id
        ├── previous_user_id = NULL (first assignment)
        └── source_system = 'open_conversations'
```

---

## Assignment History Timeline

The timeline API provides a complete audit trail:

```
GET /assignmenthistory/timeline/{contact_id}?page=1&per_page=20
    │
    ▼
ContactAssignmentHistoryModel::getContactTimelinePaginated()
    │
    ├── JOIN tbl_users (for agent names)
    ├── ORDER BY assigned_at DESC
    └── Return paginated results with:
        ├── assignment_type (initial/transfer/reassignment/...)
        ├── assignment_method (manual/automatic/round_robin/system)
        ├── assigned_to_name, previous_user_name
        ├── transfer_reason, transfer_notes
        ├── assigned_at timestamp
        ├── source_system
        └── backfill_confidence (high/medium/low)
```

### Frontend Display

```
AssignmentHistoryDialogComponent
    │
    ├── Triggered from contact detail views
    ├── Calls AssignmentHistoryService::getTimeline()
    │
    └── AssignmentTimelineComponent
        ├── Visual timeline with color-coded events
        ├── Icons per assignment_type:
        │   ├── initial → person_add
        │   ├── transfer → swap_horiz
        │   ├── reassignment → autorenew
        │   ├── round_robin → loop
        │   └── contact_merged → merge
        └── Shows agent names, reasons, timestamps
```

---

## Lifecycle Assignment Events

Beyond standard assignments, the system tracks lifecycle events:

| Event | Trigger | Assignment Type |
|-------|---------|----------------|
| Account merge | Two accounts merged | `contact_merged` |
| Contact discard | Duplicate removed | `contact_discarded` |
| Contact reactivation | Closed contact reopened | `contact_reactivated` |

---

## Workload Tracking

```
GET /assignmenthistory/workload/{agent_id}?from=...&to=...
    │
    ▼
Returns:
├── total_assignments (in date range)
├── active_conversations (currently open)
├── transfers_in (received from other agents)
├── transfers_out (sent to other agents)
└── initial_assignments (new leads assigned)
```

---

## Database Tables

| Table | Purpose |
|-------|---------|
| `tbl_contact_assignment_history` | Central audit trail of all assignment events |
| `tbl_unified_transfer_log` | Transfer-specific history with reasons |
| `tbl_open_conversations` | Current conversation-agent mapping |
| `tbl_telecommunication_agents` | Agent records (is_active flag) |
| `tbl_users` | User accounts linked to agents |
| `tbl_user_leaves` | Leave calendar for availability |
| `tbl_company_work_hours` | Working hours configuration |
| `tbl_settings` | Round-robin agent rotation config |

---

## Cross-References

**Core Modules**
- [`04-core-modules/assignment-management.md`](../04-core-modules/assignment-management.md) — AgentAssignmentHelper, round-robin logic, and transfer execution
- [`04-core-modules/conversations.md`](../04-core-modules/conversations.md) — Conversation creation and agent binding at conversation level
- [`04-core-modules/whatsapp-integration.md`](../04-core-modules/whatsapp-integration.md) — Entry point where assignment is triggered on inbound message

**Database Design**
- [`03-database-design/crm-tables.md`](../03-database-design/crm-tables.md) — `tbl_contact_assignment_history`, `tbl_unified_transfer_log`, `tbl_open_conversations` schema

**System Architecture**
- [`01-system-architecture/communication-patterns.md`](../01-system-architecture/communication-patterns.md) — Real-time transfer notifications via WebSocket and FCM

**Related Data Flows**
- [`06-data-flow/message-flow.md`](./message-flow.md) — Inbound message processing that triggers initial assignment
- [`06-data-flow/conversation-lifecycle.md`](./conversation-lifecycle.md) — Lifecycle stages affected by assignment and transfer events
