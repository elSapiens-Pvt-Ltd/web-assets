# Search & Filters

> Role: All
> Trigger: User searches for conversations, contacts, or data
> Primary screen: Global search bar, Inbox filters, list filters

---

## Global Search

```
Top navigation bar contains search input (Ctrl+K / Cmd+K to focus)

┌─────────────────────────────────────────────────┐
│ 🔍 Search conversations, contacts, accounts...  │
└─────────────────────────────────────────────────┘

User types: "Rahul"

Results dropdown (grouped by type):
┌─────────────────────────────────────────────────┐
│ Contacts (3)                                     │
│   Rahul Verma — Acme Corp — +91 98765 43210    │
│   Rahul Sharma — TechParts — +91 87654 32109   │
│   Rahul K — FreshMart — rahul@freshmart.com     │
│                                                  │
│ Conversations (5)                                │
│   Rahul Verma — "Can you share the quotation"   │
│   Rahul Sharma — "Need samples for Grade A"     │
│   ...                                            │
│                                                  │
│ Accounts (1)                                     │
│   Rahul Industries Pvt Ltd                       │
│                                                  │
│ [View all results →]                             │
└─────────────────────────────────────────────────┘

Search scope:
  - Contact name, phone, email (via accounts-api gRPC)
  - Account/entity name (via accounts-api gRPC)
  - Conversation message text (CRM full-text search)
  - Custom field values (CRM)

Agent: searches only their assigned data (unless capability allows all)
Manager: searches all workspace data
```

---

## Inbox Filters

```
Conversation List panel has filter controls:

┌─────────────────────────┐
│ [All ▾] [🔍 Search]     │
│                          │
│ Quick Filters:           │
│ [Mine] [Unread] [Open]  │
│ [Unassigned] [Due]      │
│                          │
│ Advanced Filters:        │
│ ┌──────────────────────┐│
│ │ Stage:    [All ▾]    ││
│ │ Channel:  [All ▾]    ││
│ │ Source:   [All ▾]    ││
│ │ Agent:    [All ▾]    ││
│ │ Priority: [All ▾]    ││
│ │ SLA:      [All ▾]    ││
│ │ Date:     [Range ▾]  ││
│ │ Tags:     [Select ▾] ││
│ │                      ││
│ │ [Apply] [Clear] [Save]│
│ └──────────────────────┘│
└─────────────────────────┘
```

### Filter Definitions

| Filter | Options | Behavior |
|--------|---------|----------|
| **Status** | Open, Pending, Closed, All | Conversations by lifecycle status |
| **Assignment** | Mine, Unassigned, All, Specific Agent | Who it's assigned to |
| **Stage** | Workspace-configured stages | Conversation pipeline stage |
| **Channel** | WhatsApp, Voice, Email, All | Primary or active channel |
| **Source** | Workspace-configured sources | Lead origin |
| **Priority** | Normal, High, Urgent, All | Conversation priority flag |
| **SLA** | Within SLA, Warning, Breached, All | SLA status |
| **Unread** | Unread only toggle | Has messages agent hasn't seen |
| **Follow-up** | Due today, Overdue, Upcoming | Has follow-up reminders |
| **Date** | Created date range, Last message date range | Time-based |
| **Tags** | Custom tags (workspace-configured) | Categorical labels |

### Saved Filters

```
Agent saves a frequently used filter combination:
  → Clicks [Save] → names it: "Hot JustDial Leads"
  → Filter: Source = JustDial, Stage = New or Contacted, Unread = Yes
  → Saved filter appears as quick access tab

Saved filters are per-user, per-workspace.
Managers can create shared filters visible to the team.
```

### Sort Options

| Sort | Description |
|------|-------------|
| Newest message first | Default — most recent activity on top |
| Oldest unanswered first | Prioritizes conversations waiting longest for reply |
| Priority | Urgent → High → Normal |
| SLA status | Breached → Warning → OK |
| Created date | Newest or oldest first |

---

## Contact List Filters

```
Contacts page (table/list view):

Filters:
  - Lifecycle stage: Lead, Customer, Inactive, All
  - Account: specific account or all
  - Source: where the contact originated
  - Agent: assigned agent
  - Custom fields: any custom field as filter
  - Created date range
  - Last activity date range
  - Has conversation: Yes/No
  - Has opportunity: Yes/No

Columns (configurable):
  Name | Phone | Email | Account | Stage | Source | Agent | Last Activity | Created
  [+ Add Column] from custom fields
```

---

## Pipeline Filters

```
Pipeline board filters:
  - Agent: [All | Specific agent]
  - Date range: Created date or Expected close date
  - Source: Lead source
  - Value range: Min-Max
  - Custom fields on opportunity

Pipeline list view supports all the above plus:
  - Sort by: Value, Close date, Age, Stage
  - Group by: Agent, Source, Stage
```

---

## Report Filters

All reports support:

| Filter | Type | Description |
|--------|------|-------------|
| Date range | Date picker or preset | `today`, `yesterday`, `this_week`, `last_week`, `this_month`, `last_month`, `last_7_days`, `last_30_days`, custom range |
| Agent | Multi-select dropdown | Filter by specific agents (manager only) |
| Source | Multi-select dropdown | Filter by lead sources |
| Channel | Multi-select dropdown | Filter by communication channel |
| Conversation type | Toggle | Contact vs Opportunity vs All |

---

## Filter Architecture

```
Frontend:
  → User selects filters
  → Builds filter object: { stage: ["new", "contacted"], channel: "whatsapp", ... }
  → Sends as query params (GET) or request body (POST) to CRM API

Backend (Go):
  → Filters module parses and validates filter input
  → Builds SQL WHERE clauses with parameterized queries (no injection)
  → Always prepends: WHERE workspace_id = ? (from JWT context)
  → Agent role: also prepends AND agent_id = ? (from JWT)
  → Executes query with pagination: LIMIT ? OFFSET ?

Response:
  {
    "data": [...],
    "pagination": { "page": 1, "per_page": 25, "total": 142, "total_pages": 6 },
    "filters_applied": { "stage": ["new", "contacted"], "channel": "whatsapp" }
  }
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+K / Cmd+K | Focus global search |
| Escape | Close search results / clear filters |
| ↑↓ | Navigate search results |
| Enter | Open selected result |
| Ctrl+F | Focus inbox search (within conversation list) |
