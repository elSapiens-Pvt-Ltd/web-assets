# Page Spec: Reports

> URL: `/reports`, `/reports/:reportType`
> Role: Manager, Admin (Agent: limited — own metrics only)
> Data source: CRM report APIs (materialized views + aggregation queries)

---

## Layout — Report Index

```
┌──────────────────────────────────────────────────────────────────┐
│ Reports                                                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌─────────────────────┐ ┌─────────────────────┐                 │
│ │ 📊 First Response   │ │ 📊 Sales Funnel     │                 │
│ │ Time (FRT)          │ │                     │                 │
│ │ Agent response time │ │ Stage conversion    │                 │
│ │ analysis            │ │ analysis            │                 │
│ └─────────────────────┘ └─────────────────────┘                 │
│                                                                  │
│ ┌─────────────────────┐ ┌─────────────────────┐                 │
│ │ 📊 Aging Report     │ │ 📊 Agent Activity   │                 │
│ │                     │ │                     │                 │
│ │ Deal aging by stage │ │ Per-agent            │                 │
│ │ and source          │ │ performance metrics │                 │
│ └─────────────────────┘ └─────────────────────┘                 │
│                                                                  │
│ ┌─────────────────────┐ ┌─────────────────────┐                 │
│ │ 📊 Outcome Report   │ │ 📊 Revenue          │                 │
│ │                     │ │ Contribution        │                 │
│ │ Win/loss by new vs  │ │ Revenue by source,  │                 │
│ │ existing customers  │ │ agent, pipeline     │                 │
│ └─────────────────────┘ └─────────────────────┘                 │
│                                                                  │
│ ┌─────────────────────┐ ┌─────────────────────┐                 │
│ │ 📊 Unqualified      │ │ 📊 Conversation     │                 │
│ │ Analysis            │ │ Trends              │                 │
│ │ Disposition reasons │ │ Daily/weekly volume  │                 │
│ │ and patterns        │ │ and channel mix      │                 │
│ └─────────────────────┘ └─────────────────────┘                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

- 8 report cards in 2-column grid
- Click card → navigates to `/reports/:reportType`
- Agent role: only sees FRT (own), Agent Activity (own), Conversation Trends

---

## Layout — Individual Report Page

All reports share a common page layout:

```
┌──────────────────────────────────────────────────────────────────┐
│ ← Reports / First Response Time                    [📥 Export]  │
├──────────────────────────────────────────────────────────────────┤
│ Date: [This Month ▾]  Agent: [All ▾]  Source: [All ▾]          │
│ Pipeline: [All ▾]  [Apply]                                      │
├──────────────────────────────────────────────────────────────────┤
│ View: [Summary] [By Agent] [By Source] [Trend]                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │              Chart / Visualization Area                 │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │              Data Table                                 │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Common Elements

| Element | Behavior |
|---------|----------|
| Back link | Navigate to `/reports` |
| Date filter | Presets: Today, This Week, This Month, Last 30 Days, This Quarter, Custom Range |
| Agent filter | All, specific agent. Agent role: locked to self |
| Source filter | All, or specific contact source |
| Pipeline filter | All, or specific pipeline (for pipeline-related reports) |
| View tabs | Report-specific sub-views (see individual reports below) |
| [Export] | Generate Excel file, download when ready |

---

## Report 1: First Response Time (FRT)

> URL: `/reports/frt`

### Summary View

```
┌──────────────────────────────────────────────────────────────────┐
│ FRT Summary — March 2026                                        │
├──────────────────────────────────────────────────────────────────┤
│ Average FRT:   4m 23s                                           │
│ Median FRT:    3m 10s                                           │
│ < 5 min:       82% (128/156)                                    │
│ < 15 min:      94% (147/156)                                    │
│ < 1 hour:      99% (154/156)                                    │
│ > 1 hour:      1% (2/156)                                       │
├──────────────────────────────────────────────────────────────────┤
│ Distribution:                                                    │
│ 0-1m   ████████████████████ 35%                                 │
│ 1-5m   ██████████████████████████████ 47%                       │
│ 5-15m  ████████ 12%                                             │
│ 15-60m ███ 5%                                                   │
│ >60m   █ 1%                                                     │
└──────────────────────────────────────────────────────────────────┘
```

### By Agent View

| Agent | Avg FRT | Median | < 5min | Conversations | Best | Worst |
|-------|---------|--------|--------|---------------|------|-------|
| Priya | 3m 12s | 2m 45s | 89% | 42 | 30s | 18m |
| Ravi | 5m 30s | 4m 10s | 75% | 38 | 45s | 45m |
| Ankit | 4m 05s | 3m 20s | 82% | 35 | 35s | 22m |

### By Source View

Same table grouped by contact source instead of agent.

### Trend View

Line chart: daily/weekly average FRT over selected date range. Separate line per agent if filtered.

---

## Report 2: Sales Funnel

> URL: `/reports/funnel`

### Cohort View (default)

Tracks a cohort of opportunities created in the date range through stages:

```
Stage        Count  Stage→Stage%  Overall%
New          45     —             100%
Contacted    32     71%           71%
Qualified    20     63%           44%
Proposal     14     70%           31%
Negotiation  8      57%           18%
Won          4      50%           8.9%
Lost         6      —             13%
```

Visual: horizontal funnel bars narrowing left to right.

### Activity View

Shows current stage distribution of ALL open opportunities (not cohort):

```
New          ████████████████ 8
Contacted    ████████████ 6
Qualified    ██████████ 5
Proposal     ████████ 4
Negotiation  ██████ 3
```

### Current Pipeline View

Same as Pipeline Board list view — shows all open opportunities with value, agent, age.

---

## Report 3: Aging Report

> URL: `/reports/aging`

### By Stage View

| Stage | 0-3d | 4-7d | 8-14d | 15-30d | >30d | Total | Avg Age |
|-------|------|------|-------|--------|------|-------|---------|
| New | 5 | 2 | 1 | 0 | 0 | 8 | 3d |
| Contacted | 2 | 2 | 1 | 1 | 0 | 6 | 7d |
| Qualified | 1 | 1 | 2 | 1 | 0 | 5 | 10d |
| Proposal | 0 | 1 | 1 | 1 | 1 | 4 | 18d |

Cells color-coded: green (<7d), amber (7-14d), red (>14d).

### By Source View

Same age buckets grouped by contact source.

### By Agent View

Same age buckets grouped by assigned agent.

---

## Report 4: Agent Activity

> URL: `/reports/agent-activity`

| Metric | Priya | Ravi | Ankit | Team Avg |
|--------|-------|------|-------|----------|
| Conversations handled | 42 | 38 | 35 | 38 |
| Messages sent | 210 | 185 | 160 | 185 |
| Calls made | 15 | 22 | 18 | 18 |
| Avg FRT | 3m 12s | 5m 30s | 4m 05s | 4m 16s |
| Opportunities created | 10 | 8 | 10 | 9 |
| Opportunities won | 4 | 2 | 3 | 3 |
| Revenue won | ₹1,50,000 | ₹80,000 | ₹1,20,000 | ₹1,17,000 |
| Follow-ups completed | 18 | 12 | 15 | 15 |
| Follow-ups overdue | 2 | 5 | 3 | 3 |
| Avg response time | 8m | 15m | 11m | 11m |
| Active deals | 6 | 4 | 7 | 6 |

- Highlight best performer in green, worst in amber per row
- Click agent name → drill-down to agent detail view

---

## Report 5: Outcome Report

> URL: `/reports/outcome`

Compares won/lost outcomes for new vs existing customers:

```
             New Customers    Existing Customers    Total
Won          3 (₹1,20,000)   1 (₹30,000)          4 (₹1,50,000)
Lost         4               2                     6
Open         15              5                     20
Win Rate     17%             33%                   —
Avg Value    ₹40,000         ₹30,000               ₹37,500
Avg Close    22 days         12 days               18 days
```

---

## Report 6: Revenue Contribution

> URL: `/reports/revenue`

### By Source

| Source | Won | Revenue | % of Total | Avg Deal |
|--------|-----|---------|-----------|----------|
| JustDial | 2 | ₹80,000 | 53% | ₹40,000 |
| Facebook | 1 | ₹45,000 | 30% | ₹45,000 |
| Direct | 1 | ₹25,000 | 17% | ₹25,000 |

### By Agent

Same table grouped by agent.

### By Pipeline

Same table grouped by pipeline.

### Trend

Bar chart: monthly revenue over last 6 months, stacked by source.

---

## Report 7: Unqualified Analysis

> URL: `/reports/unqualified`

| Disposition Reason | Count | % |
|-------------------|-------|---|
| Wrong number | 8 | 25% |
| Not interested | 6 | 19% |
| Competitor customer | 5 | 16% |
| Budget constraints | 4 | 13% |
| Location not serviceable | 3 | 9% |
| Duplicate | 3 | 9% |
| Other | 3 | 9% |

- Pie chart visualization
- Click reason → drill-down list of contacts with that disposition

---

## Report 8: Conversation Trends

> URL: `/reports/conversation-trends`

### Daily View

```
          Mon  Tue  Wed  Thu  Fri  Sat  Sun
Inbound   12   15   18   14   16   8    3
Outbound  10   12   14   12   14   6    2
Total     22   27   32   26   30   14   5
```

Line chart with dual axis: inbound vs outbound.

### By Channel

| Channel | Count | % | Avg Messages |
|---------|-------|---|-------------|
| WhatsApp | 85 | 55% | 12 |
| Voice | 42 | 27% | 1 (call) |
| Email | 18 | 12% | 4 |
| Lead Capture | 11 | 7% | 1 |

### By Status

Pie chart: Open, Resolved, Closed, Pending.

---

## Export

All reports support Excel export:

```
[📥 Export] → dropdown:
  ○ Current view (what's visible)
  ○ Full report (all data, all views)

→ Click triggers async export
→ Toast: "Generating report..."
→ Toast (on complete): "Report ready — [Download]"
→ Also available: GET /exports/:id/download
```

Export format: .xlsx with:
- Sheet 1: Summary metrics
- Sheet 2: Detail data table
- Header row with filters applied noted

---

## State Management

| State | Source | Cache |
|-------|--------|-------|
| Report data | CRM API | React Query, 5min stale |
| Filter state | URL params | — |
| Export status | CRM API polling | Poll every 3s until complete |

---

## API Endpoints

| Report | Method | Endpoint |
|--------|--------|----------|
| FRT | GET | `/reports/frt?view=summary&filters` |
| Sales Funnel | GET | `/reports/funnel?view=cohort&filters` |
| Aging | GET | `/reports/aging?view=by_stage&filters` |
| Agent Activity | GET | `/reports/agent-activity?filters` |
| Outcome | GET | `/reports/outcome?filters` |
| Revenue | GET | `/reports/revenue?view=by_source&filters` |
| Unqualified | GET | `/reports/unqualified?filters` |
| Conversation Trends | GET | `/reports/conversation-trends?view=daily&filters` |
| Export | POST | `/exports` |
| Export status | GET | `/exports/:id` |
| Export download | GET | `/exports/:id/download` |
