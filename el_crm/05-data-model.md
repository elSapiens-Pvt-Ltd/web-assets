# Data Model

> CRM-owned PostgreSQL tables, relationships, and external references.

---

## 1. Design Principles

- **CRM does NOT own contacts/accounts** — person and entity data lives in accounts-api (MongoDB). CRM stores `person_id`/`entity_id` as foreign references.
- **`workspace_id` on every table** — tenant isolation via PostgreSQL Row-Level Security.
- **UUID primary keys** — `gen_random_uuid()`, compatible with accounts-api UUIDs.
- **Soft deletes** — `deleted_at TIMESTAMP` where applicable (conversations, opportunities). Not all tables need soft delete.
- **Timestamps** — `created_at`, `updated_at` on all tables. Set by application, not DB triggers.
- **JSONB for flexible data** — custom field values, metadata, config payloads.
- **No business logic in triggers** — all logic in Go application code.
- **Ecosystem service references** — CRM stores IDs that reference data in other services: `person_id`/`entity_id` (accounts-api), `agent_id` (elauth), `product_id` (Goods & Services). Currency conversion via elCurrency Rates API, location enrichment via elGeolocations API — these are fetched at runtime, not stored redundantly.

---

## 2. Entity Relationship Diagram

```
accounts-api (external)          CRM PostgreSQL (owned)
═══════════════════════          ═══════════════════════

┌──────────────┐                 ┌──────────────────────┐
│ Person       │◄────person_id───│ contact_handles      │
│ (MongoDB)    │                 │ workspace_id         │
│              │◄────person_id───│ handle_type          │
│              │                 │ handle_value         │
└──────┬───────┘                 └──────────────────────┘
       │                                    │
       │ person_id                          │ person_id
       │                                    ▼
       │                         ┌──────────────────────┐        ┌─────────────────┐
       │                         │ conversations        │───────▶│ pipeline_stages  │
       │                         │ workspace_id         │stage_id│ workspace_id     │
       │                         │ person_id            │        │ pipeline_id      │
       │                         │ agent_id ─────────┐  │        └────────┬────────┘
       │                         │ source_id ──────┐ │  │                 │
       │                         └───────┬─────────│─│──┘                 │
       │                                 │         │ │           ┌────────▼────────┐
       │                                 │         │ │           │ pipelines       │
       │                                 ▼         │ │           │ workspace_id    │
       │                    ┌────────────────────┐ │ │           └─────────────────┘
       │                    │ conversation_msgs  │ │ │
       │                    │ workspace_id       │ │ │    ┌──────────────────┐
       │                    │ conversation_id    │ │ └───▶│ elauth Person    │
       │                    └────────────────────┘ │     │ (agent user)     │
       │                                           │     └──────────────────┘
       │                    ┌────────────────────┐ │
       │◄───person_id──────│ opportunities      │ │     ┌──────────────────┐
       │                    │ workspace_id       │─┴────▶│ contact_sources  │
       │                    │ pipeline_id        │       │ workspace_id     │
       │                    │ current_stage_id   │       └──────────────────┘
       │                    │ agent_id           │
       │                    └────────────────────┘
       │
       │                    ┌────────────────────┐      ┌──────────────────┐
       │                    │ activities         │      │ followups        │
       │                    │ workspace_id       │      │ workspace_id     │
       │                    │ entity_type/id     │      │ conversation_id  │
       │                    └────────────────────┘      │ agent_id         │
       │                                                └──────────────────┘
       │                    ┌────────────────────┐
       │                    │ assignment_history  │      ┌──────────────────────┐
       │                    │ workspace_id       │      │ custom_field_values   │
       │                    │ entity_type/id     │      │ workspace_id          │
       │                    └────────────────────┘      │ entity_type/id        │
       │                                                │ field_definition_id   │
       │                    ┌────────────────────┐      └──────────────────────┘
       │                    │ workflow_rules     │               │
       │                    │ workspace_id       │      ┌──────────────────────┐
       │                    └────────────────────┘      │ custom_field_defs    │
       │                                                │ workspace_id          │
       │                    ┌────────────────────┐      └──────────────────────┘
       │                    │ crm_workspace_config│
       │                    │ workspace_id       │
       │                    └────────────────────┘
```

---

## 3. Table Definitions

### crm_workspace_config

```sql
CREATE TABLE crm_workspace_config (
    workspace_id    UUID NOT NULL,
    config_key      VARCHAR(100) NOT NULL,
    config_value    JSONB NOT NULL DEFAULT '{}',
    updated_by      UUID,
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, config_key)
);
```

Keys: `workspace_profile`, `working_hours`, `sla_policies`, `conversation_settings`, `assignment_defaults`, `channel_defaults`, `followup_settings`, `disposition_reasons`, `loss_reasons`, `lifecycle_stages`, `call_dispositions`, `notification_defaults`, `quick_replies`, `import_settings`.

### contact_handles

```sql
CREATE TABLE contact_handles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL,
    person_id       UUID NOT NULL,          -- from accounts-api
    handle_type     VARCHAR(20) NOT NULL,   -- phone, email, whatsapp, instagram
    handle_value    VARCHAR(255) NOT NULL,
    is_primary      BOOLEAN NOT NULL DEFAULT false,
    channel         VARCHAR(50),            -- which channel this handle is used on
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, handle_type, handle_value)
);

CREATE INDEX idx_handles_ws_person ON contact_handles (workspace_id, person_id);
CREATE INDEX idx_handles_ws_value ON contact_handles (workspace_id, handle_value);
```

### conversations

```sql
CREATE TABLE conversations (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id                UUID NOT NULL,
    person_id                   UUID NOT NULL,          -- from accounts-api
    handle_value                VARCHAR(255),           -- primary handle for this conversation
    channel                     VARCHAR(50) NOT NULL,   -- whatsapp, voice, email, lead_capture
    status                      VARCHAR(20) NOT NULL DEFAULT 'open',  -- open, pending, closed
    stage_id                    UUID REFERENCES pipeline_stages(id),
    agent_id                    UUID,                   -- from elauth person_id
    priority                    VARCHAR(10) NOT NULL DEFAULT 'normal', -- normal, high, urgent
    source_id                   UUID REFERENCES contact_sources(id),
    first_response_at           TIMESTAMP WITH TIME ZONE,
    first_response_time_seconds INT,
    sla_status                  VARCHAR(20) DEFAULT 'ok', -- ok, warning, breached
    last_activity_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    last_idle_event_at          TIMESTAMP WITH TIME ZONE,
    closed_at                   TIMESTAMP WITH TIME ZONE,
    closed_reason               VARCHAR(50),            -- completed, unqualified, auto_closed
    disposition                 VARCHAR(100),           -- disposition reason key
    metadata                    JSONB DEFAULT '{}',
    created_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    deleted_at                  TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_conv_ws_agent_status ON conversations (workspace_id, agent_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_conv_ws_person ON conversations (workspace_id, person_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_conv_ws_stage ON conversations (workspace_id, stage_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_conv_ws_last_activity ON conversations (workspace_id, last_activity_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_conv_ws_sla ON conversations (workspace_id, sla_status) WHERE status = 'open';
```

### conversation_messages

```sql
CREATE TABLE conversation_messages (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id            UUID NOT NULL,
    conversation_id         UUID NOT NULL REFERENCES conversations(id),
    channel                 VARCHAR(50) NOT NULL,
    direction               VARCHAR(10) NOT NULL,    -- inbound, outbound
    sender_type             VARCHAR(20) NOT NULL,    -- customer, agent, system
    sender_id               UUID,                    -- agent person_id if outbound
    content_type            VARCHAR(30) NOT NULL,    -- text, image, video, document, audio, template, interactive_buttons, interactive_list, email, call_event, lead_capture, location, note
    content_text            TEXT,                    -- plain text body (searchable)
    content_json            JSONB,                  -- structured content (media URLs, template data, email HTML, etc.)
    external_message_id     VARCHAR(255),           -- channel-specific ID (wamid.xxx)
    delivery_status         VARCHAR(20) DEFAULT 'queued', -- queued, sending, sent, delivered, read, failed
    delivered_at            TIMESTAMP WITH TIME ZONE,
    read_at                 TIMESTAMP WITH TIME ZONE,
    failed_reason           TEXT,
    is_internal             BOOLEAN NOT NULL DEFAULT false, -- internal notes not sent to customer
    metadata                JSONB DEFAULT '{}',
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_msgs_ws_conv ON conversation_messages (workspace_id, conversation_id, created_at);
CREATE INDEX idx_msgs_ws_external ON conversation_messages (workspace_id, external_message_id) WHERE external_message_id IS NOT NULL;
CREATE INDEX idx_msgs_fulltext ON conversation_messages USING gin(to_tsvector('english', content_text)) WHERE content_text IS NOT NULL;
```

### pipelines

```sql
CREATE TABLE pipelines (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL,
    name            VARCHAR(100) NOT NULL,
    entity_type     VARCHAR(20) NOT NULL DEFAULT 'sales', -- sales, renewal, partnership
    is_default      BOOLEAN NOT NULL DEFAULT false,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, name)
);
```

### pipeline_stages

```sql
CREATE TABLE pipeline_stages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL,
    pipeline_id     UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    stage_order     INT NOT NULL,
    probability     INT DEFAULT 0,           -- 0-100
    color           VARCHAR(7) DEFAULT '#3b82f6',
    is_terminal     BOOLEAN NOT NULL DEFAULT false,
    outcomes        JSONB,                   -- ["won", "lost"] for terminal stages
    required_fields JSONB DEFAULT '[]',      -- fields required to enter this stage
    auto_actions    JSONB DEFAULT '[]',      -- workflow-like actions on stage entry
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, pipeline_id, stage_order)
);
```

### opportunities

```sql
CREATE TABLE opportunities (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        UUID NOT NULL,
    person_id           UUID NOT NULL,      -- from accounts-api
    entity_id           UUID,               -- company, from accounts-api
    pipeline_id         UUID NOT NULL REFERENCES pipelines(id),
    current_stage_id    UUID NOT NULL REFERENCES pipeline_stages(id),
    agent_id            UUID,               -- from elauth
    currency            VARCHAR(3) DEFAULT 'INR', -- ISO 4217, converted via elCurrency Rates API
    expected_value      DECIMAL(15,2),
    expected_value_base DECIMAL(15,2),           -- value in workspace base currency (auto-converted)
    won_value           DECIMAL(15,2),
    won_value_base      DECIMAL(15,2),           -- in workspace base currency
    expected_close_date DATE,
    closed_at           TIMESTAMP WITH TIME ZONE,
    outcome             VARCHAR(10),        -- won, lost (null if open)
    loss_reason         VARCHAR(100),
    competitor          VARCHAR(255),
    source_id           UUID REFERENCES contact_sources(id),
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    deleted_at          TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_opp_ws_pipeline_stage ON opportunities (workspace_id, pipeline_id, current_stage_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_opp_ws_agent ON opportunities (workspace_id, agent_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_opp_ws_person ON opportunities (workspace_id, person_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_opp_ws_close_date ON opportunities (workspace_id, expected_close_date) WHERE outcome IS NULL AND deleted_at IS NULL;
```

### activities

```sql
CREATE TABLE activities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL,
    entity_type     VARCHAR(30) NOT NULL,   -- conversation, opportunity, contact, account
    entity_id       UUID NOT NULL,
    activity_type   VARCHAR(30) NOT NULL,   -- call, note, email, meeting, stage_change, assignment, system
    content         JSONB NOT NULL,         -- type-specific payload
    created_by      UUID,                   -- person_id (null for system-generated)
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_activities_ws_entity ON activities (workspace_id, entity_type, entity_id, created_at DESC);
```

Activity content examples:
```json
// Call
{ "call_type": "outbound", "duration_seconds": 272, "recording_url": "https://...", "disposition": "interested" }

// Stage change
{ "old_stage": "Contacted", "new_stage": "Qualified", "old_stage_id": "uuid", "new_stage_id": "uuid" }

// Assignment
{ "assigned_from": "uuid", "assigned_to": "uuid", "method": "manual", "reason": "Agent overloaded" }

// Note
{ "text": "Customer wants bulk pricing for Grade A", "is_internal": true }
```

### followups

```sql
CREATE TABLE followups (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id            UUID NOT NULL,
    conversation_id         UUID NOT NULL REFERENCES conversations(id),
    agent_id                UUID NOT NULL,
    followup_type           VARCHAR(30) NOT NULL,   -- call_back, send_quote, send_sample, check_in, payment_followup, custom
    note                    TEXT,
    priority                VARCHAR(10) NOT NULL DEFAULT 'normal',
    scheduled_at            TIMESTAMP WITH TIME ZONE NOT NULL,
    original_scheduled_at   TIMESTAMP WITH TIME ZONE NOT NULL,
    status                  VARCHAR(20) NOT NULL DEFAULT 'upcoming', -- upcoming, due, overdue, completed, cancelled, snoozed
    completed_at            TIMESTAMP WITH TIME ZONE,
    snooze_count            INT NOT NULL DEFAULT 0,
    created_by              UUID NOT NULL,
    created_via             VARCHAR(20) NOT NULL DEFAULT 'manual', -- manual, workflow_rule, call_disposition, system
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_followups_ws_agent_status ON followups (workspace_id, agent_id, status, scheduled_at);
CREATE INDEX idx_followups_ws_due ON followups (workspace_id, scheduled_at) WHERE status IN ('upcoming', 'due');
```

### assignment_history

```sql
CREATE TABLE assignment_history (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        UUID NOT NULL,
    entity_type         VARCHAR(30) NOT NULL,   -- conversation, opportunity
    entity_id           UUID NOT NULL,
    assigned_from       UUID,
    assigned_to         UUID,
    assignment_type     VARCHAR(20) NOT NULL,   -- auto, manual, transfer, bulk, escalation
    assignment_method   VARCHAR(30),            -- round_robin, load_balanced, source_based, manual
    reason              VARCHAR(255),
    note                TEXT,
    created_by          UUID,                   -- person_id or null for system
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_assign_ws_entity ON assignment_history (workspace_id, entity_type, entity_id, created_at DESC);
```

### assignment_rules

```sql
CREATE TABLE assignment_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL,
    name            VARCHAR(255) NOT NULL,
    priority        INT NOT NULL,
    conditions      JSONB NOT NULL DEFAULT '{}',
    strategy        VARCHAR(30) NOT NULL,       -- specific_agent, round_robin, load_balanced, unassigned
    strategy_config JSONB NOT NULL DEFAULT '{}',
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, priority)
);
```

### contact_sources

```sql
CREATE TABLE contact_sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL,
    name            VARCHAR(100) NOT NULL,
    icon            VARCHAR(50),
    color           VARCHAR(7),
    is_active       BOOLEAN NOT NULL DEFAULT true,
    sort_order      INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, name)
);
```

### custom_field_definitions

```sql
CREATE TABLE custom_field_definitions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL,
    entity_type     VARCHAR(30) NOT NULL,   -- contact, account, opportunity, conversation
    field_label     VARCHAR(100) NOT NULL,
    field_key       VARCHAR(100) NOT NULL,  -- snake_case, unique per workspace+entity
    field_type      VARCHAR(20) NOT NULL,   -- text, textarea, number, currency, date, dropdown, multi_select, checkbox, url, email, phone
    options         JSONB,                  -- for dropdown/multi_select
    is_required     BOOLEAN NOT NULL DEFAULT false,
    default_value   TEXT,
    show_in         VARCHAR(10) NOT NULL DEFAULT 'both', -- list, detail, both
    is_searchable   BOOLEAN NOT NULL DEFAULT false,
    is_filterable   BOOLEAN NOT NULL DEFAULT false,
    sort_order      INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, entity_type, field_key)
);
```

### custom_field_values

```sql
CREATE TABLE custom_field_values (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        UUID NOT NULL,
    entity_type         VARCHAR(30) NOT NULL,
    entity_id           UUID NOT NULL,
    field_definition_id UUID NOT NULL REFERENCES custom_field_definitions(id),
    value_text          TEXT,
    value_number        DECIMAL(15,4),
    value_date          DATE,
    value_json          JSONB,              -- for multi_select and complex types
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, entity_type, entity_id, field_definition_id)
);

CREATE INDEX idx_cfv_ws_entity ON custom_field_values (workspace_id, entity_type, entity_id);
```

### workflow_rules & workflow_execution_logs

See [09-workflow-engine.md](09-workflow-engine.md) for full schema.

### message_templates

```sql
CREATE TABLE message_templates (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id            UUID NOT NULL,
    channel                 VARCHAR(50) NOT NULL,   -- whatsapp, email, quick_reply
    category                VARCHAR(50),            -- utility, marketing, sales, follow_up
    name                    VARCHAR(255) NOT NULL,
    body                    TEXT NOT NULL,
    variables               JSONB DEFAULT '[]',     -- [{position: 1, sample: "John"}]
    external_template_id    VARCHAR(255),           -- Meta template ID for WhatsApp
    status                  VARCHAR(20) DEFAULT 'active', -- active, pending, rejected (for WhatsApp)
    is_active               BOOLEAN NOT NULL DEFAULT true,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_templates_ws_channel ON message_templates (workspace_id, channel, is_active);
```

### workspace_channels

```sql
CREATE TABLE workspace_channels (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        UUID NOT NULL,
    channel_type        VARCHAR(50) NOT NULL,   -- whatsapp, voice, email, justdial, facebook, indiamart, webform
    config              JSONB NOT NULL,         -- encrypted credentials and settings
    status              VARCHAR(20) DEFAULT 'active', -- active, inactive, error
    last_health_check   TIMESTAMP WITH TIME ZONE,
    health_status       VARCHAR(20) DEFAULT 'unknown', -- healthy, degraded, down, unknown
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, channel_type)
);
```

### agent_settings

```sql
CREATE TABLE agent_settings (
    workspace_id                UUID NOT NULL,
    person_id                   UUID NOT NULL,      -- from elauth
    max_capacity                INT NOT NULL DEFAULT 50,
    is_available_for_assignment BOOLEAN NOT NULL DEFAULT true,
    status                      VARCHAR(20) NOT NULL DEFAULT 'active', -- active, inactive
    last_seen_at                TIMESTAMP WITH TIME ZONE,
    created_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, person_id)
);
```

### notifications & notification_preferences

```sql
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL,
    recipient_id    UUID NOT NULL,
    type            VARCHAR(50) NOT NULL,
    title           VARCHAR(255) NOT NULL,
    body            TEXT,
    priority        VARCHAR(10) NOT NULL DEFAULT 'normal',
    data            JSONB DEFAULT '{}',
    channels_sent   VARCHAR(20)[] DEFAULT '{}',
    is_read         BOOLEAN NOT NULL DEFAULT false,
    read_at         TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_notif_ws_recipient ON notifications (workspace_id, recipient_id, is_read, created_at DESC);

CREATE TABLE notification_preferences (
    workspace_id    UUID NOT NULL,
    person_id       UUID NOT NULL,
    preferences     JSONB NOT NULL DEFAULT '{}',
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, person_id)
);
```

### saved_filters

```sql
CREATE TABLE saved_filters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL,
    person_id       UUID NOT NULL,
    name            VARCHAR(100) NOT NULL,
    entity_type     VARCHAR(30) NOT NULL,   -- conversation, contact, opportunity
    filter_config   JSONB NOT NULL,
    is_shared       BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
```

### outbox (Transactional Outbox Pattern)

```sql
CREATE TABLE outbox (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type  VARCHAR(50) NOT NULL,   -- conversation, opportunity, etc.
    aggregate_id    UUID NOT NULL,
    event_type      VARCHAR(100) NOT NULL,  -- conversation.stage_changed
    payload         JSONB NOT NULL,
    published_at    TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_outbox_unpublished ON outbox (created_at) WHERE published_at IS NULL;
```

### config_audit_log

```sql
CREATE TABLE config_audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL,
    config_key      VARCHAR(100) NOT NULL,
    old_value       JSONB,
    new_value       JSONB,
    changed_by      UUID NOT NULL,
    changed_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_config_audit_ws ON config_audit_log (workspace_id, config_key, changed_at DESC);
```

---

## 4. Row-Level Security

```sql
-- Enable RLS on all CRM tables
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE followups ENABLE ROW LEVEL SECURITY;
-- ... (all tables with workspace_id)

-- Policy: rows only visible for current workspace
CREATE POLICY workspace_isolation ON conversations
    USING (workspace_id = current_setting('app.current_workspace_id')::uuid);

CREATE POLICY workspace_isolation ON conversation_messages
    USING (workspace_id = current_setting('app.current_workspace_id')::uuid);

-- Repeat for all tables...

-- CRM app sets this per request:
SET app.current_workspace_id = '<workspace_uuid_from_jwt>';
```

---

## 5. External References

| CRM Column | External Service | Resolution |
|-----------|-----------------|------------|
| `*.person_id` | accounts-api `Person._id` | gRPC `GetPerson(person_id, workspace_id)` |
| `*.entity_id` | accounts-api `Entity._id` | gRPC `GetEntity(entity_id, workspace_id)` |
| `*.agent_id` | elauth `person_id` | JWT contains agent person_id; gRPC `GetPerson()` for name/email |
| `*.workspace_id` | elauth `workspaces.id` | JWT contains workspace_id |
| `*.created_by` | elauth `person_id` | Same resolution as agent_id |

---

## 6. Table Count Summary

| Category | Tables | Count |
|----------|--------|-------|
| Core CRM | conversations, conversation_messages, contact_handles | 3 |
| Pipeline | pipelines, pipeline_stages, opportunities | 3 |
| Activities | activities, followups, assignment_history | 3 |
| Custom Fields | custom_field_definitions, custom_field_values | 2 |
| Configuration | crm_workspace_config, contact_sources, assignment_rules, workspace_channels, agent_settings, message_templates | 6 |
| Workflow | workflow_rules, workflow_execution_logs | 2 |
| Notifications | notifications, notification_preferences | 2 |
| Other | saved_filters, outbox, config_audit_log | 3 |
| **Total** | | **24** |
