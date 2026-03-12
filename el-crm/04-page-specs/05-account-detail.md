# Page Spec: Account Detail

> URL: `/accounts/:entityId`
> Role: All
> Data source: accounts-api (entity + members) + CRM (conversations, opportunities, activities)

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ ← Accounts / Acme Corp                          [Edit] [⋮ More]│
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ACME CORP                                Industry: Spices       │
│  🏢 Manufacturing                         Source: JustDial       │
│  Agent: Priya Sharma                      Created: Mar 1, 2026   │
│                                                                  │
│  ┌─────────┬─────────┬──────────┬──────────┐                    │
│  │Contacts │ Pipeline│Activities│  Details  │                    │
│  ├─────────┴─────────┴──────────┴──────────┤                    │
│  │                                          │                    │
│  │  (Tab content area)                      │                    │
│  │                                          │                    │
│  │                                          │                    │
│  └──────────────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Header Section

| Element | Source | Behavior |
|---------|--------|----------|
| Back link | Router | Navigate to `/accounts` |
| Entity name | accounts-api `entity.name` | Display only |
| Industry | accounts-api `entity.industry` | Display only |
| Source | CRM `contact_sources` | Display only |
| Agent | elauth `person.name` via CRM `conversations.agent_id` | Primary agent (most conversations) |
| Created date | accounts-api `entity.created_at` | Relative or absolute based on age |
| [Edit] button | — | Opens edit dialog (delegates to accounts-api) |
| [⋮ More] menu | — | Merge account, Delete, Export |

### More Menu Actions

| Action | Capability Required | Behavior |
|--------|-------------------|----------|
| Merge Account | `accounts:merge` | Opens merge dialog — select target account, preview merge, confirm |
| Delete Account | `accounts:delete` | Confirmation dialog. Only if 0 open conversations and 0 open opportunities |
| Export | `reports:export` | Export account data as Excel |

---

## Tab: Contacts

Default tab. Shows all people (members) associated with this entity.

```
┌──────────────────────────────────────────────────────────────────┐
│ Contacts (5)                                   [+ Add Contact]  │
├──────────────────────────────────────────────────────────────────┤
│ Name              Role          Phone           Conversations    │
│ Rajesh Kumar      Owner         +91 98765 43210    8             │
│ Priya Mehta       Procurement   +91 87654 32109    3             │
│ Amit Shah         Finance       +91 76543 21098    1             │
│ Sneha Patel       Operations    sneha@acme.com     2             │
│ Vivek Joshi       Sales         +91 65432 10987    0             │
└──────────────────────────────────────────────────────────────────┘
```

- Data: accounts-api `GET /entities/:id/members` + CRM conversation counts
- Click row → `/contacts/:personId`
- [+ Add Contact] → search existing contacts (accounts-api) or create new
- Role column: from `membership.role` in accounts-api

---

## Tab: Pipeline

Shows all opportunities linked to contacts of this account.

```
┌──────────────────────────────────────────────────────────────────┐
│ Opportunities (3)                          [+ New Opportunity]  │
├──────────────────────────────────────────────────────────────────┤
│ Contact        Pipeline   Stage       Value      Expected Close │
│ Rajesh Kumar   Sales      Proposal    ₹2,50,000  Mar 30, 2026  │
│ Rajesh Kumar   Sales      Qualified   ₹1,20,000  Apr 15, 2026  │
│ Priya Mehta    Sales      Contacted   ₹80,000    May 1, 2026   │
├──────────────────────────────────────────────────────────────────┤
│ Total Value: ₹4,50,000  |  Weighted: ₹2,10,000                │
└──────────────────────────────────────────────────────────────────┘
```

- Data: CRM `GET /opportunities?entity_id=:entityId`
- Click row → opportunity detail slide-over
- [+ New Opportunity] → create form (pre-fills account)
- Summary row shows total and weighted (stage probability × value)

---

## Tab: Activities

Unified activity feed across all contacts of this account.

```
┌──────────────────────────────────────────────────────────────────┐
│ Activities                    Filter: [All ▾]  [+ Add Note]     │
├──────────────────────────────────────────────────────────────────┤
│ Mar 12, 10:30 — Note (Priya)                                   │
│   "Customer requested revised pricing for Q2 order"             │
│                                                                  │
│ Mar 11, 15:00 — Stage Change                                    │
│   Rajesh Kumar: Qualified → Proposal (Sales Pipeline)           │
│                                                                  │
│ Mar 10, 09:00 — Follow-up Completed (Priya)                    │
│   Called Rajesh Kumar — discussed delivery timeline              │
│                                                                  │
│ Mar 8, 14:20 — Conversation Created                             │
│   Priya Mehta via WhatsApp — assigned to Priya                  │
│                                                                  │
│                        [Load More]                               │
└──────────────────────────────────────────────────────────────────┘
```

- Data: CRM `GET /activities?entity_id=:entityId&sort=-created_at`
- Filter dropdown: All, Notes, Stage Changes, Follow-ups, Conversations, Assignments
- [+ Add Note] → inline note form (text + optional attachment)
- Pagination: cursor-based "Load More"

---

## Tab: Details

Account metadata and custom fields.

```
┌──────────────────────────────────────────────────────────────────┐
│ Account Information                                  [Edit]     │
├──────────────────────────────────────────────────────────────────┤
│ Name:            Acme Corp                                      │
│ Industry:        Spices                                         │
│ Website:         www.acmecorp.in                                │
│ Annual Revenue:  ₹2,00,00,000                                  │
│ Employee Count:  150                                            │
│                                                                  │
│ Billing Address                                                 │
│ 42, Industrial Area Phase II, Chandigarh 160002                │
│                                                                  │
│ Shipping Address                                                │
│ Same as billing                                                 │
├──────────────────────────────────────────────────────────────────┤
│ Custom Fields                                                   │
├──────────────────────────────────────────────────────────────────┤
│ Distribution Type:    Wholesale                                 │
│ Payment Terms:        Net 30                                    │
│ Credit Limit:         ₹5,00,000                                │
└──────────────────────────────────────────────────────────────────┘
```

- Data: accounts-api `GET /entities/:id` (base fields) + CRM `GET /custom-fields?entity_type=account&entity_id=:id` (custom fields)
- [Edit] → opens edit dialog, delegates to accounts-api for base fields, CRM API for custom fields
- Custom fields are workspace-configured (see Settings)

---

## Edit Dialog

Opens as a modal dialog when [Edit] is clicked (header or Details tab).

```
┌────────────────────────────────────────────┐
│ Edit Account                               │
│                                            │
│ Name:        [Acme Corp              ]     │
│ Industry:    [Spices           ▾]          │
│ Website:     [www.acmecorp.in        ]     │
│ Annual Rev:  [2,00,00,000            ]     │
│ Employees:   [150                    ]     │
│                                            │
│ Billing Address                            │
│ [42, Industrial Area Phase II...     ]     │
│ [Chandigarh      ] [160002          ]      │
│                                            │
│ Custom Fields                              │
│ Distribution: [Wholesale      ▾]          │
│ Payment:      [Net 30         ▾]          │
│ Credit Limit: [5,00,000             ]      │
│                                            │
│ [Cancel]                     [Save]        │
└────────────────────────────────────────────┘
```

- Base fields → `PUT /entities/:id` (accounts-api via CRM backend)
- Custom fields → `PUT /custom-fields` (CRM API)
- Validation: Name required, industry from predefined list

---

## State Management

| State | Source | Cache |
|-------|--------|-------|
| Entity details | accounts-api via CRM | React Query, 5min stale |
| Members list | accounts-api via CRM | React Query, 5min stale |
| Opportunities | CRM API | React Query, 2min stale |
| Activities | CRM API | React Query, 1min stale |
| Custom fields | CRM API | React Query, 5min stale |

---

## API Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Get account detail | GET | `/accounts/:entityId` |
| Update account | PUT | `/accounts/:entityId` |
| Get members | GET | `/accounts/:entityId/contacts` |
| Get opportunities | GET | `/opportunities?entity_id=:entityId` |
| Get activities | GET | `/activities?entity_type=account&entity_id=:entityId` |
| Add note | POST | `/activities` |
| Get custom fields | GET | `/custom-fields?entity_type=account&entity_id=:entityId` |
| Update custom fields | PUT | `/custom-fields` |
| Merge account | POST | `/accounts/:entityId/merge` |
| Delete account | DELETE | `/accounts/:entityId` |
