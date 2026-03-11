# Reports API

> Module: `climate/api/reports`
> Last updated: 2026-03-11

---

## Table of Contents

1. [CRM Reports](#crm-reports)
2. [Order Reports](#order-reports)
3. [Export](#export)
4. [Cross-References](#cross-references)

---

## CRM Reports

All CRM report endpoints accept date range filters and return analytics data. Sales agents (role_id=4) are automatically filtered to see only their own data.

### GET /conversationreports/frt_agents

**Capability**: `@capability crm_reports.view_frt_summary crm_reports.view`

First Response Time report — measures agent response speed.

**Query Parameters**: `start_date`, `end_date`, `agent_id`, `preset`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "overall_avg_frt_minutes": 12.5,
    "by_agent": [
      { "agent_id": 5, "agent_name": "Priya Sharma", "avg_frt": 8.2, "total_conversations": 45 },
      { "agent_id": 8, "agent_name": "Rahul Kumar", "avg_frt": 15.3, "total_conversations": 38 }
    ],
    "distribution": {
      "under_5_min": 120,
      "5_to_15_min": 85,
      "15_to_30_min": 45,
      "30_to_60_min": 20,
      "over_60_min": 10
    }
  },
  "filters": {},
  "generated_at": "2026-03-11 10:30:00"
}
```

---

### POST /conversationreports/funnel_report

**Capability**: `@capability reports.crm`

Sales funnel — lead stage progression.

**Request**:
```json
{
  "date_from": "2026-03-01",
  "date_to": "2026-03-11",
  "agent_ids": [],
  "source_id": null
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "stages": [
      { "stage": "new", "count": 250, "percentage": 100 },
      { "stage": "attempted", "count": 180, "percentage": 72 },
      { "stage": "contacted", "count": 150, "percentage": 60 },
      { "stage": "nurturing", "count": 100, "percentage": 40 },
      { "stage": "qualified", "count": 65, "percentage": 26 },
      { "stage": "unqualified", "count": 50, "percentage": 20 }
    ],
    "conversion_rates": {
      "new_to_attempted": 72,
      "attempted_to_contacted": 83,
      "contacted_to_nurturing": 67,
      "nurturing_to_qualified": 65
    }
  }
}
```

---

### POST /conversationreports/aging_report

**Capability**: `@capability reports.crm`

Conversation aging analysis.

**Response** (200):
```json
{
  "success": true,
  "data": {
    "buckets": [
      { "range": "0-1 days", "count": 45 },
      { "range": "1-3 days", "count": 62 },
      { "range": "3-7 days", "count": 38 },
      { "range": "7-14 days", "count": 25 },
      { "range": "14-30 days", "count": 15 },
      { "range": "30+ days", "count": 8 }
    ]
  }
}
```

---

### POST /conversationreports/unqualified_report

**Capability**: `@capability reports.crm`

Analysis of disqualified leads by disposition reason.

**Response** (200):
```json
{
  "success": true,
  "data": {
    "total_unqualified": 305,
    "by_disposition": [
      { "disposition": "price_too_high", "count": 85, "percentage": 28 },
      { "disposition": "not_interested", "count": 62, "percentage": 20 },
      { "disposition": "rnr3", "count": 55, "percentage": 18 },
      { "disposition": "competitor_chosen", "count": 38, "percentage": 12 },
      { "disposition": "budget_issues", "count": 25, "percentage": 8 }
    ]
  }
}
```

---

### POST /conversationreports/outcome_report

**Capability**: `@capability reports.crm`

Deal outcome analysis (win/loss/pending).

---

### POST /conversationreports/revenue_contribution

**Capability**: `@capability reports.crm`

Revenue attribution by agent, source, and region.

**Response** (200):
```json
{
  "success": true,
  "data": {
    "total_revenue": 1250000,
    "by_agent": [
      { "agent_name": "Priya Sharma", "revenue": 450000, "orders": 15 },
      { "agent_name": "Rahul Kumar", "revenue": 380000, "orders": 12 }
    ],
    "by_source": [
      { "source": "WhatsApp", "revenue": 650000 },
      { "source": "JustDial", "revenue": 280000 },
      { "source": "Phone", "revenue": 200000 }
    ]
  }
}
```

---

### POST /conversationreports/agent_activity

**Capability**: `@capability reports.crm`

Agent performance metrics.

**Response** (200):
```json
{
  "success": true,
  "data": [
    {
      "agent_id": 5,
      "agent_name": "Priya Sharma",
      "total_conversations": 45,
      "new_assigned": 30,
      "closed_qualified": 12,
      "closed_unqualified": 8,
      "avg_response_time_min": 8.2,
      "transfers_in": 5,
      "transfers_out": 2,
      "orders_created": 10,
      "revenue": 450000
    }
  ]
}
```

---

## Order Reports

### POST /reports/getDailyConfirmedOrders

Daily confirmed orders summary.

**Request**:
```json
{
  "date_from": "2026-03-01",
  "date_to": "2026-03-11"
}
```

---

## Export

### POST /reportexports/export

**Capability**: `@capability reports.export`

Generates Excel/CSV export of report data.

**Request**:
```json
{
  "report_type": "agent_activity",
  "format": "xlsx",
  "date_from": "2026-03-01",
  "date_to": "2026-03-11",
  "filters": {}
}
```

**Response**: File download or S3 URL.

### POST /reports/downloadContactsList

Exports filtered contact list as Excel.

**Request**:
```json
{
  "filters": {
    "status": "active",
    "region": "South"
  },
  "fields": ["contact_name", "phone", "account_name", "designation"]
}
```

---

## Cross-References

| Document | Path |
|----------|------|
| Reporting Module | `04-core-modules/reporting.md` |
| Conversations Module | `04-core-modules/conversations.md` |
| Authentication | `05-api-documentation/authentication.md` |
