# Workflow Configuration

> Role: Admin
> Trigger: Admin wants to automate CRM actions based on events
> Primary screen: Settings → Automation → Workflow Rules

---

## Flow Summary

Workflow rules are "if this, then that" automations configured per workspace. They fire on CRM events (stage change, new conversation, idle timeout, etc.) and execute actions (create follow-up, notify agent, change stage, send template, etc.).

---

## Workflow Rule Structure

```
TRIGGER (when this happens)
  + CONDITIONS (only if these are true)
  → ACTIONS (do these things)
```

---

## Configuration UI

```
Settings → Automation → Workflow Rules

┌─────────────────────────────────────────────────────────────────┐
│ Workflow Rules                                      [+ Rule]    │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Active  "Auto-create opportunity on Qualified"                │
│   Trigger: Conversation stage changed to "Qualified"            │
│   Action: Create opportunity in "Sales Pipeline"                │
│                                                    [Edit] [Off] │
│ ─────────────────────────────────────────────────────────────── │
│ ✓ Active  "Notify manager on high-value deal"                  │
│   Trigger: Opportunity value > ₹1,00,000                       │
│   Action: Send notification to manager                          │
│                                                    [Edit] [Off] │
│ ─────────────────────────────────────────────────────────────── │
│ ✓ Active  "Follow-up on idle conversations"                    │
│   Trigger: Conversation idle > 3 days                           │
│   Action: Create follow-up for assigned agent                   │
│                                                    [Edit] [Off] │
│ ─────────────────────────────────────────────────────────────── │
│ ○ Inactive "Welcome message for JustDial leads"                │
│   Trigger: New conversation, source = JustDial                  │
│   Action: Send WhatsApp template "welcome_justdial"             │
│                                                    [Edit] [On]  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Creating a Workflow Rule

```
Admin clicks [+ Rule]

Step 1: Name & Description
  → Name: "Auto-create opportunity on Qualified"
  → Description: "When a conversation reaches Qualified stage, auto-create an opportunity"

Step 2: Trigger
  Select trigger event:
  ┌─────────────────────────────────────────┐
  │ Conversation Events                      │
  │   ○ Conversation created                 │
  │   ● Conversation stage changed           │
  │   ○ Conversation assigned                │
  │   ○ Conversation closed                  │
  │   ○ Conversation idle (no activity for)  │
  │   ○ Conversation reopened                │
  │                                          │
  │ Message Events                           │
  │   ○ Message received (inbound)           │
  │   ○ Message sent (outbound)              │
  │   ○ Message delivery failed              │
  │                                          │
  │ Opportunity Events                       │
  │   ○ Opportunity created                  │
  │   ○ Opportunity stage changed            │
  │   ○ Opportunity closed (won/lost)        │
  │   ○ Opportunity value changed            │
  │                                          │
  │ Follow-Up Events                         │
  │   ○ Follow-up due                        │
  │   ○ Follow-up overdue                    │
  │                                          │
  │ Time-Based                               │
  │   ○ Scheduled (cron: daily/weekly)       │
  │   ○ Date field approaching (X days before)│
  └─────────────────────────────────────────┘

  Selected: "Conversation stage changed"

Step 3: Conditions (optional, narrows when rule fires)
  ┌─────────────────────────────────────────┐
  │ ALL of these conditions must be true:    │
  │                                          │
  │ [New stage ▾] [equals ▾] [Qualified ▾]  │
  │ [+ Add condition]                        │
  │                                          │
  │ Available condition fields:              │
  │ - New stage / Previous stage             │
  │ - Channel                                │
  │ - Source                                 │
  │ - Agent                                  │
  │ - Contact custom field values            │
  │ - Conversation age                       │
  │ - Opportunity value                      │
  │                                          │
  │ Operators: equals, not equals,           │
  │ contains, greater than, less than,       │
  │ is empty, is not empty                   │
  └─────────────────────────────────────────┘

  Condition: "New stage equals Qualified"

Step 4: Actions (one or more)
  ┌─────────────────────────────────────────┐
  │ Actions to perform:                      │
  │                                          │
  │ 1. [Create opportunity ▾]                │
  │    Pipeline: [Sales Pipeline ▾]          │
  │    Stage: [New Opportunity ▾]            │
  │    Value: [Copy from conversation ▾]     │
  │                                          │
  │ [+ Add action]                           │
  │                                          │
  │ Available actions:                       │
  │ - Create opportunity                     │
  │ - Change conversation stage              │
  │ - Assign to agent/team                   │
  │ - Create follow-up                       │
  │ - Send notification (in-app)             │
  │ - Send email notification                │
  │ - Send WhatsApp template                 │
  │ - Add note to conversation               │
  │ - Update custom field                    │
  │ - Close conversation                     │
  │ - Webhook (call external URL)            │
  └─────────────────────────────────────────┘

Step 5: Review & Activate
  → Summary of trigger + conditions + actions
  → Toggle: Active / Inactive
  → Save
```

---

## Common Workflow Rule Examples

### 1. Auto-Create Opportunity
```
Trigger: Conversation stage changed
Condition: New stage = "Qualified"
Action: Create opportunity in "Sales Pipeline" at stage "New"
```

### 2. SLA Escalation
```
Trigger: Conversation idle > 30 minutes (during business hours)
Condition: Conversation has no first response yet
Action: Send notification to manager "SLA breach: {contact_name} waiting {idle_time}"
```

### 3. Welcome Message for Leads
```
Trigger: Conversation created
Condition: Source = "JustDial" AND Channel = "WhatsApp"
Action: Send WhatsApp template "welcome_justdial" with variables from contact
```

### 4. High-Value Deal Alert
```
Trigger: Opportunity value changed
Condition: New value > ₹1,00,000
Action: Send notification to all managers "High-value deal: {contact_name} - ₹{value}"
```

### 5. Auto-Close Stale Conversations
```
Trigger: Conversation idle > 30 days
Condition: Stage NOT IN ("Opportunity", "Negotiation")
Action: Change stage to "Unqualified", Set disposition: "No Response", Close conversation
```

### 6. Follow-Up After Proposal
```
Trigger: Opportunity stage changed
Condition: New stage = "Proposal Sent"
Action: Create follow-up for assigned agent, due in 3 days, note: "Follow up on proposal"
```

### 7. Reassign on Agent Deactivation
```
Trigger: Agent deactivated (from elauth event)
Condition: Agent has open conversations
Action: Reassign all to manager
```

---

## Execution Model

```
Event occurs in CRM
  → Event published to internal workflow engine
  → Engine loads active rules for this workspace
  → Filters rules by trigger type
  → Evaluates conditions for each matching rule (in priority order)
  → First matching rule: execute actions sequentially
  → Log execution: rule_id, trigger_data, conditions_evaluated, actions_executed, outcome
  → If action fails: log error, continue to next action (don't block)
```

### Execution Constraints
- **No infinite loops**: If an action triggers another rule (e.g., stage change action triggers stage change rule), the engine tracks execution depth. Max depth: 3.
- **Rate limiting**: Max 100 rule executions per conversation per hour.
- **Async execution**: Actions execute asynchronously. WebSocket template sends, notifications are queued.
- **Idempotency**: Actions check for duplicates (e.g., don't create opportunity if one already exists for this conversation).

---

## Rule Storage

```
workflow_rules:
  id: UUID
  workspace_id: UUID
  name: VARCHAR
  description: TEXT
  trigger_type: VARCHAR (conversation.stage_changed, message.received, etc.)
  conditions: JSONB
  actions: JSONB (array of action definitions)
  priority: INT
  is_active: BOOLEAN
  execution_count: INT
  last_executed_at: TIMESTAMP
  created_by: UUID
  created_at, updated_at: TIMESTAMPS

workflow_execution_logs:
  id: UUID
  workspace_id: UUID
  rule_id: UUID
  trigger_event: JSONB
  conditions_result: BOOLEAN
  actions_executed: JSONB (array with success/failure per action)
  execution_time_ms: INT
  created_at: TIMESTAMP
```
