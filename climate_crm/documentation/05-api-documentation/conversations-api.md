# Conversations & Assignment API

> Module: `climate/api/conversations`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Conversation Endpoints](#conversation-endpoints)
2. [Conversation Transfer](#conversation-transfer)
3. [Assignment History Endpoints](#assignment-history-endpoints)
4. [Cross-References](#cross-references)

---

## Conversation Endpoints

### POST /openconversations/updateStage

**Capability**: `@capability user`

Updates the conversation stage. Closing as "unqualified" requires a `disposition_status`.

**Request**:
```json
{
  "conversation_id": 123,
  "stage": "contacted",
  "disposition_status": null
}
```

**Request (unqualified)**:
```json
{
  "conversation_id": 123,
  "stage": "unqualified",
  "disposition_status": "price_too_high"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Conversation stage updated successfully",
  "data": {
    "conversation_id": 123,
    "new_stage": "contacted",
    "disposition_status": null
  }
}
```

**Valid Stages**: `new`, `attempted`, `contacted`, `nurturing`, `qualified`, `unqualified`

**Valid Dispositions**: `rnr1`, `rnr2`, `rnr3`, `not_interested`, `price_too_high`, `wrong_timing`, `need_approval`, `competitor_chosen`, `budget_issues`, `decision_maker_unavailable`, `need_discount`, `credit_needed`, `need_more_time`, `customer_need_cod`, `non_contact`, `invalid`, `other`

---

### GET /openconversations/checkFollowupRequired

**Capability**: `@capability user`

Checks if a follow-up action is pending for the current user.

**Response** (200):
```json
{
  "success": true,
  "data": {
    "pending_count": 5,
    "overdue_count": 2
  }
}
```

---

## Conversation Transfer

### POST /conversationtransfer/transfer

**Capability**: `@capability conversations.transfer`

Transfer a conversation from one agent to another.

**Request**:
```json
{
  "conversation_id": 123,
  "to_user_id": 8,
  "transfer_reason": "Customer prefers Hindi",
  "transfer_notes": "Customer is more comfortable communicating in Hindi"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Conversation transferred successfully"
}
```

**Side Effects**:
- Updates `tbl_open_conversations.user_id` to target agent
- Creates record in `tbl_contact_assignment_history` (type: `transfer`)
- Pushes real-time notification via Redis queue
- Sends FCM notification to target agent

---

## Assignment History Endpoints

### GET /assignmenthistory/timeline/{contact_id}

**Capability**: `@capability contacts.view_assignment_history`

Returns paginated assignment timeline for a contact.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 20 | Records per page |
| `offset` | int | 0 | Offset for pagination |

**Response** (200):
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
      "assigned_at": "2025-12-15T10:30:00",
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
      "assigned_at": "2025-12-20T14:15:00",
      "source_system": "unified_transfer_log",
      "backfill_confidence": "high"
    }
  ],
  "total": 2,
  "page": 1
}
```

---

### GET /assignmenthistory/transfer_count/{contact_id}

**Capability**: `@capability contacts.view_assignment_history`

Returns the number of transfers for a contact.

---

### GET /assignmenthistory/workload/{agent_id}

**Capability**: `@capability contacts.view_assignment_history`

Returns agent workload metrics for a date range.

**Query Parameters**: `from` (date), `to` (date)

**Response** (200):
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

---

### GET /assignmenthistory/statistics

**Capability**: `@capability contacts.view_assignment_history`

Returns overall assignment statistics.

---

### GET /assignmenthistory/most_transferred

**Capability**: `@capability contacts.view_assignment_history`

Returns contacts with the highest number of transfers.

---

## Cross-References

| Document | Path |
|----------|------|
| Conversations Module | `04-core-modules/conversations.md` |
| Assignment Management | `04-core-modules/assignment-management.md` |
| CRM Tables (Schema) | `03-database-design/crm-tables.md` |
| Authentication | `05-api-documentation/authentication.md` |
