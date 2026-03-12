# Report Specifications

> Each report: purpose, data sources, filters, output format, and visualization.
> Reports are ported from Climate CRM's proven patterns, adapted for multi-tenant workspace isolation.

---

## Common Report Features

### Date Handling
All reports support date range selection:
- **Presets**: Today, Yesterday, This Week, Last Week, This Month, Last Month, Last 7 Days, Last 30 Days
- **Custom range**: Start date + End date picker
- All dates respect workspace timezone
- SLA-related metrics use business hours only (pause outside working hours)

### Role-Based Filtering
- **Agent**: Automatically sees only their own data. No agent filter shown.
- **Manager**: Sees all workspace data. Agent filter dropdown available (multi-select).
- **Admin**: Same as Manager.

### Export
All reports support Excel export:
1. Click "Export" → generates .xlsx file server-side
2. Returns file path → click "Download" → binary Excel stream
3. Multi-sheet workbooks for complex reports (summary + detail sheets)

### Standard Response Envelope

```json
{
  "success": true,
  "data": { "..." },
  "filters": {
    "start_date": "2026-03-01",
    "end_date": "2026-03-12",
    "agent_ids": [],
    "source_ids": []
  },
  "generated_at": "2026-03-12T10:30:00Z"
}
```

---

## 1. First Response Time (FRT) Report

### Purpose
Measures how quickly agents respond to customer messages for the first time. Key indicator of customer experience and agent responsiveness.

### Data Source
- `conversations` table: `first_response_time_seconds`, `agent_id`, `created_at`
- Calculated: time between first inbound message and first agent reply
- Only counts conversations where a customer message exists and agent responded

### Sub-Reports

#### FRT Per Agent (`/reports/frt/agents`)
| Column | Description |
|--------|-------------|
| Agent Name | Agent who handled the conversation |
| Total Conversations | Conversations assigned in period |
| With FRT | Conversations where agent responded |
| Without FRT | Conversations with no response yet |
| Avg FRT (seconds/minutes) | Average first response time |
| Min FRT | Fastest response |
| Max FRT | Slowest response |
| Daily Breakdown | Per-day drill-down (expandable rows) |

#### FRT Summary (`/reports/frt/summary`)
| Metric | Description |
|--------|-------------|
| Total Agents | Agents with conversations in period |
| Total Conversations | All conversations in period |
| Overall Avg FRT | Business-wide average |
| Fastest Agent | Agent with lowest avg FRT |
| Slowest Agent | Agent with highest avg FRT |
| SLA Compliance % | Conversations within FRT SLA target |

#### FRT Combined (`/reports/frt`)
Both agents + summary in single view. Agents table with summary cards above.

### Filters
- Date range (with presets)
- Agent (multi-select, manager only)
- Channel (WhatsApp, Voice, Email, All)
- Conversation type (Contact, Opportunity, All)

### Visualization
- Bar chart: Avg FRT per agent
- Line chart: Daily FRT trend
- Gauge: Overall FRT vs SLA target

---

## 2. Sales Funnel Report

### Purpose
Tracks conversation progression through pipeline stages. Shows where leads are converting or dropping off.

### Data Source
- `conversations` table: `stage_id`, `created_at`, `closed_at`
- `activities` table: stage change events with timestamps
- Three views of the same data:

#### Cohort View
Conversations **created** in the date range, tracked to their current stage.
"Of leads that came in March, where are they now?"

| Stage | Count | % of Total | Conversion from Previous |
|-------|-------|-----------|------------------------|
| New | 200 | 100% | — |
| Contacted | 150 | 75% | 75% |
| Qualified | 80 | 40% | 53% |
| Opportunity | 45 | 22.5% | 56% |
| Won | 20 | 10% | 44% |
| Lost | 15 | 7.5% | — |
| Unqualified | 40 | 20% | — |

#### Activity View
Stage transitions that **happened** in the date range, regardless of when conversation was created.
"What stage movements happened in March?"

| Transition | Count |
|-----------|-------|
| New → Contacted | 120 |
| Contacted → Qualified | 65 |
| Qualified → Opportunity | 30 |
| Opportunity → Won | 15 |
| Opportunity → Lost | 8 |
| * → Unqualified | 35 |

#### Current Status View
Snapshot of all open conversations as of now, grouped by stage.
"What does our pipeline look like right now?"

| Stage | Count | Total Value |
|-------|-------|-------------|
| New | 45 | — |
| Contacted | 30 | — |
| Qualified | 25 | ₹5,00,000 |
| Opportunity | 18 | ₹8,50,000 |

### Filters
- Date range, Agent, Source, Conversation type (Contact/Opportunity)
- View type: Cohort | Activity | Current Status

### Visualization
- Funnel chart (classic funnel shape showing drop-off)
- Stacked bar chart by agent or source

---

## 3. Aging Report

### Purpose
Identifies stale/stuck conversations by showing how long they've been in their current stage.

### Data Source
- `conversations` table: current stage, stage entry timestamp (from last stage change activity)
- Age calculated: now - last_stage_change_at

### Age Buckets
| Bucket | Range |
|--------|-------|
| Fresh | 0-2 days |
| Normal | 3-7 days |
| Aging | 8-14 days |
| Stale | 15-30 days |
| Critical | 30+ days |

### Views

#### By Stage (`/reports/aging?view=stage`)

| Stage | 0-2d | 3-7d | 8-14d | 15-30d | 30+d | Total |
|-------|------|------|-------|--------|------|-------|
| New | 20 | 10 | 5 | 2 | 1 | 38 |
| Contacted | 15 | 8 | 3 | 1 | 0 | 27 |
| Qualified | 10 | 5 | 4 | 2 | 1 | 22 |

#### By Source (`/reports/aging?view=source`)

| Source | 0-2d | 3-7d | 8-14d | 15-30d | 30+d | Total |
|--------|------|------|-------|--------|------|-------|
| WhatsApp | 25 | 12 | 6 | 3 | 1 | 47 |
| JustDial | 10 | 5 | 3 | 1 | 0 | 19 |
| Facebook | 10 | 6 | 3 | 1 | 1 | 21 |

Each cell is clickable → shows the actual conversations in that bucket.

#### By Agent
Nested within stage or source view — expand a row to see per-agent breakdown.

### Filters
- Conversation type (Contact/Opportunity)
- Agent, Source, Stage
- View mode: Stage | Source | Agent

### Visualization
- Heatmap: stages × age buckets (color intensity = count)
- Stacked bar chart by agent

---

## 4. Agent Activity Report

### Purpose
Measures agent productivity across all activity types: calls, messages, follow-ups.

### Data Source
- `conversation_messages` table: count by direction, agent, date
- `activities` table: calls (incoming/outgoing/missed), call duration
- `followups` table: created, completed counts

### Metrics Per Agent

| Metric | Description |
|--------|-------------|
| Incoming Calls Attempted | Total incoming call events |
| Incoming Calls Successful | Answered incoming calls |
| Incoming Calls Missed | Unanswered incoming calls |
| Outgoing Calls Attempted | Total outgoing call events |
| Outgoing Calls Successful | Connected outgoing calls |
| Outgoing Calls Missed | Failed/no-answer outgoing |
| Total Call Duration | Sum of all call durations (formatted: Xh Ym) |
| Messages Sent | Outbound messages across all channels |
| Follow-up Tasks Created | New follow-ups in period |
| Follow-up Tasks Completed | Completed follow-ups in period |
| Success Rate | (Successful calls / Total calls) × 100 |

### Summary (Top-Level)

```json
{
  "summary": {
    "active_users": 8,
    "incoming_attempted": 500,
    "incoming_successful": 400,
    "outgoing_attempted": 800,
    "outgoing_successful": 600,
    "total_call_duration_formatted": "42h 30m",
    "messages_sent": 1200,
    "followup_tasks_created": 350,
    "success_rate": 76.9
  },
  "users": [ ... per agent ... ],
  "daily_trend": [ ... per day ... ]
}
```

### Filters
- Date range, Agent

### Visualization
- Bar chart: calls per agent (stacked: incoming/outgoing)
- Line chart: daily activity trend
- Table: detailed per-agent breakdown

---

## 5. Outcome Report

### Purpose
Tracks opportunity-to-order conversion with breakdown by new vs. existing customers.

### Data Source
- `opportunities` table: outcome (won/lost), won_value, agent_id, source_id
- Cross-reference with accounts-api: person's order history to determine new/existing

### Metrics

| Metric | Description |
|--------|-------------|
| Total Opportunities | Opportunities closed in period |
| Opportunity Amount | Sum of expected values |
| Orders (Won) | Opportunities with outcome = won |
| Order Amount | Sum of won values |
| Conversion Rate | (Won / Total) × 100 |
| New Customer Orders | Won opportunities where contact had no prior orders |
| Existing Customer Orders | Won opportunities where contact had previous orders |

### Breakdowns
- **By Agent**: Each agent's conversion rate, new vs existing split
- **By Source**: Each lead source's conversion rate

### Filters
- Date range

### Visualization
- Donut chart: new vs existing customer split
- Bar chart: conversion rate by agent
- Bar chart: conversion rate by source

---

## 6. Revenue Contribution Report

### Purpose
Revenue attribution — which agents and sources generate the most revenue.

### Data Source
- `opportunities` table: won_value, agent_id, source_id
- Same new/existing customer split as Outcome report

### Metrics

| Metric | Description |
|--------|-------------|
| Total Orders | Won opportunities in period |
| Total Revenue | Sum of won_value |
| Avg Order Value | Revenue / Orders |
| Revenue by Agent | Per-agent revenue + contribution percentage |
| Revenue by Source | Per-source revenue + contribution percentage |

### Each Agent/Source Row

```json
{
  "user_id": 5,
  "creator_name": "Priya",
  "orders": 50,
  "order_amount": 200000,
  "avg_order_value": 4000,
  "contribution_pct": 23.5,
  "new_customer": { "orders": 30, "amount": 120000 },
  "existing_customer": { "orders": 20, "amount": 80000 }
}
```

### Filters
- Date range

### Visualization
- Pie chart: revenue contribution by agent
- Pie chart: revenue contribution by source
- Bar chart: avg order value comparison

---

## 7. Unqualified Analysis Report

### Purpose
Analyzes why leads are being marked as unqualified — identifies patterns by reason, agent, and source.

### Data Source
- `conversations` table: where stage = unqualified terminal stage
- `activities` table: disposition reason from stage change activity
- Grouped by disposition reason

### Disposition Reasons (Workspace-Configurable)

Default reasons: Not Interested, Budget Too Low, Wrong Product Category, Competitor Chosen, Duplicate, Spam/Irrelevant, Location Not Serviceable, Not Decision Maker, No Response, Already a Customer, Under Maintenance, Wrong Number, Test/Internal, Language Barrier, Not Available, Incorrect Information, Will Call Back, Other

### Output Structure

```json
{
  "data": {
    "contact": [
      { "reason": "not_interested", "label": "Not Interested", "count": 45, "percentage": 22.5 }
    ],
    "opportunity": [ ... ],
    "combined": [ ... ],
    "summary": {
      "total_contact": 200,
      "total_opportunity": 80,
      "total": 280
    },
    "agent_wise": [
      { "user_id": 5, "agent_name": "Priya", "total": 35, "reasons": { "not_interested": 10, ... } }
    ],
    "source_wise": [
      { "source_id": 1, "source_name": "WhatsApp", "total": 60, "reasons": { ... } }
    ]
  }
}
```

### Filters
- Date range

### Visualization
- Horizontal bar chart: disposition reasons ranked by count
- Stacked bar chart: reasons by agent
- Table: detailed breakdown

---

## 8. Conversation Trend Report

### Purpose
Shows daily/weekly trends in conversation stage transitions over time. Identifies patterns, seasonality, and the effect of campaigns.

### Data Source
- `activities` table: stage change events with timestamps
- Grouped by day or week

### Granularity
- **Daily**: Each row = one day
- **Weekly**: Each row = one week (Mon-Sun)

### Output

```json
{
  "data": {
    "trend": [
      {
        "period": "2026-03-01",
        "new": 25,
        "contacted": 20,
        "qualified": 10,
        "opportunity": 5,
        "won": 3,
        "lost": 2,
        "unqualified": 8
      }
    ],
    "totals": { "new": 200, "contacted": 150, ... }
  }
}
```

### Enhanced Trend (post-launch)
- Agent breakdown per period
- Source breakdown per period
- Velocity metrics: avg days per stage transition
- Loss analysis: lost reason breakdown per period

### Filters
- Date range, Granularity (daily/weekly), Conversation type (Contact/Opportunity)

### Visualization
- Multi-line chart: each stage as a separate line over time
- Area chart: stacked stages showing volume over time

---

## 9. Report Summary Table

| Report | Endpoint | Key Metric | Export |
|--------|----------|-----------|--------|
| FRT Agents | GET /reports/frt/agents | Avg first response time per agent | Excel |
| FRT Summary | GET /reports/frt/summary | Overall FRT, best/worst agent | Excel |
| Sales Funnel | POST /reports/funnel | Stage-by-stage conversion rates | Excel |
| Aging | GET /reports/aging | Open conversations by age bucket | Excel |
| Agent Activity | POST /reports/activity | Calls, messages, follow-ups per agent | Excel |
| Outcome | POST /reports/outcome | Opportunity → order conversion rate | Excel |
| Revenue | POST /reports/revenue | Revenue by agent and source | Excel |
| Unqualified | POST /reports/unqualified | Disposition reasons breakdown | Excel |
| Trend | POST /reports/trend | Daily/weekly stage transition volumes | Excel |

---

## 10. Dashboard Widgets (Manager Home)

The manager dashboard composes data from multiple reports into widget cards:

| Widget | Source Report | Display |
|--------|-------------|---------|
| Pipeline Value | Pipeline data | Total value, weighted value, deal count |
| Win Rate | Outcome | Conversion % with trend arrow |
| FRT Gauge | FRT Summary | Avg FRT vs SLA target |
| Team Activity Today | Agent Activity (today preset) | Calls + messages + follow-ups |
| Conversion Funnel | Sales Funnel (current status) | Mini funnel visualization |
| SLA Compliance | FRT + Conversation data | % within SLA, breaches count |
| Open Conversations | Conversation counts | By status: open, pending, unassigned |
| Top Agent | Agent Activity + Outcome | Highest performing agent this period |

Dashboard date range defaults to "This Month" with period selector.
