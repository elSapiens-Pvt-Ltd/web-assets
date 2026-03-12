# Agent Daily Workflow

> Role: Sales Agent
> Frequency: Daily
> Primary screen: Inbox

---

## Flow Summary

The agent's day revolves around the **Inbox**. They log in, see their assigned conversations sorted by priority, respond to customers across channels, qualify leads, manage their pipeline, and complete follow-ups.

---

## Step-by-Step Flow

### 1. Login & Landing

```
Agent opens el-CRM URL
  → elsdk AuthGuard checks JWT in localStorage
  → If expired → redirect to elauth login page
  → If valid → check workspace context
    → If single workspace → load Inbox directly
    → If multiple workspaces → show OrgSwitcher (from elsdk)
  → Agent lands on INBOX (home screen)
```

**System state after login:**
- WebSocket connection established for real-time messages
- Unread conversation count loaded
- Active conversations list populated (assigned to this agent)

### 2. Inbox Overview (Home Screen)

```
┌─────────────────────────────────────────────────────────────────┐
│ ┌─────────────┐ ┌──────────────────────┐ ┌────────────────────┐ │
│ │ CONV LIST   │ │ CHAT THREAD          │ │ CONTACT DETAILS    │ │
│ │             │ │                      │ │                    │ │
│ │ [Filter ▾]  │ │ Messages...          │ │ Name, Phone, Email │ │
│ │ [Search]    │ │                      │ │ Account            │ │
│ │             │ │                      │ │ Stage: Qualified   │ │
│ │ ● Priya - 2m│ │                      │ │ Source: WhatsApp   │ │
│ │   Ravi - 15m│ │                      │ │ Agent: You         │ │
│ │   Ankit - 1h│ │                      │ │                    │ │
│ │   ...       │ │ ┌──────────────────┐ │ │ [Activities]       │ │
│ │             │ │ │ Type message...  │ │ │ [Follow-ups]       │ │
│ │             │ │ │ [📎] [📋] [Send]│ │ │ [Opportunities]    │ │
│ │             │ │ └──────────────────┘ │ │ [Notes]            │ │
│ └─────────────┘ └──────────────────────┘ └────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Panel 1 — Conversation List** (left, ~25% width):
- Filters: All | Mine | Unread | Unassigned | By Channel | By Stage
- Sort: Newest message | Oldest unanswered | Priority
- Each item shows: Contact name, last message preview, time, channel icon, unread badge
- Color indicators: Overdue SLA (red), approaching SLA (amber), normal (none)

**Panel 2 — Chat Thread** (center, ~45% width):
- Full message history for selected conversation
- Messages show: sender, timestamp, channel icon, delivery status (sent/delivered/read)
- Composer at bottom: text input, attach file, template picker, channel selector
- Channel indicator shows which channel is active for this conversation

**Panel 3 — Contact Details** (right, ~30% width):
- Contact info (from accounts-api): name, phone, email, account, designation
- CRM data: current stage, source, assigned agent, lifecycle stage
- Tabs: Activities | Follow-ups | Opportunities | Notes | History
- Quick actions: Create follow-up, Add note, Create opportunity, Transfer, Change stage

### 3. Handle Inbound Message

```
New WhatsApp message arrives
  → WebSocket pushes to agent's browser
  → Conversation moves to top of list with unread badge
  → If conversation exists → append message to thread
  → If new handle (unknown number) → system auto-creates:
      1. Contact handle record (CRM)
      2. Person record (accounts-api via gRPC)
      3. Conversation record (CRM, status: open, stage: New)
      4. Assignment based on workspace rules
  → Agent clicks conversation
  → Reads message in chat thread
  → Types reply → selects channel (defaults to same channel as inbound)
  → Clicks Send
  → Message sent via Communication Gateway
  → Delivery status updates in real-time (sent → delivered → read)
```

### 4. Qualify a Lead

```
Agent reviews conversation with new contact
  → Asks qualifying questions (via chat/call)
  → Opens Contact Details panel → clicks "Change Stage"
  → Stage options (workspace-configured):
      New → Contacted → Qualified → Opportunity → Won/Lost/Unqualified
  → Selects "Qualified"
  → If workspace has workflow rule: "On Qualified → Create Opportunity"
      → System auto-creates opportunity in default pipeline
  → Agent can also manually: Contact Details → Opportunities tab → "Create Opportunity"
  → Fills: Pipeline, Expected Value, Expected Close Date, Notes
  → Opportunity appears in Pipeline board
```

### 5. Manage Follow-Ups

```
Agent finishes a call, needs to follow up tomorrow
  → Contact Details → Follow-ups tab → "Create Follow-up"
  → Fills: Date/time, Note ("Send revised quote after internal pricing")
  → Saves
  → Next day: system sends notification (in-app + push if configured)
  → Agent sees follow-up reminder in Inbox (badge/filter: "Due follow-ups")
  → Clicks → opens the conversation
  → Completes the follow-up action
  → Marks follow-up as "Completed"
```

### 6. Log an Activity

```
After a phone call:
  → Contact Details → Activities tab → "Log Activity"
  → Type: Call (auto-populated if call came via Communication Gateway)
  → Duration: 5 min
  → Disposition: Interested / Call Back / Not Reachable / ...
  → Notes: "Customer wants bulk pricing for Grade A"
  → Save
  → Activity appears in timeline
  → If call via Comm Gateway → call recording link auto-attached
```

### 7. End of Day

```
Agent reviews their pipeline:
  → Navigates to Pipeline (sidebar)
  → Sees kanban board of their opportunities
  → Drags stalled opportunity to next stage (or marks lost)
  → Reviews overdue follow-ups → reschedules or completes
  → Checks unread conversations → responds or snoozes
  → Logs out (or just closes browser — JWT handles session)
```

---

## System Behaviors During Agent Workflow

| Trigger | System Action |
|---------|---------------|
| Agent sends first reply to a conversation | Calculate and store First Response Time (FRT) |
| Conversation stage changes | Log in activity timeline, publish event to bus |
| Follow-up becomes due | Send notification (in-app, push, email per preference) |
| SLA threshold breached | Mark conversation as SLA-breached, notify manager |
| Agent is idle on assigned conversation > X hours | Escalation per workflow rules |
| Inbound message on closed conversation | Reopen conversation, re-assign to original agent |

---

## Error States

| Scenario | Behavior |
|----------|----------|
| Message send fails (WhatsApp API error) | Show error in chat thread, retry button, log failure |
| Agent tries to reply on expired WhatsApp session (>24h) | Prompt to use template message instead |
| Contact handle already exists for another contact | Show merge suggestion dialog |
| WebSocket disconnects | Show "Reconnecting..." banner, auto-retry, queue messages |
