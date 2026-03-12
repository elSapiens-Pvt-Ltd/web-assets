# Assignment Override

> Role: Manager, Admin
> Trigger: Manager needs to reassign conversations or contacts between agents
> Primary screen: Inbox, Contacts, Pipeline

---

## Flow Summary

Managers can override automatic assignment by manually reassigning conversations, contacts, or opportunities to different agents. This is used when agents are overloaded, on leave, or when a deal needs a specialist.

---

## Single Conversation Reassignment

### From Inbox

```
Manager opens Inbox → selects a conversation
  → Chat Thread header shows: Agent: Priya
  → Clicks "Priya" (or [⋮] → Transfer)
  → Transfer dialog:

  ┌────────────────────────────────────────┐
  │ Transfer Conversation                  │
  │                                        │
  │ From: Priya Sharma                     │
  │ To: [Search agent ▾]                   │
  │     Ravi Kumar (12 open conversations) │
  │     Ankit Patel (8 open conversations) │
  │     Meera Joshi (15 open conversations)│
  │                                        │
  │ Reason: [Select ▾]                     │
  │   ○ Agent overloaded                   │
  │   ○ Agent on leave                     │
  │   ○ Specialist needed                  │
  │   ○ Customer request                   │
  │   ○ Other                              │
  │                                        │
  │ Internal note (optional):              │
  │ [Customer prefers Hindi speaker]       │
  │                                        │
  │ □ Notify new agent                     │
  │ □ Notify previous agent                │
  │                                        │
  │ [Cancel]              [Transfer]       │
  └────────────────────────────────────────┘

  → On transfer:
      1. Update conversation.agent_id
      2. Log assignment_history record
      3. Add system message in conversation: "Transferred from Priya to Ravi"
      4. If internal note provided → add as internal note in conversation
      5. Notify new agent (WebSocket + push)
      6. Notify previous agent (if checkbox checked)
```

---

## Bulk Reassignment

### From Inbox (Multiple Conversations)

```
Manager enters selection mode (checkbox appears on each conversation)
  → Selects multiple conversations (or "Select All matching filter")
  → Bulk action bar appears:

  ┌──────────────────────────────────────────────────┐
  │ 12 conversations selected                         │
  │ [Assign To ▾] [Change Stage ▾] [Close] [Cancel]  │
  └──────────────────────────────────────────────────┘

  → Clicks [Assign To]
  → Same agent selection + reason dialog
  → Confirms: "Reassign 12 conversations to Ravi Kumar?"
  → Bulk operation executes
  → Progress indicator: "12/12 reassigned"
  → All 12 conversations update in real-time
```

### Agent Handoff (All Conversations)

```
Manager → Settings → Team → Agent "Priya" → [⋮] → "Reassign All"
  → Shows: "Priya has 15 open conversations and 8 active opportunities"
  → Options:
      ○ Reassign all to specific agent: [Select ▾]
      ○ Distribute via assignment rules (round-robin/load-balanced)
      ○ Move to unassigned queue
  → Reason: Agent on leave / Agent departing / Workload balancing
  → Confirm
  → Bulk reassignment executes
  → All affected agents notified
```

---

## Opportunity Reassignment

```
Manager opens Pipeline board
  → Right-clicks opportunity card → "Transfer"
  → Or: Opportunity detail → [Transfer]
  → Same dialog: select agent, reason, note
  → Opportunity.agent_id updated
  → Related conversation(s) optionally transferred too:
      □ Also transfer active conversations for this contact (checked by default)
```

---

## Assignment History

Every assignment change is logged and visible:

```
Contact Detail → Activities tab:
  Mar 12, 10:30 — Conversation transferred from Priya to Ravi
    Reason: Agent overloaded
    By: Manager Meera
    Note: "Customer prefers Hindi speaker"

  Mar 10, 09:00 — Auto-assigned to Priya
    Method: Round-robin
    Rule: Default assignment rule

  Mar 10, 09:00 — Conversation created
    Source: JustDial
    Handle: +91 98765 43210
```

Manager can view full assignment history:
- Per conversation: in activity timeline
- Per agent: Settings → Team → Agent → "Assignment History"
- Workspace-wide: Reports → Agent Activity (includes transfers)

---

## Data Model Impact

```
assignment_history:
  id: UUID
  workspace_id: UUID
  entity_type: 'conversation' | 'opportunity' | 'contact'
  entity_id: UUID
  assigned_from: UUID (person_id, nullable if first assignment)
  assigned_to: UUID (person_id, nullable if moved to unassigned)
  assignment_type: 'auto' | 'manual' | 'transfer' | 'bulk' | 'escalation'
  assignment_method: 'round_robin' | 'load_balanced' | 'source_based' | 'manual' | 'escalation_rule'
  reason: VARCHAR (nullable)
  note: TEXT (nullable)
  created_by: UUID (person_id of who triggered it, or 'system')
  created_at: TIMESTAMP
```

---

## Permissions

| Action | Agent | Manager | Admin |
|--------|-------|---------|-------|
| Transfer own conversation | Yes | Yes | Yes |
| Transfer any conversation | No | Yes | Yes |
| Bulk reassign | No | Yes | Yes |
| Reassign all from agent | No | Yes | Yes |
| View assignment history (own) | Yes | Yes | Yes |
| View assignment history (all) | No | Yes | Yes |
