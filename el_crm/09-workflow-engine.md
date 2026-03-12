# Workflow Engine Specification

> Automation rules engine: triggers, conditions, actions, execution model.
> Internal to CRM service. Event-driven, evaluated on domain events.

---

## 1. Architecture

```
Domain Event (internal or from NATS)
  │
  ▼
Workflow Engine (Go goroutine pool)
  │
  ├─ Load active rules for workspace (cached, invalidated on rule change)
  ├─ Filter by trigger type
  ├─ Evaluate conditions (in priority order)
  ├─ First match → execute actions sequentially
  ├─ Log execution
  └─ Handle errors (log, continue, don't block)
```

The workflow engine runs inside the CRM service process — not a separate service. It subscribes to internal domain events (same process) and NATS events.

---

## 2. Trigger Types

### Conversation Triggers

| Trigger | Event Key | Fires When | Available Context |
|---------|-----------|------------|-------------------|
| Conversation Created | `conversation.created` | New conversation record created | conversation, person, channel, source, handle |
| Conversation Stage Changed | `conversation.stage_changed` | Stage transitions | conversation, person, old_stage, new_stage, agent |
| Conversation Assigned | `conversation.assigned` | Agent assignment (auto or manual) | conversation, person, assigned_to, assigned_from, method |
| Conversation Closed | `conversation.closed` | Conversation status → closed | conversation, person, reason, disposition, agent |
| Conversation Reopened | `conversation.reopened` | Closed conversation receives new message | conversation, person, channel |
| Conversation Idle | `conversation.idle` | No activity for X duration (checked by cron) | conversation, person, agent, idle_duration |

### Message Triggers

| Trigger | Event Key | Fires When | Available Context |
|---------|-----------|------------|-------------------|
| Message Received | `message.received` | Inbound message stored | message, conversation, person, channel, content_type |
| Message Sent | `message.sent` | Outbound message sent by agent | message, conversation, person, channel, agent |
| Message Delivery Failed | `message.delivery_failed` | Channel reports failure | message, conversation, channel, error_reason |

### Opportunity Triggers

| Trigger | Event Key | Fires When | Available Context |
|---------|-----------|------------|-------------------|
| Opportunity Created | `opportunity.created` | New opportunity record | opportunity, person, pipeline, stage, agent, value |
| Opportunity Stage Changed | `opportunity.stage_changed` | Pipeline stage transitions | opportunity, person, old_stage, new_stage, agent, value |
| Opportunity Closed | `opportunity.closed` | Won or lost | opportunity, person, outcome, value, reason, agent |
| Opportunity Value Changed | `opportunity.value_changed` | Expected value updated | opportunity, person, old_value, new_value, agent |

### Follow-Up Triggers

| Trigger | Event Key | Fires When | Available Context |
|---------|-----------|------------|-------------------|
| Follow-Up Due | `followup.due` | Scheduled time reached (cron checks) | followup, conversation, person, agent |
| Follow-Up Overdue | `followup.overdue` | Due + threshold exceeded (cron) | followup, conversation, person, agent, overdue_duration |

### Time-Based Triggers

| Trigger | Event Key | Fires When | Available Context |
|---------|-----------|------------|-------------------|
| Scheduled | `schedule.cron` | Cron expression matches | workspace, current_time |
| Date Field Approaching | `schedule.date_approaching` | Entity date field within X days | entity, field_name, field_value, days_until |

---

## 3. Condition System

### Condition Structure

```json
{
  "operator": "AND",
  "rules": [
    {
      "field": "new_stage.name",
      "operator": "equals",
      "value": "Qualified"
    },
    {
      "field": "source.name",
      "operator": "in",
      "value": ["JustDial", "Facebook"]
    }
  ],
  "groups": [
    {
      "operator": "OR",
      "rules": [
        { "field": "channel", "operator": "equals", "value": "whatsapp" },
        { "field": "channel", "operator": "equals", "value": "email" }
      ]
    }
  ]
}
```

Top-level `operator` (AND/OR) combines `rules` and nested `groups`.

### Operators

| Operator | Description | Applicable Types |
|----------|-------------|-----------------|
| `equals` | Exact match | text, number, date, enum |
| `not_equals` | Not equal | text, number, date, enum |
| `contains` | Substring match | text |
| `not_contains` | No substring match | text |
| `starts_with` | Prefix match | text |
| `greater_than` | > value | number, date |
| `less_than` | < value | number, date |
| `greater_or_equal` | >= value | number, date |
| `less_or_equal` | <= value | number, date |
| `in` | Value in list | text, number, enum |
| `not_in` | Value not in list | text, number, enum |
| `is_empty` | Field is null/empty | any |
| `is_not_empty` | Field has value | any |
| `between` | Value in range [min, max] | number, date |

### Available Fields Per Trigger Type

**conversation.stage_changed:**
- `new_stage.name`, `new_stage.id`, `old_stage.name`, `old_stage.id`
- `conversation.channel`, `conversation.source.name`, `conversation.priority`
- `conversation.agent_id`, `conversation.age_days`
- `person.custom_field.*` (any custom field by key)

**message.received:**
- `message.channel`, `message.content_type`, `message.content.body`
- `conversation.stage.name`, `conversation.agent_id`

**opportunity.stage_changed:**
- `new_stage.name`, `old_stage.name`
- `opportunity.value`, `opportunity.pipeline.name`
- `opportunity.agent_id`

**conversation.idle:**
- `idle_duration_hours`, `idle_duration_days`
- `conversation.stage.name`, `conversation.has_first_response`
- `conversation.agent_id`

---

## 4. Action Types

### create_opportunity

```json
{
  "type": "create_opportunity",
  "config": {
    "pipeline": "default",
    "stage": "first",
    "copy_value_from": "conversation.custom_field.expected_value",
    "copy_close_date_from": null
  }
}
```
Creates opportunity linked to the conversation's person. Skips if opportunity already exists for this person + pipeline.

### change_stage

```json
{
  "type": "change_stage",
  "config": {
    "entity": "conversation",
    "new_stage": "Qualified"
  }
}
```

### assign

```json
{
  "type": "assign",
  "config": {
    "entity": "conversation",
    "target_type": "specific_agent",
    "target_id": "uuid-of-agent",
    "reason": "Workflow rule: Source-based routing"
  }
}
```
target_type: `specific_agent`, `team` (with strategy), `manager`, `next_available`.

### create_followup

```json
{
  "type": "create_followup",
  "config": {
    "offset_hours": 72,
    "offset_from": "now",
    "type": "check_in",
    "note_template": "Follow up on {{conversation.stage.name}} with {{person.name}}",
    "priority": "normal",
    "assign_to": "current_agent"
  }
}
```

### send_notification

```json
{
  "type": "send_notification",
  "config": {
    "recipients": ["manager"],
    "channels": ["in_app", "email"],
    "title_template": "SLA Breach: {{person.name}}",
    "body_template": "Conversation with {{person.name}} has been waiting {{idle_duration_minutes}} minutes without response.",
    "priority": "high"
  }
}
```
recipients: `current_agent`, `manager`, `all_managers`, `specific_user:uuid`, `all_agents`.

### send_template_message

```json
{
  "type": "send_template_message",
  "config": {
    "channel": "whatsapp",
    "template_id": "uuid-of-template",
    "variables": {
      "1": "{{person.name}}",
      "2": "{{conversation.source.name}}"
    }
  }
}
```

### add_note

```json
{
  "type": "add_note",
  "config": {
    "entity": "conversation",
    "content_template": "Auto-note: Stage changed from {{old_stage.name}} to {{new_stage.name}}",
    "is_internal": true
  }
}
```

### update_field

```json
{
  "type": "update_field",
  "config": {
    "entity": "conversation",
    "field": "priority",
    "value": "high"
  }
}
```
Works for built-in fields and custom fields.

### close_conversation

```json
{
  "type": "close_conversation",
  "config": {
    "reason": "auto_closed",
    "disposition": "no_response",
    "change_stage": "Unqualified"
  }
}
```

### webhook

```json
{
  "type": "webhook",
  "config": {
    "url": "https://api.client.com/crm-hook",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer {{workspace.webhook_secret}}",
      "Content-Type": "application/json"
    },
    "body_template": {
      "event": "conversation_qualified",
      "contact_name": "{{person.name}}",
      "phone": "{{person.phone}}",
      "stage": "{{new_stage.name}}"
    },
    "timeout_ms": 5000,
    "retry_count": 3
  }
}
```

---

## 5. Execution Engine

### Processing Flow

```go
func (e *WorkflowEngine) ProcessEvent(ctx context.Context, event DomainEvent) {
    workspace_id := event.WorkspaceID

    // 1. Load active rules (cached per workspace, invalidated on rule change)
    rules := e.ruleCache.GetActive(workspace_id, event.Type)

    // 2. Sort by priority
    sort.Slice(rules, func(i, j int) bool { return rules[i].Priority < rules[j].Priority })

    // 3. Check execution depth (loop prevention)
    depth := ctx.Value(executionDepthKey).(int)
    if depth >= 3 {
        log.Warn("max execution depth reached", "workspace", workspace_id)
        return
    }

    // 4. Evaluate each rule
    for _, rule := range rules {
        if e.evaluateConditions(ctx, rule.Conditions, event) {
            // 5. Execute actions
            e.executeActions(ctx, rule, event, depth+1)

            // 6. Log execution
            e.logExecution(ctx, rule, event, true)

            // First match wins (configurable: first-match or all-matches)
            if rule.StopOnMatch {
                break
            }
        }
    }
}
```

### Loop Prevention

| Mechanism | Detail |
|-----------|--------|
| Execution depth | Max 3 levels of cascading rules. If rule A triggers rule B which triggers rule C → C can execute. If C would trigger D → blocked. |
| Rate limiting | Max 100 rule executions per entity per hour. Prevents runaway rules. |
| Same-event dedup | If an action would trigger the same event that triggered the rule on the same entity → skip. |

### Async Execution

Actions that involve external calls (send_template_message, webhook, send_notification) are queued:

```
Rule matched → actions list
  │
  ├─ Synchronous actions (fast, local):
  │    change_stage, update_field, add_note, close_conversation
  │    → Execute immediately in same goroutine
  │
  └─ Async actions (external, potentially slow):
       create_followup, send_notification, send_template_message, webhook
       → Queue to action worker pool (buffered channel)
       → Worker executes with timeout
       → Result logged
```

### Error Handling

```
Action execution:
  Success → log success, continue to next action
  Failure → log error with details, continue to next action (don't block)
  Timeout → log timeout, mark as failed, continue

Rule execution:
  Condition evaluation error → log, skip rule (don't execute actions)
  All actions failed → log, mark execution as "all_failed"
```

---

## 6. Rule Storage

### workflow_rules Table

```sql
CREATE TABLE workflow_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    trigger_type    VARCHAR(100) NOT NULL,  -- 'conversation.stage_changed'
    conditions      JSONB NOT NULL DEFAULT '{}',
    actions         JSONB NOT NULL DEFAULT '[]',
    priority        INT NOT NULL DEFAULT 100,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    stop_on_match   BOOLEAN NOT NULL DEFAULT true,
    execution_count BIGINT NOT NULL DEFAULT 0,
    last_executed_at TIMESTAMP WITH TIME ZONE,
    created_by      UUID NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_workflow_rules_ws_trigger
    ON workflow_rules (workspace_id, trigger_type, is_active, priority);
```

### Full Rule Example

```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "name": "Auto-create opportunity on Qualified",
  "description": "When a conversation reaches Qualified stage, create an opportunity in the default pipeline",
  "trigger_type": "conversation.stage_changed",
  "conditions": {
    "operator": "AND",
    "rules": [
      { "field": "new_stage.name", "operator": "equals", "value": "Qualified" }
    ]
  },
  "actions": [
    {
      "type": "create_opportunity",
      "config": { "pipeline": "default", "stage": "first" }
    },
    {
      "type": "send_notification",
      "config": {
        "recipients": ["current_agent"],
        "channels": ["in_app"],
        "title_template": "Opportunity created for {{person.name}}",
        "body_template": "A new opportunity has been auto-created in the Sales Pipeline."
      }
    }
  ],
  "priority": 10,
  "is_active": true,
  "stop_on_match": true
}
```

---

## 7. Execution Logging

### workflow_execution_logs Table

```sql
CREATE TABLE workflow_execution_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL,
    rule_id         UUID NOT NULL REFERENCES workflow_rules(id),
    trigger_event   JSONB NOT NULL,     -- snapshot of the triggering event
    conditions_result BOOLEAN NOT NULL, -- did conditions match?
    actions_executed JSONB,             -- per-action results
    execution_time_ms INT,
    error           TEXT,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_wf_exec_logs_ws_rule
    ON workflow_execution_logs (workspace_id, rule_id, created_at DESC);
```

### Execution Log Entry Example

```json
{
  "id": "uuid",
  "rule_id": "uuid",
  "trigger_event": {
    "type": "conversation.stage_changed",
    "conversation_id": "uuid",
    "person_id": "uuid",
    "old_stage": "Contacted",
    "new_stage": "Qualified"
  },
  "conditions_result": true,
  "actions_executed": [
    {
      "type": "create_opportunity",
      "status": "success",
      "result": { "opportunity_id": "uuid" },
      "duration_ms": 45
    },
    {
      "type": "send_notification",
      "status": "success",
      "result": { "notification_id": "uuid" },
      "duration_ms": 12
    }
  ],
  "execution_time_ms": 62,
  "error": null
}
```

### Log Viewing UI

Settings → Workflows → Rule → "Execution Log" tab:
- Last 100 executions
- Filter: success/failure, date range
- Each entry expandable to see full trigger event and action results
- Useful for debugging: "Why didn't this rule fire?" → check conditions_result = false entries

---

## 8. Template Variables

Actions use `{{variable}}` syntax for dynamic content. Variables resolved from event context:

| Variable | Source | Example Value |
|----------|--------|---------------|
| `{{person.name}}` | accounts-api person | "Rahul Verma" |
| `{{person.phone}}` | accounts-api person | "+919876543210" |
| `{{person.email}}` | accounts-api person | "rahul@acme.com" |
| `{{conversation.id}}` | CRM conversation | "uuid" |
| `{{conversation.channel}}` | CRM conversation | "whatsapp" |
| `{{conversation.stage.name}}` | CRM pipeline stage | "Qualified" |
| `{{conversation.source.name}}` | CRM contact source | "JustDial" |
| `{{conversation.agent.name}}` | elauth person | "Priya Sharma" |
| `{{old_stage.name}}` | Trigger context | "Contacted" |
| `{{new_stage.name}}` | Trigger context | "Qualified" |
| `{{opportunity.value}}` | CRM opportunity | "50000" |
| `{{opportunity.pipeline.name}}` | CRM pipeline | "Sales Pipeline" |
| `{{idle_duration_minutes}}` | Calculated | "45" |
| `{{idle_duration_hours}}` | Calculated | "2.5" |
| `{{workspace.name}}` | elauth workspace | "Climate Naturals" |

---

## 9. Dry-Run Mode

For testing rules before activation:

```
Settings → Workflows → Rule → [Test / Dry Run]
  → Select a recent event to simulate against
  → Engine evaluates conditions → shows result (match/no-match)
  → If match → shows actions that WOULD execute (without actually running)
  → Admin can verify rule behavior before enabling

API: POST /settings/workflows/:id/dry-run
Body: { "event_id": "uuid" } or { "event_snapshot": { ... } }
Response: {
  "conditions_matched": true,
  "actions_would_execute": [
    { "type": "create_opportunity", "config": {...}, "preview": "Would create opportunity in Sales Pipeline" }
  ]
}
```

---

## 10. Idle Conversation Detection

The `conversation.idle` trigger requires a background cron job since there's no explicit event:

```
Every 5 minutes (cron job in CRM service):
  1. Query conversations WHERE status = 'open'
     AND last_activity_at < now() - interval (configured threshold)
     AND workspace_id IN (workspaces with idle rules configured)
  2. For each idle conversation:
     Emit internal event: conversation.idle { idle_duration }
  3. Workflow engine processes as normal

  Dedup: track last idle check timestamp per conversation to avoid
  re-triggering the same rule repeatedly. Use a `last_idle_event_at`
  column or Redis key.
```
