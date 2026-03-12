# Follow-Up Workflow

> Role: Sales Agent
> Trigger: Agent creates a follow-up reminder or system auto-creates one
> Primary screen: Inbox, Follow-ups panel

---

## Flow Summary

Follow-ups are scheduled reminders tied to a conversation. They ensure no lead falls through the cracks. Agents create them manually or the system creates them based on workflow rules.

---

## Creating a Follow-Up

### Manual Creation (from Inbox)

```
Agent is in a conversation with Rahul Verma
  → Contact Details panel → Follow-ups tab → "+ New Follow-up"
  → Form:
      Date: [date picker] (default: tomorrow)
      Time: [time picker] (default: 10:00 AM workspace time)
      Type: Call Back | Send Quote | Send Sample | Check In | Custom
      Note: "Send revised pricing after checking with procurement team"
      Priority: Normal | High | Urgent
  → Save
  → Follow-up appears in:
      - Contact Details → Follow-ups tab (with countdown)
      - Agent's Follow-up list (sidebar or dedicated view)
      - Inbox filter: "Due Follow-ups"
```

### Auto-Created by System

```
Scenarios where system creates follow-ups:
  1. Missed inbound call → follow-up: "Call back" in 30 min
  2. Call disposition = "Call Back Later" → follow-up with agent-set date
  3. Workflow rule: "If conversation idle > 3 days → create follow-up for agent"
  4. Stage change to "Proposal" → follow-up: "Check proposal response" in 3 days
```

---

## Follow-Up Lifecycle

```
Created → Upcoming → Due → Overdue → Completed / Cancelled
  │                   │       │
  │                   │       └→ Escalated (if overdue > threshold)
  │                   │
  │                   └→ Snoozed (reschedule to later)
  │
  └→ Cancelled (agent decides not to follow up)
```

---

## Due Follow-Up — Agent Experience

### Notification

```
Follow-up becomes due at 10:00 AM
  → In-app notification: "Follow-up due: Call back Rahul Verma"
  → Push notification (if enabled): same message
  → Inbox: conversation shows follow-up badge/indicator
  → Follow-ups view: item highlighted as "Due Now"
```

### Acting on Follow-Up

```
Agent clicks notification or finds in Follow-ups view
  → Opens the linked conversation
  → Performs the action (calls, sends message, etc.)
  → Marks follow-up as "Completed"
  → Optional: create a new follow-up for the next step
```

### Snooze

```
Agent can't act right now
  → Follow-up → "Snooze" → select new date/time
  → Follow-up moves back to "Upcoming"
  → Original due date logged for accountability tracking
```

---

## Follow-Ups View (Dedicated Page or Panel)

```
┌─────────────────────────────────────────────────────────────┐
│ Follow-Ups     [Today] [This Week] [Overdue] [All]         │
├─────────────────────────────────────────────────────────────┤
│ OVERDUE (3)                                                  │
│ ┌─ ⚠ Rahul Verma — Call Back — Due: Mar 10 (2 days ago)   │
│ ┌─ ⚠ Ankit Shah — Send Quote — Due: Mar 11 (1 day ago)    │
│ ┌─ ⚠ Priya M — Check In — Due: Mar 11 (1 day ago)        │
│                                                              │
│ TODAY (5)                                                    │
│ ┌─ ● Suresh K — Send Sample Details — Due: 10:00 AM       │
│ ┌─ ● Meera J — Follow up on proposal — Due: 2:00 PM       │
│ ┌─ ○ Tech Corp — Discuss pricing — Due: 4:00 PM           │
│ ...                                                          │
│                                                              │
│ UPCOMING                                                     │
│ ┌─ ○ Mar 13 — BuildRight — Payment follow-up               │
│ ┌─ ○ Mar 15 — FreshMart — Contract renewal check           │
└─────────────────────────────────────────────────────────────┘

● = Due now    ○ = Upcoming    ⚠ = Overdue
Click any item → opens the linked conversation
```

### Manager View

Managers see follow-ups for their entire team:
- Filter by agent
- See overdue counts per agent
- Can reassign follow-ups if agent is unavailable

---

## SLA & Escalation

Workspace-configurable overdue thresholds:

| Threshold | Action |
|-----------|--------|
| Due + 1 hour | Badge turns red in agent's view |
| Due + 4 hours | In-app reminder notification to agent |
| Due + 24 hours | Notify manager (in-app + email) |
| Due + 48 hours | Auto-escalate: reassign to manager or senior agent |

---

## Data Model

```
followups:
  id: UUID
  workspace_id: UUID
  conversation_id: UUID
  agent_id: UUID (assigned agent — from elauth person_id)
  followup_type: enum (call_back, send_quote, send_sample, check_in, custom)
  note: text
  priority: enum (normal, high, urgent)
  scheduled_at: timestamp with timezone
  original_scheduled_at: timestamp (preserved if snoozed)
  status: enum (upcoming, due, overdue, completed, cancelled, snoozed)
  completed_at: timestamp (nullable)
  created_by: UUID (agent or system)
  created_via: enum (manual, workflow_rule, call_disposition, system)
  created_at, updated_at: timestamps
```

---

## Integration Points

| System | Interaction |
|--------|-------------|
| Notification Hub | Send due/overdue notifications (in-app, push, email) |
| Workflow Engine | Auto-create follow-ups based on rules |
| Reports | Follow-up completion rate, overdue rate per agent |
| Calendar (future) | Sync follow-ups to Google Calendar / Outlook |
