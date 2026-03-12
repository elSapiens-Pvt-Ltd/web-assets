# Configuration Specification

> All workspace-level configurable settings. Every setting described with: key, type, default, and behavior.
> Configuration eliminates hardcoded business logic — each workspace adapts the CRM to their needs.

---

## 1. Storage Model

Configuration is stored in two patterns:

**Pattern A — Dedicated Tables**: For structured, frequently queried config (pipelines, stages, custom fields, assignment rules, workflow rules, contact sources). Each has its own table with proper indexing.

**Pattern B — Key-Value JSONB**: For general workspace settings. Stored in `crm_workspace_config`:

```sql
crm_workspace_config:
  workspace_id  UUID    -- FK, part of composite PK
  config_key    VARCHAR -- e.g., "working_hours", "sla_policies"
  config_value  JSONB   -- the configuration payload
  updated_by    UUID    -- person_id who last modified
  updated_at    TIMESTAMP
  PRIMARY KEY (workspace_id, config_key)
```

---

## 2. General Settings

### Workspace Profile
```
Key: workspace_profile
Default: populated from elauth workspace data
```
```json
{
  "display_name": "Climate Naturals",
  "industry": "manufacturing",
  "country": "IN",
  "timezone": "Asia/Kolkata",
  "currency": "INR",
  "currency_symbol": "₹",
  "currency_locale": "en-IN",
  "logo_url": "https://cdn.../logo.png",
  "date_format": "DD/MM/YYYY",
  "time_format": "12h"
}
```

### Business Hours
```
Key: working_hours
```
```json
{
  "days": {
    "monday":    { "enabled": true,  "start": "09:00", "end": "18:00" },
    "tuesday":   { "enabled": true,  "start": "09:00", "end": "18:00" },
    "wednesday": { "enabled": true,  "start": "09:00", "end": "18:00" },
    "thursday":  { "enabled": true,  "start": "09:00", "end": "18:00" },
    "friday":    { "enabled": true,  "start": "09:00", "end": "18:00" },
    "saturday":  { "enabled": true,  "start": "09:00", "end": "14:00" },
    "sunday":    { "enabled": false, "start": null,    "end": null    }
  },
  "timezone": "Asia/Kolkata",
  "holidays": [
    { "date": "2026-01-26", "name": "Republic Day" },
    { "date": "2026-08-15", "name": "Independence Day" }
  ]
}
```

**Used by**: SLA calculations (pause outside hours), Assignment rules (after-hours routing), Auto-reply messages, Report date filtering.

---

## 3. Pipeline Configuration

### Stored in: `pipelines` + `pipeline_stages` tables

### Pipeline Defaults
```
Key: pipeline_defaults
```
```json
{
  "default_pipeline_id": "uuid-of-sales-pipeline",
  "auto_create_opportunity_on_stage": "qualified",
  "allow_multiple_opportunities_per_contact": true,
  "require_close_reason": true,
  "show_weighted_values": true
}
```

### Pipeline Stage Schema

Each stage row in `pipeline_stages`:
```json
{
  "id": "uuid",
  "pipeline_id": "uuid",
  "name": "Qualified",
  "stage_order": 3,
  "probability": 40,
  "color": "#22c55e",
  "is_terminal": false,
  "outcomes": null,
  "required_fields": ["contact_name", "company_name", "phone"],
  "auto_actions": [
    { "type": "create_opportunity", "pipeline": "default" }
  ]
}
```

Terminal stage example:
```json
{
  "name": "Closed",
  "is_terminal": true,
  "outcomes": ["won", "lost"],
  "required_fields": {
    "won": ["won_value", "close_date"],
    "lost": ["loss_reason"]
  }
}
```

### Loss Reasons
```
Key: loss_reasons
```
```json
[
  { "key": "price_too_high", "label": "Price Too High", "active": true },
  { "key": "competitor_won", "label": "Competitor Won", "active": true },
  { "key": "customer_silent", "label": "Customer Went Silent", "active": true },
  { "key": "budget_cut", "label": "Budget Cut", "active": true },
  { "key": "timeline_mismatch", "label": "Timeline Mismatch", "active": true }
]
```

### Disposition Reasons (Unqualified)
```
Key: disposition_reasons
```
```json
[
  { "key": "not_interested", "label": "Not Interested", "active": true },
  { "key": "budget_too_low", "label": "Budget Too Low", "active": true },
  { "key": "wrong_category", "label": "Wrong Product Category", "active": true },
  { "key": "competitor", "label": "Competitor Chosen", "active": true },
  { "key": "duplicate", "label": "Duplicate", "active": true },
  { "key": "spam", "label": "Spam / Irrelevant", "active": true },
  { "key": "not_serviceable", "label": "Location Not Serviceable", "active": true },
  { "key": "not_decision_maker", "label": "Not Decision Maker", "active": true },
  { "key": "no_response", "label": "No Response", "active": true },
  { "key": "already_customer", "label": "Already a Customer", "active": true },
  { "key": "wrong_number", "label": "Wrong Number", "active": true },
  { "key": "language_barrier", "label": "Language Barrier", "active": true },
  { "key": "other", "label": "Other", "active": true }
]
```

---

## 4. Contact & Conversation Settings

### Lifecycle Stages
```
Key: lifecycle_stages
```
```json
[
  { "key": "lead", "label": "Lead", "color": "#3b82f6", "is_default": true },
  { "key": "customer", "label": "Customer", "color": "#22c55e" },
  { "key": "inactive", "label": "Inactive", "color": "#9ca3af" }
]
```

### Conversation Settings
```
Key: conversation_settings
```
```json
{
  "reopen_on_new_message": true,
  "reopen_creates_new_conversation": false,
  "auto_close_after_days": 30,
  "auto_close_exclude_stages": ["opportunity", "negotiation"],
  "max_conversations_per_contact": null,
  "default_priority": "normal"
}
```

### Call Dispositions
```
Key: call_dispositions
```
```json
[
  { "key": "interested", "label": "Interested", "create_followup": false },
  { "key": "call_back", "label": "Call Back Later", "create_followup": true, "followup_offset_hours": 24 },
  { "key": "not_reachable", "label": "Not Reachable", "create_followup": true, "followup_offset_hours": 4 },
  { "key": "wrong_number", "label": "Wrong Number", "create_followup": false },
  { "key": "not_interested", "label": "Not Interested", "create_followup": false },
  { "key": "voicemail", "label": "Left Voicemail", "create_followup": true, "followup_offset_hours": 48 }
]
```

---

## 5. Assignment Configuration

### Stored in: `assignment_rules` table + config key

### Assignment Defaults
```
Key: assignment_defaults
```
```json
{
  "default_strategy": "round_robin",
  "respect_business_hours": true,
  "skip_offline_agents": true,
  "skip_at_capacity_agents": true,
  "default_max_capacity": 50,
  "offline_threshold_minutes": 30,
  "unassigned_escalation_minutes": 15
}
```

### Assignment Rule Schema (in `assignment_rules` table)

```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "name": "JustDial leads to Ravi",
  "priority": 1,
  "conditions": {
    "operator": "AND",
    "rules": [
      { "field": "source.name", "operator": "equals", "value": "JustDial" }
    ]
  },
  "strategy": "specific_agent",
  "strategy_config": {
    "agent_id": "uuid-of-ravi"
  },
  "is_active": true
}
```

Strategy types:
| Strategy | Config | Behavior |
|----------|--------|----------|
| `specific_agent` | `{ "agent_id": "uuid" }` | Always assign to this agent |
| `round_robin` | `{ "team": "all" or ["uuid1","uuid2"] }` | Sequential rotation |
| `load_balanced` | `{ "team": "all" or ["uuid1","uuid2"] }` | Least open conversations |
| `unassigned` | `{}` | Don't assign, put in queue |

---

## 6. SLA Configuration

```
Key: sla_policies
```
```json
{
  "first_response": {
    "enabled": true,
    "target_seconds": 300,
    "warning_seconds": 180,
    "breach_actions": [
      { "type": "notify", "recipients": ["manager"], "channels": ["in_app"] },
      { "type": "escalate", "strategy": "reassign_to_next_available" }
    ],
    "business_hours_only": true
  },
  "follow_up_response": {
    "enabled": true,
    "target_seconds": 1800,
    "warning_seconds": 1200,
    "breach_actions": [
      { "type": "notify", "recipients": ["manager"], "channels": ["in_app", "email"] }
    ],
    "business_hours_only": true
  },
  "conversation_resolution": {
    "enabled": false,
    "target_hours": 48,
    "warning_hours": 36,
    "breach_actions": [],
    "business_hours_only": true
  }
}
```

---

## 7. Channel Configuration

### Stored in: `workspace_channels` table (credentials encrypted)

### Channel Defaults
```
Key: channel_defaults
```
```json
{
  "default_outbound_channel": "whatsapp",
  "channel_priority": ["whatsapp", "email", "sms", "voice"],
  "fallback_enabled": true,
  "auto_reply_outside_hours": {
    "enabled": true,
    "channels": ["whatsapp"],
    "message": "Thank you for contacting us. We'll respond during business hours (Mon-Sat, 9AM-6PM)."
  }
}
```

### WhatsApp-Specific
```
Key: channel_whatsapp
```
```json
{
  "session_expiry_warning_minutes": 30,
  "template_categories_visible": ["utility", "marketing"],
  "auto_assign_on_first_message": true,
  "media_auto_download": true,
  "max_media_size_mb": 16
}
```

---

## 8. Notification Configuration

### Workspace-Level Defaults
```
Key: notification_defaults
```
```json
{
  "channels": {
    "in_app": true,
    "push": true,
    "email": false
  },
  "digest": {
    "daily_summary_enabled": true,
    "daily_summary_time": "09:00",
    "weekly_summary_enabled": true,
    "weekly_summary_day": "monday"
  }
}
```

User-level preferences in `notification_preferences` table override workspace defaults.

---

## 9. Follow-Up Configuration

```
Key: followup_settings
```
```json
{
  "default_time": "10:00",
  "overdue_escalation_hours": 24,
  "overdue_escalation_target": "manager",
  "max_snooze_count": 3,
  "auto_create_on_missed_call": true,
  "auto_create_missed_call_offset_minutes": 30,
  "followup_types": [
    { "key": "call_back", "label": "Call Back" },
    { "key": "send_quote", "label": "Send Quote" },
    { "key": "send_sample", "label": "Send Sample" },
    { "key": "check_in", "label": "Check In" },
    { "key": "payment_followup", "label": "Payment Follow-up" },
    { "key": "custom", "label": "Custom" }
  ]
}
```

---

## 10. Template Configuration

### Quick Replies (Canned Responses)
```
Key: quick_replies
```
```json
[
  {
    "id": "uuid",
    "shortcut": "/greeting",
    "title": "Standard Greeting",
    "body": "Hello {{contact_name}}! Thank you for contacting us. How can I help you today?",
    "category": "general",
    "available_to": "all"
  },
  {
    "id": "uuid",
    "shortcut": "/pricing",
    "title": "Pricing Request",
    "body": "I'd be happy to share our pricing. Could you let me know:\n1. Which products you're interested in?\n2. Expected monthly volume?\n3. Delivery location?",
    "category": "sales",
    "available_to": "all"
  }
]
```

Agent types `/greeting` in composer → auto-expands to full text with variables replaced.

WhatsApp templates are synced from Meta via Communication Gateway and stored in `message_templates` table — not configurable in CRM (managed in Meta Business Manager).

---

## 11. Custom Fields Configuration

### Stored in: `custom_field_definitions` table

```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "entity_type": "contact",
  "field_label": "Business Type",
  "field_key": "business_type",
  "field_type": "dropdown",
  "options": [
    { "value": "manufacturer", "label": "Manufacturer" },
    { "value": "trader", "label": "Trader" },
    { "value": "retailer", "label": "Retailer" },
    { "value": "distributor", "label": "Distributor" }
  ],
  "is_required": false,
  "default_value": null,
  "show_in": "both",
  "is_searchable": true,
  "is_filterable": true,
  "sort_order": 1
}
```

### Supported Field Types

| Type | Storage Column | Input Component |
|------|---------------|-----------------|
| text | value_text | Text input |
| textarea | value_text | Multi-line textarea |
| number | value_number | Number input |
| currency | value_number | Currency input (with workspace currency symbol) |
| date | value_date | Date picker |
| dropdown | value_text | Select dropdown |
| multi_select | value_json | Multi-select chips |
| checkbox | value_text ("true"/"false") | Toggle/checkbox |
| url | value_text | URL input with validation |
| email | value_text | Email input with validation |
| phone | value_text | Phone input with formatting |

### Entities Supporting Custom Fields
- Contact (person-level, stored in CRM linked by person_id)
- Account (entity-level, stored in CRM linked by entity_id)
- Opportunity (stored directly on opportunities table)
- Conversation (stored in custom_field_values linked by conversation_id)

---

## 12. Import/Export Configuration

```
Key: import_settings
```
```json
{
  "csv_max_rows": 10000,
  "duplicate_handling": "skip",
  "default_field_mapping": {
    "Name": "contact_name",
    "Phone": "phone_handle",
    "Email": "email_handle",
    "Company": "account_name"
  },
  "required_import_fields": ["contact_name"],
  "auto_create_accounts": true,
  "auto_assign_imported_contacts": false
}
```

---

## 13. Configuration Change Audit

All configuration changes are logged:

```sql
config_audit_log:
  id          UUID
  workspace_id UUID
  config_key  VARCHAR    -- which config was changed
  old_value   JSONB      -- previous value
  new_value   JSONB      -- new value
  changed_by  UUID       -- person_id
  changed_at  TIMESTAMP
```

This enables: "Who changed the assignment rules and when?" — visible in Settings → Audit Log (admin only).
