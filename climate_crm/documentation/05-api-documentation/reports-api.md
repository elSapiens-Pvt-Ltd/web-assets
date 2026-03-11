# Reports API

> Module: `climate/api/reports`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [CRM Reports — ConversationReports](#crm-reports--conversationreports)
3. [Order Reports — Reports & OrderReports](#order-reports--reports--orderreports)
4. [Dashboards — DashBoard](#dashboards--dashboard)
5. [Export — ReportExports](#export--reportexports)
6. [Cross-References](#cross-references)

---

## Overview

All CRM report endpoints apply role-based filtering — sales agents (`role_id=4`) automatically see only their own data. All date-based endpoints support a `preset` query parameter for quick date ranges: `today`, `yesterday`, `this_week`, `last_week`, `this_month`, `last_month`, `last_7_days`, `last_30_days`.

**Standard response envelope**:
```json
{
  "success": true,
  "data": { "..." },
  "filters": { "start_date": "2026-03-01", "end_date": "2026-03-11" },
  "generated_at": "2026-03-11 10:30:00"
}
```

---

## CRM Reports — ConversationReports

### GET /conversationreports/frt_agents

**Capability**: `crm_reports.view_frt_summary`, `crm_reports.view`

Per-agent First Response Time breakdown.

**Query Parameters**: `start_date`, `end_date`, `agent_id`, `preset`

**Response** (200):
```json
{
  "success": true,
  "data": [
    {
      "user_id": 5,
      "agent_name": "Priya Sharma",
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
  ]
}
```

---

### GET /conversationreports/frt_summary

**Capability**: `crm_reports.view_frt_summary`, `crm_reports.view`

Overall business FRT summary with fastest/slowest agent.

**Query Parameters**: `start_date`, `end_date`, `agent_id`, `preset`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "total_users": 8,
    "total_conversations": 950,
    "conversations_with_frt": 820,
    "conversations_without_frt": 130,
    "overall_avg_frt_seconds": 420,
    "overall_avg_frt_minutes": 7.0,
    "fastest_user": { "user_id": 5, "agent_name": "Priya", "avg_frt_seconds": 180 },
    "slowest_user": { "user_id": 8, "agent_name": "Rahul", "avg_frt_seconds": 900 }
  }
}
```

---

### GET /conversationreports/frt_report

**Capability**: `crm_reports.view_frt_summary`, `crm_reports.view`

Combined agents + summary in single request.

**Query Parameters**: `start_date`, `end_date`, `agent_id`, `preset`

**Response** (200): `{ "data": { "agents": [...], "summary": {...} } }`

---

### POST /conversationreports/funnel_report

**Capability**: `crm_reports.view_conversation_funnel`, `crm_reports.view`

Sales funnel with 3 views (cohort, activity, current status).

**Request**:
```json
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-11",
  "conversation_type": "contact"
}
```

`conversation_type`: `"contact"`, `"opportunity"`, or `null` (all)

---

### POST /conversationreports/trend_report

**Capability**: `crm_reports.view_trend_report`, `crm_reports.view`

Daily/weekly trend lines for conversation stage transitions.

**Request**:
```json
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-11",
  "granularity": "daily",
  "conversation_type": "contact"
}
```

`granularity`: `"daily"` or `"weekly"`

---

### POST /conversationreports/enhanced_trend_report

**Capability**: `crm_reports.view_trend_report`, `crm_reports.view`

Enhanced trend with agent breakdown, source breakdown, velocity metrics, and loss analysis.

**Request**:
```json
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-11",
  "conversation_type": "contact"
}
```

---

### GET /conversationreports/aging_report

**Capability**: `crm_reports.view_contact_aging`, `crm_reports.view_opportunity_aging`, `crm_reports.view`

Open conversations grouped by stage and age bucket.

**Query Parameters**: `conversation_type` (`contact` or `opportunity`)

**Age Buckets**: 0-2 days, 3-7 days, 8-14 days, 15-30 days, 30+ days

---

### GET /conversationreports/aging_by_source

**Capability**: `crm_reports.view_contact_aging`, `crm_reports.view_opportunity_aging`, `crm_reports.view`

Aging grouped by lead source with per-agent breakdown.

**Query Parameters**: `conversation_type` (default: `contact`)

---

### POST /conversationreports/unqualified_analysis

**Capability**: `crm_reports.view_contact_unqualified`, `crm_reports.view_opportunity_unqualified`, `crm_reports.view`

Unqualified conversations grouped by disposition reason.

**Request**:
```json
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-11"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "contact": [{ "reason": "not_interested", "label": "Not Interested", "count": 45, "percentage": 22.5 }],
    "opportunity": [...],
    "combined": [...],
    "summary": { "total_contact": 200, "total_opportunity": 80, "total": 280 },
    "agent_wise": [{ "user_id": 5, "agent_name": "John", "contact": {...}, "opportunity": {...} }],
    "source_wise": [{ "source_id": 1, "source_name": "WhatsApp", "contact": {...}, "opportunity": {...} }]
  }
}
```

---

### POST /conversationreports/source_breakdown

**Capability**: `crm_reports.view_source_breakdown`, `crm_reports.view`

Per-source funnel metrics.

**Request**:
```json
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-11",
  "conversation_type": "contact"
}
```

---

### POST /conversationreports/outcome_report

**Capability**: `crm_reports.view_outcome`, `crm_reports.view`

Opportunity → Order conversion with new vs. existing customer breakdown.

**Request**:
```json
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-11"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "summary": {
      "opportunities": 150,
      "opportunity_amount": 500000,
      "orders": 45,
      "order_amount": 180000,
      "conversion_rate": 30.0,
      "new_customer": { "orders": 30, "amount": 120000, "percentage": 66.7 },
      "existing_customer": { "orders": 15, "amount": 60000, "percentage": 33.3 }
    },
    "users": [{ "user_id": 5, "creator_name": "John", "opportunities": 40, "orders": 15, "conversion_rate": 37.5 }],
    "sources": [{ "source_id": 1, "source_name": "WhatsApp", "opportunities": 60, "orders": 20, "conversion_rate": 33.3 }]
  }
}
```

---

### POST /conversationreports/revenue_contribution

**Capability**: `crm_reports.view_revenue_contribution`, `crm_reports.view`

Revenue attribution by user and source with new/existing customer split.

**Request**:
```json
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-11"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "summary": {
      "orders": 200,
      "order_amount": 850000,
      "avg_order_value": 4250,
      "new_customer": { "orders": 120, "amount": 480000, "percentage": 60.0, "avg_order": 4000 },
      "existing_customer": { "orders": 80, "amount": 370000, "percentage": 40.0, "avg_order": 4625 }
    },
    "users": [{ "user_id": 5, "creator_name": "John", "orders": 50, "order_amount": 200000, "contribution_pct": 23.5 }],
    "sources": [{ "source_id": 1, "source_name": "WhatsApp", "orders": 80, "order_amount": 320000, "contribution_pct": 37.6 }]
  }
}
```

---

### POST /conversationreports/agent_activity

**Capability**: `crm_reports.view_agent_activity`, `crm_reports.view`

Agent performance: calls (incoming/outgoing), messages, follow-up tasks.

**Request**:
```json
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-11"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "summary": {
      "incoming_attempted": 500, "incoming_successful": 400, "incoming_missed": 100,
      "outgoing_attempted": 800, "outgoing_successful": 600, "outgoing_missed": 200,
      "total_call_duration_formatted": "10h 0m",
      "messages_sent": 1200, "followup_tasks_created": 350,
      "active_users": 8, "success_rate": 76.9
    },
    "users": [
      {
        "user_id": 5, "user_name": "Priya",
        "incoming_successful": 50, "outgoing_successful": 80,
        "total_call_duration_formatted": "1h 30m",
        "messages_sent": 150, "success_rate": 81.3
      }
    ],
    "daily_trend": [
      { "summary_date": "2026-03-01", "total_successful": 120, "messages_sent": 80 }
    ]
  }
}
```

---

## Order Reports — Reports & OrderReports

### GET /reports/weightProjection

Weight-wise order projection.

### GET /reports/gradewiseSummary

Grade-wise order summary.

### POST /reports/getDailyConfirmedOrders

Daily confirmed orders summary with amounts.

**Request**: `{ "start_date": "2026-03-01", "end_date": "2026-03-11" }`

### POST /reports/dailyConfirmedOrdersExportExcel

Export daily confirmed orders to Excel.

### POST /reports/downloadExcel

Download report as Excel file.

### POST /reports/export

Generic report export.

### GET /reports/getCompanyGodowns

Returns list of company warehouses/godowns.

### POST /reports/downloadContactsList

Export filtered contact list as Excel.

**Request**:
```json
{
  "filters": { "status": "active", "region": "South" },
  "fields": ["contact_name", "phone", "account_name", "designation"]
}
```

### POST /orderreports/gradeSalesReport

Grade-wise sales analytics.

### POST /orderreports/downloadGradeSalesReport

Export grade sales report to Excel.

---

## Dashboards — DashBoard

### GET /dashboard/data

Main dashboard data (all roles).

### GET /dashboard/getContacts

Contact/conversation metrics.

### GET /dashboard/getPayments

Payment overview.

### GET /dashboard/getSummary

Combined summary data.

### GET /dashboard/getSales

Sales/revenue metrics.

### GET /dashboard/agentDashBoard

Agent-specific dashboard data (role_id=4). Returns only the authenticated agent's data.

### GET /dashboard/adminDashBoard

Admin dashboard data (role_id=9). Returns team-wide performance metrics.

---

## Export — ReportExports

Two-step process: (1) POST to generate endpoint → returns file path, (2) POST to download endpoint with file path.

**Capability**: `crm_reports.view` (all except callLogs which requires `user`)

### Generate Endpoints

| Endpoint | Report |
|----------|--------|
| `POST /reportexports/outcomeReport` | Outcome Report |
| `POST /reportexports/revenueContribution` | Revenue Contribution |
| `POST /reportexports/agentActivity` | Agent Activity |
| `POST /reportexports/frtSummary` | FRT Summary |
| `POST /reportexports/contactConversations` | Contact Funnel |
| `POST /reportexports/contactSourceBreakdown` | Contact Source Breakdown |
| `POST /reportexports/contactAging` | Contact Aging |
| `POST /reportexports/contactUnqualified` | Contact Unqualified |
| `POST /reportexports/opportunityConversations` | Opportunity Funnel |
| `POST /reportexports/opportunitySourceBreakdown` | Opportunity Source Breakdown |
| `POST /reportexports/opportunityAging` | Opportunity Aging |
| `POST /reportexports/opportunityUnqualified` | Opportunity Unqualified |
| `POST /reportexports/conversationTrend` | Conversation Trend |
| `POST /reportexports/callLogs` | Call Logs |

**Common request body**:
```json
{
  "start_date": "2026-03-01",
  "end_date": "2026-03-11"
}
```

Funnel/source endpoints also accept `view_type`: `"cohort"`, `"activity"`, or `"current"`.
Aging endpoints accept `view_mode`: `"stage"` or `"agent"`.
FRT endpoint accepts `conversation_type`: `"contact"` or `"opportunity"`.

**Generate response**:
```json
{
  "success": true,
  "file": "reports/outcome_report_20260311_143022.xlsx",
  "file_name": "Outcome Report 2026-03-01 to 2026-03-11.xlsx"
}
```

### POST /reportexports/download

**Request**: `{ "file": "reports/outcome_report_20260311_143022.xlsx" }`

**Response**: Binary Excel file stream (`Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)

---

## Cross-References

| Document | Path |
|----------|------|
| Reporting Module | `04-core-modules/reporting.md` |
| Triggers & Functions | `03-database-design/triggers-and-functions.md` |
| Conversations Module | `04-core-modules/conversations.md` |
| Authentication | `05-api-documentation/authentication.md` |
