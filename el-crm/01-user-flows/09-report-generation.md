# Report Generation

> Role: Manager, Admin (Agent: limited to own data reports)
> Trigger: Manager navigates to Reports
> Primary screen: Reports (/reports, /reports/:type)

---

## Flow Summary

Manager selects a report from the reports index, applies date range and filters, views the visualization, and optionally exports to Excel. All reports use the same interaction pattern.

---

## Reports Index Page

```
/reports

┌──────────────────────────────────────────────────────────────────┐
│ Reports                                                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ CRM Performance                                                  │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│ │ 📊 FRT       │ │ 📊 Funnel    │ │ 📊 Aging     │             │
│ │ First        │ │ Sales        │ │ Stale        │             │
│ │ Response     │ │ Conversion   │ │ Conversations│             │
│ │ Time         │ │ Funnel       │ │              │             │
│ └──────────────┘ └──────────────┘ └──────────────┘             │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│ │ 📊 Activity  │ │ 📊 Trend     │ │ 📊 Unqualified│            │
│ │ Agent        │ │ Conversation │ │ Analysis     │             │
│ │ Activity     │ │ Trends       │ │              │             │
│ └──────────────┘ └──────────────┘ └──────────────┘             │
│                                                                  │
│ Revenue & Outcomes                                               │
│ ┌──────────────┐ ┌──────────────┐                               │
│ │ 📊 Outcome   │ │ 📊 Revenue   │                               │
│ │ Opportunity  │ │ Revenue      │                               │
│ │ Conversion   │ │ Contribution │                               │
│ └──────────────┘ └──────────────┘                               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

Each card shows: icon, report name, brief description
Click → navigates to /reports/:type
```

---

## Standard Report Page Layout

Every report page follows this pattern:

```
┌──────────────────────────────────────────────────────────────────┐
│ ← Reports    FRT Report                          [⬇ Export]     │
├──────────────────────────────────────────────────────────────────┤
│ [Today] [This Week] [This Month] [Last 30 Days] [Custom ▾]     │
│ Agent: [All ▾]   Source: [All ▾]   Channel: [All ▾]  [Apply]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ Summary Cards (key metrics)                                  ││
│ │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        ││
│ │ │ Avg FRT  │ │ Total    │ │ Best     │ │ SLA      │        ││
│ │ │ 5.2 min  │ │ Convos   │ │ Agent    │ │ Compliance│       ││
│ │ │          │ │ 950      │ │ Priya    │ │ 85%      │        ││
│ │ └──────────┘ └──────────┘ └──────────┘ └──────────┘        ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ Visualization (chart)                                        ││
│ │                                                              ││
│ │ [Bar chart / Line chart / Funnel / Heatmap]                  ││
│ │                                                              ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ Data Table (detailed breakdown)                              ││
│ │                                                              ││
│ │ Agent   | Total | With FRT | Avg FRT | Min | Max           ││
│ │ Priya   | 120   | 105      | 3.2 min | 0   | 15 min       ││
│ │ Ravi    | 95    | 80       | 6.8 min | 1m  | 30 min       ││
│ │ Ankit   | 110   | 92       | 5.1 min | 0   | 20 min       ││
│ │ ...                                                          ││
│ │                                                              ││
│ │ Expandable rows → daily breakdown per agent                  ││
│ └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Report Flow

```
1. Manager clicks "FRT Report" card on reports index
   → Navigate to /reports/frt
   → Default: This Month, All Agents

2. Page loads:
   → API: GET /reports/frt?preset=this_month
   → Summary cards populate
   → Chart renders (bar chart: avg FRT per agent)
   → Data table loads with per-agent breakdown

3. Manager adjusts filters:
   → Changes date to "Last 7 Days"
   → Selects Agent: Priya, Ravi
   → Clicks [Apply]
   → API: GET /reports/frt?start_date=2026-03-05&end_date=2026-03-12&agent_ids=5,8
   → All widgets refresh

4. Manager drills down:
   → Clicks expand arrow on "Ravi" row
   → Daily breakdown appears: date, conversations, avg FRT per day
   → Identifies: Ravi's FRT spiked on March 8 (was on leave, conversations queued)

5. Manager exports:
   → Clicks [⬇ Export]
   → API: POST /reportexports/frtSummary { start_date, end_date, agent_ids }
   → Returns: { file: "reports/frt_20260312.xlsx", file_name: "FRT Report..." }
   → Auto-download: POST /reportexports/download { file: "..." }
   → Excel file downloads with Summary + Per-Agent + Daily sheets
```

---

## Report-Specific Views

### FRT Report
- **Summary**: Avg FRT, total conversations, best/worst agent, SLA compliance
- **Chart**: Bar chart (avg FRT per agent), Line chart (daily FRT trend)
- **Table**: Per-agent with expandable daily breakdown

### Sales Funnel
- **View toggle**: Cohort | Activity | Current Status
- **Chart**: Funnel visualization showing stage-by-stage conversion
- **Table**: Stage | Count | % of Total | Conversion from Previous

### Aging Report
- **View toggle**: By Stage | By Source | By Agent
- **Chart**: Heatmap (stages × age buckets, color = count)
- **Table**: Age buckets as columns (0-2d, 3-7d, 8-14d, 15-30d, 30+d)
- **Clickable cells**: Click count → shows actual conversations in that bucket

### Agent Activity
- **Summary**: Total calls, messages, follow-ups, success rate
- **Chart**: Stacked bar (calls per agent), Line (daily trend)
- **Table**: Per-agent: incoming/outgoing calls, messages, follow-ups, duration

### Outcome Report
- **Summary**: Opportunities, orders, conversion rate, new vs existing split
- **Chart**: Donut (new vs existing), Bar (conversion by agent)
- **Table**: Per-agent and per-source conversion breakdown

### Revenue Contribution
- **Summary**: Total revenue, avg order value, new vs existing split
- **Chart**: Pie (contribution by agent), Pie (contribution by source)
- **Table**: Per-agent/source: orders, amount, contribution %, avg order value

### Unqualified Analysis
- **Summary**: Total unqualified (contact + opportunity), top reason
- **Chart**: Horizontal bar (reasons ranked by count)
- **Table**: Reasons with count + percentage, agent-wise breakdown, source-wise breakdown

### Conversation Trend
- **Granularity**: Daily | Weekly toggle
- **Chart**: Multi-line (each stage as line) or stacked area
- **Table**: Period | New | Contacted | Qualified | Opportunity | Won | Lost | Unqualified

---

## Agent Report Access

Agents can access limited reports showing only their own data:
- "My Performance" view (FRT, activity, pipeline)
- No agent filter (hardcoded to own person_id)
- Accessed via: Sidebar → Reports (shows limited set)

---

## Export Details

Excel exports generate multi-sheet workbooks:

| Report | Sheet 1 | Sheet 2 | Sheet 3 |
|--------|---------|---------|---------|
| FRT | Summary | Per Agent | Daily Breakdown |
| Funnel | Summary | Stage Breakdown | Per Agent |
| Aging | By Stage | By Source | By Agent |
| Activity | Summary | Per Agent | Daily Trend |
| Outcome | Summary | By Agent | By Source |
| Revenue | Summary | By Agent | By Source |
| Unqualified | Summary | By Reason | By Agent |
| Trend | Summary | Daily/Weekly Data | — |
