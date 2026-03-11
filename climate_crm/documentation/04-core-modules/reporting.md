# Reporting & Analytics Module

> Module: `climate/modules/reporting`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [CRM Reports](#crm-reports)
3. [Order Reports](#order-reports)
4. [Dashboards](#dashboards)
5. [Export System](#export-system)
6. [Frontend Module](#frontend-module)
7. [Report Models Summary](#report-models-summary)
8. [Cross-References](#cross-references)

---

## Overview

The reporting module provides comprehensive analytics across CRM operations, sales pipeline health, and agent performance. Reports are available through dedicated dashboards and an export system for Excel/CSV downloads. The `ConversationReports` controller loads seven dedicated report models and applies role-based data filtering — sales agents (role_id=4) only see their own data.

```php
class ConversationReports extends CI_Controller
{
    public function __construct()
    {
        parent::__construct();
        $this->load->model('reports/AgentFRTReportModel', '_frtReport');
        $this->load->model('reports/ConversationFunnelModel', '_funnelReport');
        $this->load->model('reports/ConversationAgingModel', '_agingReport');
        $this->load->model('reports/UnqualifiedAnalysisModel', '_unqualifiedReport');
        $this->load->model('reports/OutcomeReportModel', '_outcomeReport');
        $this->load->model('reports/RevenueContributionModel', '_revenueContribution');
        $this->load->model('reports/AgentActivityReportModel', '_agentActivityReport');
    }

    private function applyUserFiltering(&$filters)
    {
        $CI = &get_instance();
        $authData = $CI->AuthData ?? [];
        if (isset($authData['role_id']) && $authData['role_id'] == 4) {
            if (!isset($filters['user_id']) && !isset($filters['agent_id'])) {
                $filters['user_id'] = $authData['user_id'] ?? null;
            }
        }
        return $filters;
    }
}
```

---

## CRM Reports

### First Response Time (FRT) Report

Measures how quickly agents respond to new conversations.

**Endpoint**: `GET /conversationreports/frt_agents`
**Model**: `AgentFRTReportModel`

```php
/**
 * @capability crm_reports.view_frt_summary crm_reports.view
 */
public function frt_agents()
{
    $filters = [
        'start_date' => $this->input->get('start_date') ?: date('Y-m-d', strtotime('-30 days')),
        'end_date' => $this->input->get('end_date') ?: date('Y-m-d'),
        'agent_id' => $this->input->get('agent_id') ?: null
    ];
    $this->applyUserFiltering($filters);
    $reportData = $this->_frtReport->getAgentFRTReport($filters);
}
```

**Metrics**: Average FRT per agent, FRT distribution (< 5 min, 5-15 min, 15-30 min, 30-60 min, > 60 min), FRT trend over time, comparison across agents.

**Cron**: `Cron::calculateFRTSummary` pre-calculates FRT metrics periodically.

---

### Conversation Funnel Report

Visualizes lead progression through conversation stages.

**Endpoint**: `POST /conversationreports/funnel_report`
**Model**: `ConversationFunnelModel`

**Funnel Stages**:
```
New            ████████████████████████████  250
Attempted      ██████████████████████        180
Contacted      ██████████████████            150
Nurturing      ████████████                  100
Qualified      ████████                       65
Unqualified    ██████                         50
```

**Metrics**: Count per stage, conversion rate between stages, drop-off analysis. Filterable by date range, agent, source.

---

### Conversation Aging Report

Shows how long conversations remain open at each stage.

**Endpoint**: `POST /conversationreports/aging_report`
**Model**: `ConversationAgingModel`

**Age Buckets**:
| Bucket | Description |
|--------|-------------|
| 0-1 days | Fresh conversations |
| 1-3 days | Recent |
| 3-7 days | Moderate age |
| 7-14 days | Aging |
| 14-30 days | Stale |
| 30+ days | Critical |

**Cron**: `Cron::generateAgingSnapshot` takes periodic snapshots for trend analysis.

---

### Unqualified Analysis Report

Analyzes patterns in disqualified leads to identify areas for improvement.

**Endpoint**: `POST /conversationreports/unqualified_report`
**Model**: `UnqualifiedAnalysisModel`

**Filters**: By agent, date range, source, region.

---

### Outcome Report

Win/loss/pending analysis of qualified leads.

**Endpoint**: `POST /conversationreports/outcome_report`
**Model**: `OutcomeReportModel`

**Outcomes**: Qualified → Order created (won), Qualified → No order yet (pending), Unqualified (lost) by reason.

---

### Revenue Contribution Report

Revenue attribution by agent, source, and region.

**Endpoint**: `POST /conversationreports/revenue_contribution`
**Model**: `RevenueContributionModel`

**Dimensions**: Revenue by agent, by lead source (WhatsApp, JustDial, IndiaMart, etc.), by region, by time period.

---

### Agent Activity Report

Per-agent performance metrics.

**Endpoint**: `POST /conversationreports/agent_activity`
**Model**: `AgentActivityReportModel`

**Metrics per Agent**: Total conversations handled, new conversations assigned, conversations closed (qualified + unqualified), average response time, transfer rate (in/out), orders created, revenue generated.

---

## Order Reports

### Daily Confirmed Orders

**Endpoint**: `POST /reports/getDailyConfirmedOrders`

Daily summary of confirmed orders with amounts.

### Order Analytics

**Controller**: `OrderReports`
**Model**: `OrderReportsModel`

**Metrics**: Orders by status, by courier, by warehouse, weight-wise reports, grade-wise reports.

---

## Dashboards

### Main Dashboard (`/dashboard`)

General overview for all users: active conversations summary, order summary, revenue charts, recent activity.

### Admin Dashboard (`/admindashboard`, role_id: 9)

Sales admin-specific metrics: team performance overview, pipeline health, revenue targets, agent comparison.

### Agent Dashboard (`/agentdashboard`, role_id: 4)

Individual agent view: my active conversations, my pending follow-ups, my orders today, my performance metrics.

### Dashboard Backend (`DashBoard` controller)

| Method | Purpose |
|--------|---------|
| `getContactsSummary()` | Contact/conversation metrics |
| `getPaymentsSummary()` | Payment overview |
| `getSalesSummary()` | Sales/revenue metrics |
| `getDashboardSummary()` | Combined summary data |

---

## Export System

### Export Controller (`ReportExports`)

**Endpoint**: `POST /reportexports/export`

Generates downloadable files in Excel or CSV format.

### Export Service (Frontend)

- `ExportDateRangeDialogComponent`: Date range picker for exports
- Download triggers: Direct download via pre-signed S3 URL or inline response

### Excel Generation

Uses `XlsxWriter` library (server-side): supports multiple sheets, formatted headers and data types, large dataset handling.

### Contact List Export

**Endpoint**: `POST /reports/downloadContactsList`

Exports filtered contact list with selected fields.

---

## Frontend Module

### CRM Reports Module (`views/crm-reports/`)

| Component | Purpose |
|-----------|---------|
| FRT Report | First response time charts |
| Funnel Report | Sales funnel visualization |
| Aging Report | Conversation aging analysis |
| Unqualified Report | Disposition analysis |
| Outcome Report | Win/loss tracking |
| Revenue Report | Revenue attribution |
| Agent Activity | Agent performance |

### Charting Libraries

- **Chart.js / ng2-charts**: Bar, line, pie, doughnut charts
- **ngx-echarts / ECharts**: Advanced visualizations, geographical maps

### Report Filters

Common filter controls across all reports: date range picker, agent selector (multi-select), lead source filter, region filter, conversation stage filter.

---

## Report Models Summary

| Model | Controller | Report Type |
|-------|-----------|-------------|
| `AgentFRTReportModel` | `ConversationReports` | First Response Time |
| `ConversationFunnelModel` | `ConversationReports` | Sales Funnel |
| `ConversationAgingModel` | `ConversationReports` | Aging Analysis |
| `UnqualifiedAnalysisModel` | `ConversationReports` | Unqualified Leads |
| `OutcomeReportModel` | `ConversationReports` | Deal Outcomes |
| `RevenueContributionModel` | `ConversationReports` | Revenue Analytics |
| `AgentActivityReportModel` | `ConversationReports` | Agent Metrics |
| `OrderReportsModel` | `OrderReports` | Order Analytics |
| `ReportExportModel` | `ReportExports` | Export Generation |

---

## Cross-References

| Document | Path |
|----------|------|
| CRM Tables | `03-database-design/crm-tables.md` |
| Order Tables | `03-database-design/order-tables.md` |
| Reports API | `05-api-documentation/reports-api.md` |
| Backend Architecture | `01-system-architecture/backend-architecture.md` |
| Conversations | `04-core-modules/conversations.md` |
