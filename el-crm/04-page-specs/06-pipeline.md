# Page Spec: Pipeline Board

> URL: `/pipeline`
> Role: Agent (own deals), Manager (team deals), Admin (all deals)
> Data source: CRM (pipelines, pipeline_stages, opportunities)

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Pipeline: [Sales Pipeline ▾]    View: [Kanban] [List] [Forecast]│
│ Agent: [All ▾]  Source: [All ▾]  Date: [This Quarter ▾]        │
│ [🔍 Search]                                                     │
├──────────────────────────────────────────────────────────────────┤
│ Summary Bar:                                                     │
│ Total: ₹12,40,000 (28) │ Weighted: ₹6,80,000 │ Avg: ₹45,000  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Kanban / List / Forecast view content area                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Toolbar

| Element | Behavior |
|---------|----------|
| Pipeline selector | Dropdown of workspace pipelines. Default: first pipeline. Persisted to URL |
| View toggle | Kanban (default), List, Forecast (Manager/Admin only) |
| Agent filter | All (Manager/Admin default), or specific agent. Agent role sees only own deals |
| Source filter | Filter by contact source (JustDial, Facebook, etc.) |
| Date filter | Presets: This Quarter, This Month, Last 30 Days, Custom Range. Filters by `created_at` |
| Search | Search opportunity by contact name or entity name |

---

## Kanban View (Default)

```
┌─────────────┬─────────────┬─────────────┬─────────────┬──────────┐
│ New (8)     │ Contacted(6)│ Qualified(5)│ Proposal (4)│ Nego (3) │
│ ₹3,20,000  │ ₹2,10,000  │ ₹2,80,000  │ ₹2,50,000  │₹1,80,000│
├─────────────┼─────────────┼─────────────┼─────────────┼──────────┤
│┌───────────┐│┌───────────┐│┌───────────┐│┌───────────┐│┌────────┐│
││ Rajesh K  │││ Sneha P   │││ GreenFoods│││ Amit Shah │││BuildMax││
││ Acme Corp │││ TechParts │││ ₹80,000   │││ ₹1,50,000│││₹90,000 ││
││ ₹45,000   │││ ₹60,000   │││ Priya     │││ Ravi      │││Ankit   ││
││ 2d ago    │││ 5d ago    │││ 12d  ⚠   │││ 8d  ⚠    │││3d      ││
│└───────────┘│└───────────┘│└───────────┘│└───────────┘│└────────┘│
│┌───────────┐│┌───────────┐│             │┌───────────┐│          │
││ Priya M   │││ Vivek J   ││             ││ TechParts ││          │
││ FreshMart │││ ₹35,000   ││             ││ ₹1,00,000││          │
││ ₹25,000   │││ 3d ago    ││             ││ 20d  🔴   ││          │
││ 1d ago    │││           ││             │└───────────┘│          │
│└───────────┘│└───────────┘│             │             │          │
│ ...         │             │             │             │          │
└─────────────┴─────────────┴─────────────┴─────────────┴──────────┘
```

### Column Headers

Each column represents a pipeline stage:
- Stage name
- Count of opportunities in stage
- Total value of opportunities in stage
- Columns ordered by `pipeline_stages.stage_order`
- Terminal stages (Won, Lost) shown at the end with collapsed view

### Opportunity Cards

| Element | Source | Display |
|---------|--------|---------|
| Contact name | accounts-api (cached) | First line, bold |
| Account name | accounts-api (cached) | Second line, muted |
| Value | `opportunities.expected_value` | Formatted currency |
| Age in stage | `opportunities.stage_entered_at` | Relative time |
| Agent name | elauth (cached) | Small text (Manager/Admin view only) |
| Priority indicator | `opportunities.priority` | 🔴 Urgent, 🟡 High (only if set) |

### Card Border Colors (Age in Stage)

| Color | Condition | Meaning |
|-------|-----------|---------|
| Green (left border) | < 7 days | On track |
| Amber (left border) | 7–14 days | Attention needed |
| Red (left border) | > 14 days | Stuck deal |

Thresholds are workspace-configurable via `crm_workspace_config.stage_aging_thresholds`.

### Drag and Drop

- Drag card between columns → stage change
- On drop: confirmation if moving backward (e.g., Proposal → Qualified)
- On drop to terminal stage (Won/Lost): opens close dialog (see below)
- Agent can only drag own cards
- Manager/Admin can drag any card
- Capability: `pipeline:manage_own` (own) or `pipeline:manage_all` (any)

### Card Click

Opens opportunity detail slide-over (right panel, 400px):

```
┌────────────────────────────────────────┐
│ Opportunity Detail              [✕]    │
├────────────────────────────────────────┤
│ Rajesh Kumar — Acme Corp              │
│ ₹2,50,000  |  Sales Pipeline          │
│ Stage: Proposal (8 days)              │
│ Agent: Priya Sharma                    │
│ Expected Close: Mar 30, 2026          │
│ Priority: Normal                       │
│ Source: JustDial                       │
├────────────────────────────────────────┤
│ Stage History                          │
│ Mar 12 — Proposal (current, 8d)       │
│ Mar 8  — Qualified (4d)               │
│ Mar 5  — Contacted (3d)               │
│ Mar 4  — New (1d)                     │
├────────────────────────────────────────┤
│ Custom Fields                          │
│ Product Interest: Turmeric Powder     │
│ Quantity: 500 kg                       │
├────────────────────────────────────────┤
│ Activities                             │
│ Mar 11 — Note: Sent revised quote     │
│ Mar 9  — Follow-up: Called, discussed │
│ Mar 5  — Note: Initial enquiry        │
├────────────────────────────────────────┤
│ [Add Note] [Create Follow-up]         │
│ [Change Stage ▾] [Transfer] [Close ▾] │
└────────────────────────────────────────┘
```

---

## Close Opportunity Dialog

### Close Won

```
┌────────────────────────────────────────┐
│ Close as Won                           │
│                                        │
│ Actual Value:  [₹2,50,000        ]    │
│ Close Date:    [Mar 12, 2026     ]    │
│ Notes:         [First bulk order  ]    │
│                                        │
│ □ Close related conversation           │
│ □ Create follow-up for repeat order    │
│                                        │
│ [Cancel]                    [Close Won]│
└────────────────────────────────────────┘
```

### Close Lost

```
┌────────────────────────────────────────┐
│ Close as Lost                          │
│                                        │
│ Reason: [Select ▾]                     │
│   ○ Price too high                     │
│   ○ Competitor chosen                  │
│   ○ No budget                          │
│   ○ No response                        │
│   ○ Requirements changed               │
│   ○ Other                              │
│                                        │
│ Notes: [                          ]    │
│                                        │
│ □ Close related conversation           │
│                                        │
│ [Cancel]                   [Close Lost]│
└────────────────────────────────────────┘
```

- Loss reasons: workspace-configured list
- Both dialogs: POST `/opportunities/:id/close`

---

## List View

```
┌──────────────────────────────────────────────────────────────────┐
│ Contact       Account     Stage     Value      Agent   Age  Exp │
│ ─────────────────────────────────────────────────────────────────│
│ Rajesh Kumar  Acme Corp   Proposal  ₹2,50,000  Priya  8d  Mar30│
│ GreenFoods    GreenFoods  Qualified ₹80,000    Priya  12d Apr15│
│ Amit Shah     BuildRight  Proposal  ₹1,50,000  Ravi   8d  Mar25│
│ ...                                                              │
│                                  Page 1 of 3  [< 1 2 3 >]      │
└──────────────────────────────────────────────────────────────────┘
```

- Sortable columns: Contact, Stage, Value, Agent, Age, Expected Close
- Click row → same slide-over as card click
- Bulk select: checkboxes for bulk actions (Assign, Change Stage, Close)
- Pagination: 25 per page

---

## Forecast View (Manager/Admin Only)

```
┌──────────────────────────────────────────────────────────────────┐
│ Pipeline Forecast                                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ March 2026                                                       │
│ ┌──────────┬──────────┬──────────┬──────────┐                   │
│ │ Total    │ Weighted │ Deals    │ vs Target│                   │
│ │₹4,50,000 │₹2,80,000 │ 12       │ 70% ⚠  │                   │
│ └──────────┴──────────┴──────────┴──────────┘                   │
│                                                                  │
│ Agent Breakdown:                                                 │
│ Priya:  ₹1,50,000 (5 deals) │ Weighted: ₹90,000               │
│ Ravi:   ₹1,80,000 (4 deals) │ Weighted: ₹1,10,000             │
│ Ankit:  ₹1,20,000 (3 deals) │ Weighted: ₹80,000               │
│                                                                  │
│ April 2026                                                       │
│ ┌──────────┬──────────┬──────────┬──────────┐                   │
│ │₹5,20,000 │₹3,10,000 │ 10       │ 78% ⚠  │                   │
│ └──────────┴──────────┴──────────┴──────────┘                   │
│ ...                                                              │
└──────────────────────────────────────────────────────────────────┘
```

- Groups by expected close month (next 3 months by default)
- Weighted value = SUM(deal_value × stage_probability)
- vs Target = weighted_value / workspace_monthly_target × 100
- Agent breakdown expandable per month
- Data: `GET /pipelines/:id/forecast?months=3`

---

## New Opportunity Dialog

```
┌────────────────────────────────────────┐
│ New Opportunity                        │
│                                        │
│ Contact:     [Search contact...   ▾]  │
│ Pipeline:    [Sales Pipeline      ▾]  │
│ Stage:       [New                 ▾]  │
│ Value:       [₹                     ] │
│ Exp. Close:  [📅                    ] │
│ Priority:    [Normal              ▾]  │
│                                        │
│ Custom Fields                          │
│ Product:     [                      ] │
│ Quantity:    [                      ] │
│                                        │
│ [Cancel]                      [Create]│
└────────────────────────────────────────┘
```

- Contact search: typeahead via accounts-api
- Pipeline: workspace pipelines (defaults to first)
- Stage: defaults to first non-terminal stage
- Custom fields: rendered dynamically from `custom_field_definitions` where `entity_type = 'opportunity'`

---

## State Management

| State | Source | Cache |
|-------|--------|-------|
| Pipeline list | CRM API | React Query, 10min stale |
| Stages | CRM API | React Query, 10min stale |
| Opportunities (kanban) | CRM API | React Query, 30s stale |
| Opportunities (list) | CRM API | React Query, 30s stale |
| Forecast data | CRM API | React Query, 2min stale |

- Drag-and-drop uses optimistic updates (immediate UI, revert on error)
- WebSocket event `opportunity.stage_changed` triggers refetch

---

## API Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| List pipelines | GET | `/pipelines` |
| Get pipeline stages | GET | `/pipelines/:id/stages` |
| List opportunities | GET | `/pipelines/:id/opportunities?filters` |
| Get forecast | GET | `/pipelines/:id/forecast?months=3` |
| Create opportunity | POST | `/opportunities` |
| Update opportunity | PUT | `/opportunities/:id` |
| Change stage | POST | `/opportunities/:id/stage` |
| Close opportunity | POST | `/opportunities/:id/close` |
| Transfer opportunity | POST | `/opportunities/:id/transfer` |
| Bulk actions | POST | `/opportunities/bulk` |

---

## Responsive Behavior

| Breakpoint | Layout Change |
|------------|--------------|
| ≥1280px | Full kanban with all columns visible |
| 1024–1279px | Kanban with horizontal scroll |
| 768–1023px | List view default, kanban available with scroll |
| <768px | List view only, slide-over becomes full screen |
