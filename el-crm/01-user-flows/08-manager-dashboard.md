# Manager Dashboard

> Role: Manager, Admin
> Trigger: Manager logs in or navigates to Dashboard
> Primary screen: Dashboard (/dashboard)

---

## Flow Summary

The dashboard is the manager's home screen. It provides a real-time overview of team performance, pipeline health, and key metrics. Each widget is clickable and navigates to the full report for deeper analysis.

---

## Dashboard Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Dashboard              [This Month ▾] [vs Last Month]  [⟳]     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│ │ Pipeline    │ │ Win Rate    │ │ Avg FRT     │ │ Open Convos ││
│ │ ₹12,40,000  │ │ 32% ↑ +5%  │ │ 5.2 min     │ │ 87          ││
│ │ Weighted:   │ │             │ │ Target: 5m  │ │ Unassigned:8││
│ │ ₹6,80,000   │ │ 45 won      │ │ ● On track  │ │ SLA breach:3││
│ │ 28 deals    │ │ of 140      │ │             │ │             ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│                                                                  │
│ ┌──────────────────────────────┐ ┌──────────────────────────────┐│
│ │ Conversion Funnel            │ │ Team Activity Today          ││
│ │                              │ │                              ││
│ │ New         ███████████ 200  │ │ Agent    Calls Msgs F-ups   ││
│ │ Contacted   ████████    150  │ │ Priya    12    45   8       ││
│ │ Qualified   █████        80  │ │ Ravi     8     32   5       ││
│ │ Opportunity ███          45  │ │ Ankit    15    28   12      ││
│ │ Won         ██           20  │ │ Total    35    105  25      ││
│ │                              │ │                              ││
│ │ [View Full Report →]         │ │ [View Full Report →]         ││
│ └──────────────────────────────┘ └──────────────────────────────┘│
│                                                                  │
│ ┌──────────────────────────────┐ ┌──────────────────────────────┐│
│ │ SLA Compliance               │ │ Top Performers               ││
│ │                              │ │                              ││
│ │ Within SLA   ████████  82%  │ │ 🥇 Priya — 15 won, ₹3.2L   ││
│ │ Warning      ██        12%  │ │ 🥈 Ankit — 12 won, ₹2.8L   ││
│ │ Breached     █          6%  │ │ 🥉 Ravi  — 10 won, ₹2.1L   ││
│ │                              │ │                              ││
│ │ 5 breaches today             │ │ Based on: Won deals + revenue││
│ │ [View Details →]             │ │ [View Full Report →]         ││
│ └──────────────────────────────┘ └──────────────────────────────┘│
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Widget Specifications

### 1. Pipeline Summary Card
- **Data**: Total pipeline value, weighted value, deal count
- **Trend**: Arrow + percentage vs previous period
- **Click**: Navigate to `/pipeline`

### 2. Win Rate Card
- **Data**: (Won / Total closed) × 100, won count, total count
- **Trend**: vs previous period
- **Click**: Navigate to `/reports/outcome`

### 3. Average FRT Card
- **Data**: Average first response time across team
- **Visual**: Gauge against SLA target. Green (within), Amber (close), Red (breach)
- **Click**: Navigate to `/reports/frt`

### 4. Open Conversations Card
- **Data**: Total open, unassigned count, SLA breach count
- **Alert**: Red badge if SLA breaches > 0
- **Click**: Navigate to `/inbox?filter=open` (or `?filter=sla_breached`)

### 5. Conversion Funnel
- **Data**: Current status funnel (all open conversations by stage)
- **Visual**: Horizontal bar chart showing progressive narrowing
- **Click**: Navigate to `/reports/funnel`

### 6. Team Activity Today
- **Data**: Per-agent: calls made, messages sent, follow-ups completed
- **Visual**: Table, sortable by any column
- **Click row**: Navigate to `/reports/activity?agent=:id`

### 7. SLA Compliance
- **Data**: Percentage of conversations within SLA, warning, breached
- **Visual**: Donut chart or stacked bar
- **Click**: Navigate to `/inbox?filter=sla_breached`

### 8. Top Performers
- **Data**: Top 3 agents by won deals and revenue this period
- **Click**: Navigate to `/reports/revenue`

---

## Date Controls

```
[This Month ▾]  → Presets: Today, This Week, This Month, Last Month,
                   Last 7 Days, Last 30 Days, This Quarter, Custom Range

[vs Last Month] → Comparison toggle: shows trend arrows (↑↓) and
                   percentage change on each card
                   Green = improvement, Red = decline

[⟳]             → Refresh all widgets (data auto-refreshes every 60 seconds)
```

---

## Manager Actions from Dashboard

| Observation | Action |
|-------------|--------|
| SLA breaches > 0 | Click → see breached conversations → reassign or follow up |
| Unassigned conversations | Click → assign manually or review assignment rules |
| Agent with low activity | Click agent name → view detail → message agent or reassign load |
| Pipeline value declining | Click → review pipeline → identify stuck deals |
| Win rate dropping | Click → outcome report → analyze loss reasons |

---

## Data Loading

| Widget | API Call | Refresh |
|--------|----------|---------|
| Pipeline Summary | GET /dashboard/pipeline | 60s auto |
| Win Rate | GET /dashboard/outcome | 60s auto |
| FRT | GET /dashboard/frt | 60s auto |
| Open Conversations | GET /dashboard/conversations | 30s auto (more real-time) |
| Funnel | GET /dashboard/funnel | 60s auto |
| Team Activity | GET /dashboard/activity | 30s auto |
| SLA | GET /dashboard/sla | 30s auto |
| Top Performers | GET /dashboard/top-performers | 60s auto |

All endpoints accept `start_date`, `end_date` params. Workspace_id from JWT.
