# Assignment & Agent Management Module

> Module: `climate/modules/assignment`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [Data Model](#data-model)
3. [Assignment Types](#assignment-types)
4. [Transfer Flow](#transfer-flow)
5. [Assignment History Timeline](#assignment-history-timeline)
6. [Agent Workload](#agent-workload)
7. [Backfill System](#backfill-system)
8. [Backend Controller](#backend-controller)
9. [Frontend Components](#frontend-components)
10. [Cross-References](#cross-references)

---

## Overview

The Assignment module tracks the complete history of how contacts and conversations are assigned to agents. It provides a full audit trail of initial assignments, transfers, reassignments, merges, and lifecycle events.

---

## Data Model

### tbl_contact_assignment_history

This is the central table storing every assignment event:

```
Assignment Record
├── WHO: contact_id, account_id, conversation_id
├── FROM: previous_user_id
├── TO: assigned_to_user_id
├── BY: assigned_by_user_id
├── TYPE: assignment_type (initial, transfer, reassignment, ...)
├── METHOD: assignment_method (manual, automatic, round_robin, system)
├── WHY: transfer_reason, transfer_notes, lifecycle_reason
├── WHEN: assigned_at
├── SOURCE: source_system, source_record_id
└── CONFIDENCE: is_backfilled, backfill_confidence
```

---

## Assignment Types

### Initial Assignment

The first time a contact/conversation is assigned to an agent:

```
New lead arrives (WhatsApp, JustDial, etc.)
    │
    ├── Auto-assignment (round_robin or rules)
    │   assignment_type = 'initial'
    │   assignment_method = 'automatic' or 'round_robin'
    │
    └── Manual assignment (by manager)
        assignment_type = 'initial'
        assignment_method = 'manual'
```

### Transfer

Manual transfer of a conversation from one agent to another:

```
Agent A ──[transfer]──► Agent B

Record:
├── assignment_type = 'transfer'
├── assignment_method = 'manual'
├── previous_user_id = Agent A
├── assigned_to_user_id = Agent B
├── transfer_reason = "Customer speaks Hindi"
└── transfer_notes = "Customer prefers to communicate in Hindi"
```

### Reassignment

System-initiated change of assignment (e.g., agent goes on leave):

```
System detects Agent A is unavailable
    │
    └── Reassign to Agent B
        assignment_type = 'reassignment'
        assignment_method = 'system'
```

### Round Robin

Automatic distribution across available agents:

```
New conversation → agent_assignment_helper.php
    │
    ├── Get available agents (active, not on leave)
    ├── Calculate current workload per agent
    ├── Select agent with lowest active conversations
    └── Assign
        assignment_type = 'round_robin'
        assignment_method = 'round_robin'
```

### Lifecycle Events

| Type | Trigger | Description |
|------|---------|-------------|
| `contact_merged` | Account merge | Contact merged into another account |
| `contact_discarded` | Deduplication | Duplicate contact removed |
| `contact_reactivated` | Account reactivation | Previously closed contact reactivated |

### Assignment Methods

| Method | Description |
|--------|-------------|
| `manual` | Agent or manager manually assigns |
| `automatic` | System auto-assigns based on rules |
| `round_robin` | Distributed evenly across available agents |
| `system` | System-triggered (merge, migration, etc.) |

---

## Transfer Flow

### Agent-to-Agent Transfer

```
┌─────────────┐
│  Agent A     │
│  has convo   │
└──────┬───────┘
       │
       ▼
┌─────────────────┐
│ Initiate Transfer│
│ ├── Select Agent B
│ ├── Provide reason
│ └── Add notes
└──────┬───────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Backend: ConversationTransfer    │
│                                  │
│ 1. Validate Agent B exists/active│
│ 2. Update conversation.user_id   │
│    to Agent B                    │
│ 3. Insert assignment_history:    │
│    ├── type = 'transfer'         │
│    ├── previous = Agent A        │
│    ├── assigned_to = Agent B     │
│    └── reason + notes            │
│ 4. Push real-time notification   │
│ 5. FCM push to Agent B          │
└──────┬───────────────────────────┘
       │
       ▼
┌─────────────┐
│  Agent B     │
│  sees convo  │
│  in queue    │
└──────────────┘
```

---

## Assignment History Timeline

### API Endpoint

`GET /assignmenthistory/timeline/{contact_id}?limit=20&offset=0`

The controller implementation:

```php
class AssignmentHistory extends CI_Controller
{
    public function __construct()
    {
        parent::__construct();
        $this->load->database();
        $this->load->model('ContactAssignmentHistoryModel');
    }

    /**
     * @capability contacts.view_assignment_history
     */
    public function timeline($contact_id = null)
    {
        if (!$contact_id) {
            echo Risposta::json_encode([
                'success' => false,
                'message' => 'Contact ID is required'
            ]);
            return;
        }

        $limit = $this->input->get('limit') ?? 20;
        $offset = $this->input->get('offset') ?? 0;

        $result = $this->ContactAssignmentHistoryModel->getContactTimelinePaginated(
            $contact_id, $limit, $offset
        );

        echo Risposta::json_encode([
            'success' => true,
            'data' => $result
        ]);
    }
}
```

Returns a paginated timeline of all assignment events:

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "assignment_type": "initial",
      "assignment_method": "automatic",
      "assigned_to_user_id": 5,
      "assigned_to_name": "Priya Sharma",
      "previous_user_id": null,
      "transfer_reason": null,
      "assigned_at": "2025-12-15 10:30:00",
      "source_system": "open_conversations",
      "backfill_confidence": "high"
    },
    {
      "id": 2,
      "assignment_type": "transfer",
      "assignment_method": "manual",
      "assigned_to_user_id": 8,
      "assigned_to_name": "Rahul Kumar",
      "previous_user_id": 5,
      "previous_user_name": "Priya Sharma",
      "transfer_reason": "Customer prefers Hindi",
      "transfer_notes": "Transfer for language preference",
      "assigned_at": "2025-12-20 14:15:00",
      "source_system": "unified_transfer_log",
      "backfill_confidence": "high"
    }
  ],
  "total": 2,
  "page": 1
}
```

---

## Agent Workload

### Workload Endpoint

`GET /assignmenthistory/workload/{agent_id}?from=2026-01-01&to=2026-03-11`

```json
{
  "success": true,
  "data": {
    "agent_id": 5,
    "agent_name": "Priya Sharma",
    "total_assignments": 45,
    "active_conversations": 12,
    "transfers_in": 8,
    "transfers_out": 3,
    "initial_assignments": 34
  }
}
```

### Statistics

`GET /assignmenthistory/statistics` — Overall assignment statistics for dashboards.

### Most Transferred

`GET /assignmenthistory/most_transferred` — Identifies contacts that have been transferred the most, useful for identifying assignment issues.

---

## Backfill System

### Purpose

The assignment history includes **backfilled data** from legacy systems that didn't have a centralized assignment tracking table.

### Data Sources

| Source System | Origin | Confidence |
|--------------|--------|------------|
| `legacy_whatsapp` | Old `tbl_whatsapp_contacts.agent_id` | Medium (agent_id = last agent, not initial) |
| `legacy_transfer_log` | Old `tbl_transfer_chat_log` | High (explicit transfer records) |
| `open_conversations` | New conversation system | High (native tracking) |
| `unified_transfer_log` | Unified transfer records | High (native tracking) |
| `migration_contact_merge` | Contact merge events | High |
| `migration_contact_discard` | Contact discard events | High |
| `manual_backfill` | Manual data corrections | High |

### Confidence Levels

| Level | Meaning |
|-------|---------|
| `high` | Data verified from explicit records |
| `medium` | Reasonable inference (e.g., WA agent_id for never-transferred contacts) |
| `low` | Duplicate or uncertain data |

### Key Insight

In the old WhatsApp system, `tbl_whatsapp_contacts.agent_id` stores the **last agent** (updated in-place on each transfer), not the initial agent. The backfill migration corrects this by:

1. Looking at `tbl_transfer_chat_log` for the first transfer's `from_agent_id`
2. If a transfer exists → the `from_agent_id` of the first transfer is the real initial agent
3. If no transfer exists → the current `agent_id` IS the initial agent (never transferred)

---

## Backend Controller

### AssignmentHistory Controller

| Method | HTTP | Capability | Description |
|--------|------|------------|-------------|
| `timeline($contact_id)` | GET | `contacts.view_assignment_history` | Paginated timeline |
| `transfer_count($contact_id)` | GET | `contacts.view_assignment_history` | Transfer count |
| `workload($agent_id)` | GET | `contacts.view_assignment_history` | Agent workload |
| `statistics()` | GET | `contacts.view_assignment_history` | Overall stats |
| `most_transferred()` | GET | `contacts.view_assignment_history` | Most transferred contacts |

### ContactAssignmentHistoryModel

Database operations for the assignment history table:
- `getContactTimelinePaginated($contact_id, $limit, $offset)`: Paginated timeline with user names
- `getTransferCount($contact_id)`: Count of transfer-type assignments
- `getWorkload($agent_id, $from, $to)`: Workload metrics for date range
- `getStatistics()`: Aggregate statistics
- `getMostTransferred($limit)`: Contacts sorted by transfer count

---

## Frontend Components

### Assignment History Dialog (`assignment-history-dialog/`)

Modal dialog triggered from contact detail views. Shows full timeline with visual indicators.

### Assignment Timeline (`assignment-timeline/`)

Visual timeline component, color-coded by assignment type. Shows agent names, reasons, and dates.

---

## Agent Assignment Helper

### `agent_assignment_helper.php`

Provides logic for automatic agent assignment:

- **Available Agents**: Filters by active status, not on leave, within working hours
- **Workload Balancing**: Counts active conversations per agent
- **Selection**: Agent with lowest current workload gets the assignment
- **Holiday/Leave Check**: Integrates with `tbl_company_holidays` and `tbl_user_leaves`

---

## Cross-References

| Document | Path |
|----------|------|
| CRM Tables (Assignment History schema) | `03-database-design/crm-tables.md` |
| Configuration Tables (Users, Roles) | `03-database-design/configuration-tables.md` |
| Assignment Flow | `06-data-flow/assignment-flow.md` |
| Contacts & Accounts | `04-core-modules/contacts-accounts.md` |
| Conversations | `04-core-modules/conversations.md` |
