# Workspace Setup

> Role: Admin
> Trigger: New workspace provisioned or admin configures CRM settings
> Primary screen: Settings

---

## Flow Summary

When a new client workspace is created (via elauth), the admin configures the CRM to match their sales process. This includes pipeline stages, custom fields, business hours, SLA rules, contact sources, disposition reasons, assignment rules, and templates.

---

## First-Time Workspace Configuration Wizard

```
Admin logs into new workspace for the first time
  → CRM detects: no pipeline configured
  → Shows setup wizard (skippable, can configure later in Settings)

Step 1: Company Profile
  → Company name (pre-filled from elauth workspace)
  → Industry (dropdown: Manufacturing, Trading, Services, Retail, ...)
  → Country / Timezone
  → Currency (INR, USD, EUR, ...)
  → Logo upload

Step 2: Pipeline Setup
  → Option A: Use industry template
      Manufacturing: Lead → Qualified → Sample Sent → Negotiation → Order → Closed
      Services: Inquiry → Discovery → Proposal → Contract → Active
      Trading: Contact → Interested → Quote → PO Received → Shipped
  → Option B: Custom pipeline
      Add stages, set order, mark terminal stages, set probabilities
  → Can add multiple pipelines later

Step 3: Team Setup
  → Shows users already in workspace (from elauth)
  → Assign CRM roles: Agent, Manager, Admin
  → Set agent capacity (max open conversations)
  → Configure assignment rules (default: round-robin)

Step 4: Channels
  → Connect WhatsApp Business API (API key, phone number ID, WABA ID)
  → Configure voice provider (Smartflo credentials)
  → Set up email (SES/SMTP config, from address)
  → Each channel: test connection → green checkmark

Step 5: Business Hours
  → Set working days (Mon-Fri default)
  → Set working hours per day (9:00 AM - 6:00 PM default)
  → Timezone selection
  → Holiday list (optional, import from calendar)

  → "Complete Setup" → workspace ready to use
```

---

## Settings Navigation (Post-Setup)

```
Settings (sidebar)
├── General
│   ├── Workspace Profile
│   └── Business Hours & Holidays
├── Pipeline
│   ├── Pipelines & Stages
│   ├── Stage Requirements
│   └── Win/Loss Reasons
├── Contacts
│   ├── Custom Fields
│   ├── Contact Sources
│   ├── Lifecycle Stages
│   └── Disposition Reasons
├── Assignment
│   ├── Assignment Rules
│   ├── Agent Capacity
│   └── Escalation Rules
├── Channels
│   ├── WhatsApp
│   ├── Voice
│   ├── Email
│   └── Lead Capture (JustDial, Facebook, etc.)
├── Automation
│   ├── Workflow Rules
│   └── SLA Policies
├── Templates
│   ├── WhatsApp Templates
│   ├── Email Templates
│   └── Quick Replies
└── Import / Export
    ├── Import Contacts (CSV)
    └── Export Data
```

---

## Key Configuration Flows

### Configure Pipeline Stages

```
Settings → Pipeline → Pipelines & Stages
  → Select pipeline: "Sales Pipeline"
  → Current stages shown as reorderable list:

  ┌─────────────────────────────────────────────────────────────┐
  │ Sales Pipeline                                    [+ Stage] │
  ├─────────────────────────────────────────────────────────────┤
  │ ≡ 1. New           Probability: 10%   Color: Blue    [⚙]  │
  │ ≡ 2. Contacted     Probability: 20%   Color: Cyan    [⚙]  │
  │ ≡ 3. Qualified     Probability: 40%   Color: Green   [⚙]  │
  │ ≡ 4. Proposal      Probability: 60%   Color: Yellow  [⚙]  │
  │ ≡ 5. Negotiation   Probability: 80%   Color: Orange  [⚙]  │
  │ ≡ 6. Closed        Terminal ✓  Outcomes: Won/Lost   [⚙]  │
  └─────────────────────────────────────────────────────────────┘

  ≡ = drag handle for reorder
  [⚙] = edit stage settings:
    - Name, color, probability
    - Required fields to enter this stage
    - Auto-actions on entry (workflow rules)
    - Is terminal? (conversation closes when reaching this stage)

  [+ Stage] → Add new stage:
    - Name, position in order, probability, color
    - Cannot add after a terminal stage

  Delete stage:
    - Only if no active opportunities in this stage
    - Or: "Move X opportunities to [select stage] before deleting"
```

### Configure Custom Fields

```
Settings → Contacts → Custom Fields
  → Entity selector: Contact | Account | Opportunity | Conversation

  ┌─────────────────────────────────────────────────────────────┐
  │ Custom Fields — Contact                         [+ Field]   │
  ├─────────────────────────────────────────────────────────────┤
  │ Business Type      Dropdown    Required: No    [Edit] [Del] │
  │   Options: Manufacturer, Trader, Retailer, Distributor      │
  │ Monthly Volume     Text        Required: No    [Edit] [Del] │
  │ Product Interest   Multi-sel   Required: No    [Edit] [Del] │
  │ GST Number         Text        Required: No    [Edit] [Del] │
  └─────────────────────────────────────────────────────────────┘

  [+ Field] → Add custom field:
    - Label
    - Field type: Text, Number, Currency, Date, Dropdown, Multi-select,
                  Checkbox, URL, Email, Phone, Textarea
    - Required: Yes/No
    - Default value (optional)
    - Options (for dropdown/multi-select)
    - Show in: List view, Detail view, Both
    - Searchable: Yes/No
    - Filterable: Yes/No
```

### Configure Assignment Rules

```
Settings → Assignment → Assignment Rules

  Rules evaluated in priority order. First match wins.

  ┌─────────────────────────────────────────────────────────────┐
  │ Assignment Rules                                 [+ Rule]   │
  ├─────────────────────────────────────────────────────────────┤
  │ P1  Source = JustDial    → Assign to: Ravi       [⚙] [Del] │
  │ P2  Source = Facebook    → Assign to: Priya      [⚙] [Del] │
  │ P3  Channel = Email      → Team: Inside Sales    [⚙] [Del] │
  │     Strategy: Round Robin                                    │
  │ P4  After Hours = true   → Unassigned Queue      [⚙] [Del] │
  │ P5  Default              → Team: All Agents      [⚙] [Del] │
  │     Strategy: Load Balanced                                  │
  └─────────────────────────────────────────────────────────────┘

  [+ Rule] → Add rule:
    - Priority (position in list, drag to reorder)
    - Conditions: source, channel, time (business hours/after hours),
                  contact field matches, custom conditions
    - Assignment target:
        Specific agent
        Team (with strategy: round-robin, load-balanced)
        Unassigned queue (manual pick)
    - Agent capacity check: skip agents at max capacity? (yes/no)
    - Agent online check: skip offline agents? (yes/no)
```

### Configure Contact Sources

```
Settings → Contacts → Contact Sources

  ┌─────────────────────────────────────────────────────────────┐
  │ Contact Sources                                  [+ Source] │
  ├─────────────────────────────────────────────────────────────┤
  │ WhatsApp           Active ✓   Icon: 💬          [Edit]     │
  │ JustDial           Active ✓   Icon: 📋          [Edit]     │
  │ Facebook Leads     Active ✓   Icon: 📘          [Edit]     │
  │ IndiaMart          Active ✓   Icon: 🏭          [Edit]     │
  │ Website Form       Active ✓   Icon: 🌐          [Edit]     │
  │ Phone Call         Active ✓   Icon: 📞          [Edit]     │
  │ Referral           Active ✓   Icon: 🤝          [Edit]     │
  │ Trade Show         Inactive   Icon: 🎪          [Edit]     │
  └─────────────────────────────────────────────────────────────┘

  [+ Source] → name, icon/color, active status
  Sources appear in: conversation source dropdown, report filters, assignment rules
```

### Configure SLA Policies

```
Settings → Automation → SLA Policies

  ┌─────────────────────────────────────────────────────────────┐
  │ SLA Policies                                     [+ Policy] │
  ├─────────────────────────────────────────────────────────────┤
  │ First Response Time                                         │
  │   Target: 5 minutes (during business hours)                 │
  │   Warning: at 3 minutes                                     │
  │   Breach: at 5 minutes                                      │
  │   On breach: Notify manager + escalate to next agent        │
  │                                                             │
  │ Follow-Up Response Time                                     │
  │   Target: 30 minutes                                        │
  │   Warning: at 20 minutes                                    │
  │   Breach: at 30 minutes                                     │
  │   On breach: Notify manager                                 │
  │                                                             │
  │ Conversation Resolution Time                                │
  │   Target: 48 hours                                          │
  │   Warning: at 36 hours                                      │
  │   Breach: at 48 hours                                       │
  │   On breach: Auto-reassign to manager                       │
  └─────────────────────────────────────────────────────────────┘

  SLA applies only during business hours (pauses outside).
  SLA tracked per conversation, visible in inbox and reports.
```

---

## Configuration Storage

| Setting | Storage |
|---------|---------|
| Pipeline stages | CRM PostgreSQL: `pipelines`, `pipeline_stages` |
| Custom fields | CRM PostgreSQL: `custom_field_definitions` |
| Assignment rules | CRM PostgreSQL: `assignment_rules` |
| Business hours | CRM PostgreSQL: `crm_workspace_config` (key: `working_hours`) |
| SLA policies | CRM PostgreSQL: `crm_workspace_config` (key: `sla_policies`) |
| Contact sources | CRM PostgreSQL: `contact_sources` |
| Disposition reasons | CRM PostgreSQL: `crm_workspace_config` (key: `disposition_reasons`) |
| Templates | CRM PostgreSQL: `message_templates` |
| Channel credentials | Communication Gateway (encrypted) |
| User roles/capabilities | elauth (via gRPC) |

---

## Validation & Safety

| Scenario | Behavior |
|----------|----------|
| Delete pipeline stage with active opportunities | Block — show count, require move-first |
| Delete custom field with data | Warn — "X records use this field. Data will be archived." |
| Change assignment rules | Apply to NEW conversations only, don't retroactively reassign |
| Disable a channel | Existing conversations on that channel remain, no new outbound |
| Change business hours | SLA recalculation queued for open conversations |
