# Reporting & Analytics Module

> Module: `climate/modules/reporting`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [CRM Reports](#crm-reports)
4. [Order Reports](#order-reports)
5. [Dashboards](#dashboards)
6. [Export System](#export-system)
7. [Report Models Detail](#report-models-detail)
8. [Frontend Module](#frontend-module)
9. [Cross-References](#cross-references)

---

## Overview

The reporting module provides comprehensive analytics across CRM operations, sales pipeline health, agent performance, and order metrics. It is organized around four backend controllers and seven dedicated report models, all accessible through dashboards and an Excel/CSV export system.

**Controllers**:
| Controller | Endpoints | Purpose |
|------------|-----------|---------|
| `ConversationReports` | 13 | CRM analytics (funnel, FRT, aging, trends, outcomes) |
| `Reports` | 8 | Order reports, weight/grade summaries, contact exports |
| `OrderReports` | 2 | Grade-wise sales reports |
| `ReportExports` | 15 | Excel export for all CRM reports |
| `DashBoard` | 7 | Dashboard summary APIs |

**Report Models**:
| Model | Data Source | Purpose |
|-------|-----------|---------|
| `AgentFRTReportModel` | `crm_agent_frt_daily_summary` + live `tbl_open_conversations` | First Response Time |
| `ConversationFunnelModel` | `crm_conversation_cohort_summary`, `crm_conversation_activity_summary`, `crm_conversation_stage_summary` | Sales funnel (3 views) |
| `ConversationAgingModel` | `crm_conversation_aging_snapshot` + live `tbl_open_conversations` | Conversation aging |
| `UnqualifiedAnalysisModel` | `crm_unqualified_summary` | Disposition analysis |
| `OutcomeReportModel` | `crm_outcome_agent_summary` + live `tbl_orders`/`tbl_opportunities` | Opportunity → Order conversion |
| `RevenueContributionModel` | `crm_revenue_agent_summary` + live `tbl_orders` | Revenue attribution |
| `AgentActivityReportModel` | `crm_agent_activity_summary` | Agent calls, messages, tasks |
| `ReportExportModel` | Loads other models + `XlsxWriter` | Excel file generation |

---

## Architecture

### Hybrid Data Strategy

Reports use a **hybrid approach** combining pre-aggregated summary tables (populated by MySQL triggers) for historical data with real-time queries for today's data:

```
Historical (yesterday and before)     Today (real-time)
┌─────────────────────────┐          ┌─────────────────────────┐
│ crm_*_summary tables    │          │ tbl_open_conversations  │
│ (trigger-populated)     │          │ tbl_orders              │
│                         │          │ tbl_opportunities       │
│ Pre-aggregated daily    │          │ Live queries with same  │
│ snapshots               │          │ aggregation logic       │
└─────────────────────────┘          └─────────────────────────┘
         │                                      │
         └──────────────┬───────────────────────┘
                        ▼
              Merged & aggregated
              in report model
```

### Role-Based Data Filtering

All CRM report endpoints apply automatic user filtering via `applyUserFiltering()`:

```php
private function applyUserFiltering(&$filters)
{
    $CI = &get_instance();
    $authData = $CI->AuthData ?? [];
    // Sales agents (role_id=4) only see their own data
    if (isset($authData['role_id']) && $authData['role_id'] == 4) {
        if (!isset($filters['user_id']) && !isset($filters['agent_id'])) {
            $filters['user_id'] = $authData['user_id'] ?? null;
        }
    }
    return $filters;
}
```

### Date Presets

All reports support the `preset` parameter for quick date ranges:

| Preset | Start Date | End Date |
|--------|-----------|----------|
| `today` | Today | Today |
| `yesterday` | Yesterday | Yesterday |
| `this_week` | Monday this week | Today |
| `last_week` | Monday last week | Sunday last week |
| `this_month` | 1st of month | Today |
| `last_month` | 1st of last month | Last day of last month |
| `last_7_days` | 6 days ago | Today |
| `last_30_days` | 29 days ago | Today |

### Conversation Types

Reports that support conversation type filtering accept:
- `contact` — Lead/contact conversations
- `opportunity` — Opportunity/deal conversations
- `null` — All types combined

---

## CRM Reports

### First Response Time (FRT)

Measures how quickly agents respond to new conversations. Uses a hybrid data source: `crm_agent_frt_daily_summary` for historical dates, live `tbl_open_conversations` for today.

**Key Detail**: FRT = 0 is valid — represents an instant response where the agent responded after work hours (0 working seconds elapsed). The `attempt_time` column stores adjusted working seconds calculated by the `fn_calculate_working_seconds` stored function via a trigger.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /conversationreports/frt_agents` | `frt_agents()` | Per-agent FRT breakdown with daily data |
| `GET /conversationreports/frt_summary` | `frt_summary()` | Overall business FRT summary |
| `GET /conversationreports/frt_report` | `frt_report()` | Combined agents + summary in single request |

**Capabilities**: `crm_reports.view_frt_summary`, `crm_reports.view`

**Model**: `AgentFRTReportModel`

**Response structure** (`frt_report`):
```json
{
  "agents": [
    {
      "user_id": 5,
      "agent_name": "John Doe",
      "total_conversations": 120,
      "conversations_with_frt": 105,
      "conversations_without_frt": 15,
      "avg_frt_seconds": 342,
      "avg_frt_minutes": 5.7,
      "min_frt_seconds": 0,
      "max_frt_seconds": 3600,
      "days": [
        { "date": "2026-03-01", "conversations": 10, "conversations_with_frt": 8, "avg_frt_seconds": 300 }
      ]
    }
  ],
  "summary": {
    "total_users": 8,
    "total_conversations": 950,
    "conversations_with_frt": 820,
    "conversations_without_frt": 130,
    "overall_avg_frt_seconds": 420,
    "overall_avg_frt_minutes": 7.0,
    "fastest_user": { "..." },
    "slowest_user": { "..." }
  }
}
```

**Cron**: `calculateDailySummary($date)` — runs daily, inserts into `crm_agent_frt_daily_summary` with `ON DUPLICATE KEY UPDATE`. Aggregation uses weighted averages (weighted by `conversations_with_frt`).

---

### Conversation Funnel

Visualizes lead progression through conversation stages with three distinct views.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /conversationreports/funnel_report` | `funnel_report()` | Funnel data with 3 views |

**Capabilities**: `crm_reports.view_conversation_funnel`, `crm_reports.view`

**Model**: `ConversationFunnelModel`

**Three Views**:

| View | Summary Table | What It Shows |
|------|--------------|---------------|
| **Cohort** | `crm_conversation_cohort_summary` | Of conversations created in date range, how many reached each stage |
| **Activity** | `crm_conversation_activity_summary` | How many stage transitions happened each day |
| **Current Status** | `crm_conversation_stage_summary` | Where conversations are NOW (current stage distribution) |

**Request body**:
```json
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-11",
  "conversation_type": "contact"
}
```

**Contact stages**: new → attempted → contacted → nurturing → qualified → unqualified
**Opportunity stages**: new → attempted → contacted → won → lost

---

### Conversation Trend

Time-series trend data for conversation stage transitions.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /conversationreports/trend_report` | `trend_report()` | Daily/weekly trend lines |
| `POST /conversationreports/enhanced_trend_report` | `enhanced_trend_report()` | Trend + agent breakdown, source breakdown, velocity, loss analysis |

**Capabilities**: `crm_reports.view_trend_report`, `crm_reports.view`

**Model**: `ConversationFunnelModel` (`getTrendData()`, `getEnhancedTrendData()`)

**Request body** (`trend_report`):
```json
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-11",
  "granularity": "daily",
  "conversation_type": "contact"
}
```

**Granularity options**: `daily`, `weekly`

---

### Source Breakdown

Per-source analytics showing how each lead source performs through the funnel.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /conversationreports/source_breakdown` | `source_breakdown()` | Source-wise funnel metrics |

**Capabilities**: `crm_reports.view_source_breakdown`, `crm_reports.view`

**Model**: `ConversationFunnelModel` (`getSourceBreakdownWithViews()`)

**Contact metrics per source**: total conversations, stage counts, profiled (accounts created), opportunities created
**Opportunity metrics per source**: total, stage counts, orders created, order value, pipeline value

---

### Conversation Aging

Shows how long conversations remain open, grouped by stage and age bucket.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /conversationreports/aging_report` | `aging_report()` | Aging by stage |
| `GET /conversationreports/aging_by_source` | `aging_by_source()` | Aging by source with agent breakdown |

**Capabilities**: `crm_reports.view_contact_aging`, `crm_reports.view_opportunity_aging`, `crm_reports.view`

**Model**: `ConversationAgingModel`

**Age Buckets**:
| Bucket | Description |
|--------|-------------|
| 0-2 days | Fresh |
| 3-7 days | Recent |
| 8-14 days | Moderate |
| 15-30 days | Aging |
| 30+ days | Stale/Critical |

**Two age metrics**:
- **Conversation age**: Time since `allocated_at` (overall age)
- **Time-in-stage**: Time since last stage transition

**Contact stages tracked**: new, attempted, contacted, nurturing (excludes converted/qualified)
**Opportunity stages tracked**: new, attempted, contacted

**Cron**: `calculateDailySnapshot()` — creates periodic aging snapshots for trend analysis in `crm_conversation_aging_snapshot`.

---

### Unqualified Analysis

Analyzes patterns in disqualified conversations by disposition reason to identify improvement areas.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /conversationreports/unqualified_analysis` | `unqualified_analysis()` | Disposition reason analysis |

**Capabilities**: `crm_reports.view_contact_unqualified`, `crm_reports.view_opportunity_unqualified`, `crm_reports.view`

**Model**: `UnqualifiedAnalysisModel`

**Data source**: `crm_unqualified_summary` (trigger-populated)

**Disposition reasons**:
| Key | Label |
|-----|-------|
| `rnr1` / `rnr2` / `rnr3` | RNR Attempt 1/2/3 |
| `not_interested` | Not Interested |
| `price_too_high` | Price Too High |
| `wrong_timing` | Wrong Timing |
| `need_approval` | Need Approval |
| `competitor_chosen` | Competitor Chosen |
| `budget_issues` | Budget Issues |
| `decision_maker_unavailable` | Decision Maker Unavailable |
| `need_discount` / `credit_needed` | Need Discount / Credit Needed |
| `need_more_time` | Need More Time |
| `farmer` / `job` | Farmer / Job |
| `customer_need_cod` | Customer Need COD |
| `non_contact` / `invalid` | Non-Contactable / Invalid Contact |
| `other` | Other |

**Response structure**:
```json
{
  "contact": [{ "reason": "not_interested", "label": "Not Interested", "count": 45, "percentage": 22.5 }],
  "opportunity": [...],
  "combined": [...],
  "summary": { "total_contact": 200, "total_opportunity": 80, "total": 280 },
  "agent_wise": [
    {
      "user_id": 5, "agent_name": "John",
      "contact": { "total": 30, "reasons": [...] },
      "opportunity": { "total": 12, "reasons": [...] }
    }
  ],
  "source_wise": [
    {
      "source_id": 1, "source_name": "WhatsApp",
      "contact": { "total": 50, "reasons": [...] },
      "opportunity": { "total": 20, "reasons": [...] }
    }
  ]
}
```

---

### Outcome Report

Tracks opportunity-to-order conversion with user and source attribution. Distinguishes between new and existing customers.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /conversationreports/outcome_report` | `outcome_report()` | Conversion analysis |

**Capabilities**: `crm_reports.view_outcome`, `crm_reports.view`

**Model**: `OutcomeReportModel`

**Data sources**:
- Summary: `crm_outcome_agent_summary` (trigger-populated)
- Customer classification: Live query on `tbl_orders` + `tbl_opportunities` + `temp_tbl_accounts`

**Customer classification**:
- **New customer**: `first_order_date IS NULL OR first_order_date >= date_range_start`
- **Existing customer**: `first_order_date < date_range_start`

**Response structure**:
```json
{
  "summary": {
    "opportunities": 150,
    "opportunity_amount": 500000,
    "orders": 45,
    "order_amount": 180000,
    "conversion_rate": 30.0,
    "new_customer": { "orders": 30, "amount": 120000, "percentage": 66.7 },
    "existing_customer": { "orders": 15, "amount": 60000, "percentage": 33.3 }
  },
  "users": [
    { "user_id": 5, "creator_name": "John", "opportunities": 40, "orders": 15, "conversion_rate": 37.5 }
  ],
  "sources": [
    { "source_id": 1, "source_name": "WhatsApp", "opportunities": 60, "orders": 20, "conversion_rate": 33.3 }
  ]
}
```

---

### Revenue Contribution

Revenue attribution by user and source with new vs. existing customer breakdown.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /conversationreports/revenue_contribution` | `revenue_contribution()` | Revenue analytics |

**Capabilities**: `crm_reports.view_revenue_contribution`, `crm_reports.view`

**Model**: `RevenueContributionModel`

**Data sources**:
- Summary: `crm_revenue_agent_summary` (trigger-populated)
- Customer classification: Live query on `tbl_orders` + `temp_tbl_accounts`

**Response structure**:
```json
{
  "summary": {
    "orders": 200,
    "order_amount": 850000,
    "avg_order_value": 4250,
    "new_customer": {
      "orders": 120, "amount": 480000, "percentage": 60.0,
      "amount_percentage": 56.5, "avg_order": 4000
    },
    "existing_customer": {
      "orders": 80, "amount": 370000, "percentage": 40.0,
      "amount_percentage": 43.5, "avg_order": 4625
    }
  },
  "users": [
    { "user_id": 5, "creator_name": "John", "orders": 50, "order_amount": 200000, "avg_order": 4000, "contribution_pct": 23.5 }
  ],
  "sources": [
    { "source_id": 1, "source_name": "WhatsApp", "orders": 80, "order_amount": 320000, "contribution_pct": 37.6 }
  ]
}
```

---

### Agent Activity

Per-agent performance tracking: calls (incoming/outgoing with outcome details), messages sent, and follow-up tasks created.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /conversationreports/agent_activity` | `agent_activity()` | Agent performance metrics |

**Capabilities**: `crm_reports.view_agent_activity`, `crm_reports.view`

**Model**: `AgentActivityReportModel`

**Data source**: `crm_agent_activity_summary` (trigger-populated by `trg_agent_activity_call_insert`, `trg_agent_activity_message_insert`, `trg_agent_activity_followup_insert`)

**Metrics tracked**:

| Category | Metrics |
|----------|---------|
| Incoming Calls | attempted, successful, missed, missed_by_agent |
| Outgoing Calls | attempted, successful, missed, missed_by_agent, missed_by_customer, errors |
| Duration | total_call_duration_seconds, total_ring_duration_seconds |
| Other | messages_sent (sender='admin'), followup_tasks_created |
| Calculated | success_rate, avg_call_duration, per-user averages |

**Response structure**:
```json
{
  "summary": {
    "incoming_attempted": 500, "incoming_successful": 400, "incoming_missed": 100,
    "outgoing_attempted": 800, "outgoing_successful": 600, "outgoing_missed": 200,
    "total_call_duration_seconds": 36000, "total_call_duration_formatted": "10h 0m",
    "avg_call_duration_formatted": "36s",
    "messages_sent": 1200, "followup_tasks_created": 350,
    "active_users": 8, "success_rate": 76.9
  },
  "users": [
    {
      "user_id": 5, "user_name": "John",
      "incoming_successful": 50, "outgoing_successful": 80,
      "total_call_duration_formatted": "1h 30m",
      "messages_sent": 150, "followup_tasks_created": 45,
      "calls_pct": 13.0, "success_rate": 81.3
    }
  ],
  "daily_trend": [
    { "summary_date": "2026-03-01", "total_successful": 120, "messages_sent": 80 }
  ]
}
```

---

## Order Reports

### Reports Controller

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /reports/weightProjection` | `weightProjection()` | Weight-wise order projection |
| `GET /reports/gradewiseSummary` | `gradewiseSummary()` | Grade-wise order summary |
| `POST /reports/downloadExcel` | `downloadExcel()` | Download report as Excel |
| `POST /reports/export` | `export()` | Generic report export |
| `GET /reports/getCompanyGodowns` | `getCompanyGodowns()` | Warehouse/godown list |
| `POST /reports/getDailyConfirmedOrders` | `getDailyConfirmedOrders()` | Daily confirmed orders summary |
| `POST /reports/dailyConfirmedOrdersExportExcel` | `dailyConfirmedOrdersExportExcel()` | Export daily orders to Excel |
| `POST /reports/downloadContactsList` | `downloadContactsList()` | Export filtered contacts list |

### OrderReports Controller

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /orderreports/gradeSalesReport` | `gradeSalesReport()` | Grade-wise sales analytics |
| `POST /orderreports/downloadGradeSalesReport` | `downloadGradeSalesReport()` | Export grade sales to Excel |

---

## Dashboards

### DashBoard Controller

| Method | Route | Purpose |
|--------|-------|---------|
| `data()` | `GET /dashboard/data` | Main dashboard data |
| `getContacts()` | `GET /dashboard/getContacts` | Contact/conversation metrics |
| `getPayments()` | `GET /dashboard/getPayments` | Payment overview |
| `getSummary()` | `GET /dashboard/getSummary` | Combined summary data |
| `getSales()` | `GET /dashboard/getSales` | Sales/revenue metrics |
| `agentDashBoard()` | `GET /dashboard/agentDashBoard` | Agent-specific dashboard (role_id=4) |
| `adminDashBoard()` | `GET /dashboard/adminDashBoard` | Admin dashboard (role_id=9) |

### Dashboard Types

| Dashboard | URL | Role | Content |
|-----------|-----|------|---------|
| Main | `/dashboard` | All | Active conversations, order summary, revenue charts |
| Agent | `/agentdashboard` | role_id=4 | My conversations, pending follow-ups, my orders, my metrics |
| Admin | `/admindashboard` | role_id=9 | Team overview, pipeline health, revenue targets, agent comparison |

---

## Export System

### ReportExports Controller

Two-step process: (1) generate Excel file via report model, (2) download via `download()` endpoint.

**Library**: `XlsxWriter` — supports multiple sheets per workbook, formatted headers, typed columns (string, integer, currency), configurable column widths.

| Endpoint | Method | Source Model |
|----------|--------|-------------|
| `POST /reportexports/outcomeReport` | `outcomeReport()` | `OutcomeReportModel` |
| `POST /reportexports/revenueContribution` | `revenueContribution()` | `RevenueContributionModel` |
| `POST /reportexports/agentActivity` | `agentActivity()` | `AgentActivityReportModel` |
| `POST /reportexports/frtSummary` | `frtSummary()` | `AgentFRTReportModel` |
| `POST /reportexports/contactConversations` | `contactConversations()` | `ConversationFunnelModel` (contact) |
| `POST /reportexports/contactSourceBreakdown` | `contactSourceBreakdown()` | `ConversationFunnelModel` (contact) |
| `POST /reportexports/contactAging` | `contactAging()` | `ConversationAgingModel` (contact) |
| `POST /reportexports/contactUnqualified` | `contactUnqualified()` | `UnqualifiedAnalysisModel` (contact) |
| `POST /reportexports/opportunityConversations` | `opportunityConversations()` | `ConversationFunnelModel` (opportunity) |
| `POST /reportexports/opportunitySourceBreakdown` | `opportunitySourceBreakdown()` | `ConversationFunnelModel` (opportunity) |
| `POST /reportexports/opportunityAging` | `opportunityAging()` | `ConversationAgingModel` (opportunity) |
| `POST /reportexports/opportunityUnqualified` | `opportunityUnqualified()` | `UnqualifiedAnalysisModel` (opportunity) |
| `POST /reportexports/conversationTrend` | `conversationTrend()` | `ConversationFunnelModel` |
| `POST /reportexports/callLogs` | `callLogs()` | Direct query |
| `POST /reportexports/download` | `download()` | File download (streams Excel file) |

**Capability**: `crm_reports.view` (all export endpoints), `user` (callLogs)

**Export request body**:
```json
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-11",
  "view_type": "cohort"
}
```

**Export response**:
```json
{
  "success": true,
  "file": "reports/outcome_report_20260311_143022.xlsx",
  "file_name": "Outcome Report 2026-03-01 to 2026-03-11.xlsx"
}
```

**Download endpoint** reads file from `FCPATH . $filePath` and streams with content type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.

### ReportExportModel

The `ReportExportModel` acts as an orchestrator — each export method:
1. Loads the relevant report model
2. Calls `getXxxReport()` to fetch data
3. Transforms data into multi-sheet Excel format
4. Uses `XlsxWriter` to generate the `.xlsx` file
5. Returns file path for download

**Excel sheets per export**:

| Export | Sheets |
|--------|--------|
| Outcome Report | Summary, By User, By Source |
| Revenue Contribution | Summary, By User, By Source |
| Agent Activity | Summary, By User |
| FRT Summary | Agent FRT Summary |
| Funnel Report | Agent Summary (cohort/activity/current) |
| Source Breakdown | Source Breakdown |
| Aging Report | Aging by Stage / Aging by Agent |
| Unqualified Analysis | Summary, By Agent, By Source |
| Conversation Trend | Daily Trend |
| Call Logs | Call Logs |

---

## Report Models Detail

### Data Source Summary

All `crm_*` summary tables are populated by MySQL triggers on the source tables. See `03-database-design/triggers-and-functions.md` for trigger details.

| Summary Table | Populated By | Used By |
|--------------|-------------|---------|
| `crm_agent_frt_daily_summary` | Cron (`calculateDailySummary`) | `AgentFRTReportModel` |
| `crm_conversation_cohort_summary` | Triggers on `tbl_open_conversations` | `ConversationFunnelModel` |
| `crm_conversation_activity_summary` | Triggers on `tbl_open_conversations` | `ConversationFunnelModel` |
| `crm_conversation_stage_summary` | Triggers on `tbl_open_conversations` | `ConversationFunnelModel` |
| `crm_conversation_aging_snapshot` | Cron (`calculateDailySnapshot`) | `ConversationAgingModel` |
| `crm_unqualified_summary` | Triggers on `tbl_open_conversations` | `UnqualifiedAnalysisModel` |
| `crm_outcome_agent_summary` | Triggers on `tbl_opportunities`/`tbl_orders` | `OutcomeReportModel` |
| `crm_revenue_agent_summary` | Triggers on `tbl_orders` | `RevenueContributionModel` |
| `crm_agent_activity_summary` | Triggers on call logs, messages, follow-ups | `AgentActivityReportModel` |

### Cron Jobs

| Cron Method | Schedule | Target Table |
|-------------|----------|-------------|
| `AgentFRTReportModel::calculateDailySummary()` | Daily | `crm_agent_frt_daily_summary` |
| `ConversationAgingModel::calculateDailySnapshot()` | Daily | `crm_conversation_aging_snapshot` |

---

## Frontend Module

### CRM Reports Module (`views/crm-reports/`)

| Component | Report | Endpoints Used |
|-----------|--------|---------------|
| FRT Report | First response time | `frt_report` |
| Funnel Report | Sales funnel (3 views) | `funnel_report` |
| Aging Report | Conversation aging | `aging_report`, `aging_by_source` |
| Unqualified Report | Disposition analysis | `unqualified_analysis` |
| Outcome Report | Win/loss tracking | `outcome_report` |
| Revenue Report | Revenue attribution | `revenue_contribution` |
| Agent Activity | Agent performance | `agent_activity` |
| Trend Report | Time-series trends | `trend_report`, `enhanced_trend_report` |
| Source Breakdown | Per-source analytics | `source_breakdown` |

### Charting Libraries

- **Chart.js / ng2-charts**: Bar, line, pie, doughnut charts
- **ngx-echarts / ECharts**: Advanced visualizations, geographical maps

### Common Filter Controls

All report components share: date range picker (with presets), agent selector (multi-select), lead source filter, conversation type toggle (contact/opportunity).

---

## Cross-References

| Document | Path |
|----------|------|
| Triggers & Functions | `03-database-design/triggers-and-functions.md` |
| CRM Tables | `03-database-design/crm-tables.md` |
| Order Tables | `03-database-design/order-tables.md` |
| Reports API | `05-api-documentation/reports-api.md` |
| Backend Architecture | `01-system-architecture/backend-architecture.md` |
| Conversations | `04-core-modules/conversations.md` |
