# Page Spec: Dashboard

> URL: `/dashboard`
> Role: Manager, Admin (Agent redirected to Inbox)
> Data source: CRM reports/aggregation APIs

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Dashboard                        Date: [This Month ▾] [Refresh] │
│ Agent: [All ▾]  Source: [All ▾]  Pipeline: [All ▾]             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐           │
│ │ Pipeline      │ │ Revenue       │ │ Conversations │           │
│ │ ₹12,40,000    │ │ ₹3,80,000    │ │ 156 open      │           │
│ │ 28 deals      │ │ Won this month│ │ 42 unresponded│           │
│ │ Weighted:     │ │ vs ₹5L target│ │ Avg FRT: 4m   │           │
│ │ ₹6,80,000     │ │ ████████░░76%│ │               │           │
│ └───────────────┘ └───────────────┘ └───────────────┘           │
│                                                                  │
│ ┌─────────────────────────────┐ ┌─────────────────────────────┐ │
│ │ Sales Funnel                │ │ Team Activity               │ │
│ │                             │ │                             │ │
│ │ New        ████████████ 45  │ │ Agent    Conv  Opp  FRT     │ │
│ │ Contacted  █████████   32  │ │ Priya    42    10   3m      │ │
│ │ Qualified  ██████      20  │ │ Ravi     38    8    5m      │ │
│ │ Proposal   ████        14  │ │ Ankit    35    10   4m      │ │
│ │ Negotiation██          8   │ │ Meera    41    7    3m      │ │
│ │ Won        █           4   │ │                             │ │
│ │ Conv Rate: 8.9%        │ │                             │ │
│ └─────────────────────────────┘ └─────────────────────────────┘ │
│                                                                  │
│ ┌─────────────────────────────┐ ┌─────────────────────────────┐ │
│ │ SLA Compliance              │ │ Win Rate Trend              │ │
│ │                             │ │                             │ │
│ │ FRT < 5min:  92% ✅        │ │     40%│    ╱╲              │ │
│ │ FRT < 15min: 98% ✅        │ │     30%│ ╱╲╱  ╲╱╲          │ │
│ │ FRT < 1hr:   100% ✅       │ │     20%│╱        ╲         │ │
│ │                             │ │     10%│                    │ │
│ │ Response (business hrs):    │ │        └──────────────      │ │
│ │ Within 1hr:  85% ⚠         │ │        Oct Nov Dec Jan Feb  │ │
│ │ Within 4hr:  95% ✅        │ │ Team avg: 32%               │ │
│ └─────────────────────────────┘ └─────────────────────────────┘ │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Alerts                                                       │ │
│ │ ⚠ 5 deals stuck > 14 days in "Proposal" stage              │ │
│ │ ⚠ 2 deals past expected close date                          │ │
│ │ ⚠ Agent Ravi: 0 new opportunities this week                │ │
│ │ ⚠ 8 overdue follow-ups across team                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Filters (Top Bar)

| Filter | Options | Default |
|--------|---------|---------|
| Date range | Today, This Week, This Month, This Quarter, Last 30 Days, Custom | This Month |
| Agent | All, specific agent | All |
| Source | All, specific source | All |
| Pipeline | All, specific pipeline | All |
| [Refresh] | Manual refresh all widgets | — |

Filters apply to all widgets simultaneously. Filter state persisted in URL query params.

---

## Widget Grid

Layout: 3 columns on desktop, 2 on tablet, 1 on mobile. Widgets arranged in order shown.

### Widget 1: Pipeline Summary

| Metric | Source | Display |
|--------|--------|---------|
| Total pipeline value | SUM(opportunities.expected_value) WHERE status = open | Currency |
| Deal count | COUNT(opportunities) WHERE status = open | Number |
| Weighted value | SUM(value × stage_probability) | Currency |
| Stage distribution | GROUP BY stage | Mini bar chart |

- Click → navigates to `/pipeline`
- Auto-refresh: 2 minutes

### Widget 2: Revenue

| Metric | Source | Display |
|--------|--------|---------|
| Won revenue | SUM(actual_value) WHERE status = won AND closed_at in range | Currency |
| Target | `crm_workspace_config.monthly_target` | Currency |
| Achievement % | won / target × 100 | Progress bar |
| Deal count won | COUNT WHERE status = won | Number |
| Average deal size | AVG(actual_value) WHERE won | Currency |

- Click → navigates to `/reports/revenue`
- Auto-refresh: 5 minutes

### Widget 3: Conversations

| Metric | Source | Display |
|--------|--------|---------|
| Open conversations | COUNT WHERE status = open | Number |
| Unresponded | COUNT WHERE status = open AND awaiting_agent = true | Number (red if > threshold) |
| Average FRT | AVG(first_response_time_seconds) | Formatted duration |
| New today | COUNT WHERE created_at = today | Number |

- Click → navigates to `/inbox`
- Auto-refresh: 1 minute

### Widget 4: Sales Funnel

| Element | Display |
|---------|---------|
| Horizontal bar chart | One bar per stage, width proportional to count |
| Count per stage | Number at end of bar |
| Conversion rate | Bottom: overall conversion (won / total × 100) |
| Stage-to-stage conversion | Hover: shows % that moved from previous stage |

- Click stage bar → navigates to `/pipeline` filtered to that stage
- Auto-refresh: 5 minutes

### Widget 5: Team Activity

| Column | Source | Sort |
|--------|--------|------|
| Agent name | elauth | — |
| Conversations handled | COUNT(conversations WHERE agent = X) | Descending |
| Opportunities active | COUNT(opportunities WHERE agent = X AND status = open) | — |
| Average FRT | AVG(first_response_time_seconds) | Ascending (lower is better) |
| Messages sent | COUNT(messages WHERE sender = agent AND direction = outbound) | — |

- Click agent row → navigates to `/reports/agent-activity?agent=:id`
- Highlights: green for best performer, amber for below average
- Auto-refresh: 5 minutes

### Widget 6: SLA Compliance

| Metric | Display |
|--------|---------|
| FRT thresholds | % of conversations meeting each SLA tier |
| Response time (business hours) | % within configured thresholds |
| Status indicator | ✅ ≥ 90%, ⚠ 70–89%, 🔴 < 70% |

- SLA thresholds from `crm_workspace_config.sla_policies`
- Click → navigates to `/reports/frt`
- Auto-refresh: 5 minutes

### Widget 7: Win Rate Trend

| Element | Display |
|---------|---------|
| Line chart | Monthly win rate over last 6 months |
| Team average | Horizontal reference line |
| Data points | Hover shows: month, win rate %, won count, lost count |

- Click → navigates to `/reports/funnel`
- Auto-refresh: 10 minutes

### Widget 8: Alerts

System-generated alerts surfaced from various data sources:

| Alert Type | Condition | Source |
|------------|-----------|--------|
| Stuck deals | Opportunities in stage > threshold days | Pipeline aging |
| Overdue close | Expected close date passed | Opportunities |
| Agent inactivity | Agent below average new opportunities | Agent metrics |
| Overdue follow-ups | Follow-ups past due | Follow-ups |
| SLA breach | FRT exceeding SLA threshold | Conversation metrics |
| Unassigned conversations | Conversations without agent > threshold | Conversations |

- Each alert is clickable → navigates to relevant page
- Dismiss: per-alert, or "Dismiss All"
- Data: `GET /dashboard/alerts`
- Auto-refresh: 5 minutes

---

## Empty States

| Scenario | Display |
|----------|---------|
| New workspace (no data) | Welcome message with setup checklist links |
| No data for selected filters | "No data for the selected period" with suggestion to change filters |
| No alerts | "All clear — no alerts" with checkmark |

---

## State Management

| State | Source | Cache |
|-------|--------|-------|
| Pipeline summary | CRM API | React Query, 2min stale |
| Revenue | CRM API | React Query, 5min stale |
| Conversations | CRM API | React Query, 1min stale |
| Funnel | CRM API | React Query, 5min stale |
| Team activity | CRM API | React Query, 5min stale |
| SLA | CRM API | React Query, 5min stale |
| Win rate | CRM API | React Query, 10min stale |
| Alerts | CRM API | React Query, 5min stale |

Each widget fetches independently. Loading skeleton shown per widget while fetching. Error per widget does not block others.

---

## API Endpoints

| Widget | Method | Endpoint |
|--------|--------|----------|
| Pipeline summary | GET | `/dashboard/pipeline-summary?filters` |
| Revenue | GET | `/dashboard/revenue?filters` |
| Conversations | GET | `/dashboard/conversations?filters` |
| Sales funnel | GET | `/dashboard/funnel?filters` |
| Team activity | GET | `/dashboard/team-activity?filters` |
| SLA compliance | GET | `/dashboard/sla?filters` |
| Win rate trend | GET | `/dashboard/win-rate-trend?filters` |
| Alerts | GET | `/dashboard/alerts` |
| Dismiss alert | POST | `/dashboard/alerts/:id/dismiss` |

---

## Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| ≥1280px | 3-column grid, all widgets visible |
| 1024–1279px | 2-column grid |
| 768–1023px | 2-column grid, charts simplified |
| <768px | Single column stack, Team Activity becomes top-3 only |
