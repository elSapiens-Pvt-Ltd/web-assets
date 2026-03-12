# Pipeline Review

> Role: Manager, Admin
> Trigger: Manager reviews team pipeline for forecasting and coaching
> Primary screen: Pipeline (/pipeline), Dashboard, Reports

---

## Flow Summary

Managers review the full team pipeline to forecast revenue, identify stuck deals, compare agent performance, and take coaching actions. This builds on the Pipeline Board (see 05-pipeline-management.md) with manager-specific capabilities.

---

## Manager Pipeline View

```
Manager opens Pipeline (sidebar)
  → Default: All agents, all sources, default pipeline
  → Full team pipeline visible (agent sees only own deals)

┌──────────────────────────────────────────────────────────────────┐
│ Pipeline: Sales Pipeline ▾    View: [Kanban] [List] [Forecast]  │
│ Agent: [All ▾]  Source: [All ▾]  Date: [This Quarter ▾]        │
├──────────────────────────────────────────────────────────────────┤
│ Summary Bar:                                                     │
│ Total: ₹12,40,000 (28 deals) | Weighted: ₹6,80,000            │
│ Win Rate: 32% | Avg Deal: ₹45,000 | Avg Close: 18 days        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ [Kanban board with all agents' opportunities visible]            │
│ Each card shows agent name in addition to contact, value, date   │
│                                                                  │
│ Cards color-coded by age in stage:                               │
│   Green border: < 7 days                                         │
│   Amber border: 7-14 days                                        │
│   Red border: > 14 days (stuck deal)                             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Identifying Stuck Deals

```
Manager scans pipeline → notices red-bordered cards in "Proposal" stage
  → Sorts column by "Age in stage" (click column header)
  → Sees:
      GreenFoods — ₹80,000 — Priya — 22 days in Proposal
      BuildRight — ₹35,000 — Ankit — 18 days in Proposal

  → Clicks GreenFoods card → detail slide-over:
      Last activity: 12 days ago (follow-up completed, no response)
      Last message: 15 days ago (customer hasn't replied)
      Follow-ups: 1 overdue

  → Manager actions:
      a. Add internal note: "Priya, please escalate to customer's manager"
      b. Create follow-up for Priya: "Call GreenFoods procurement head"
      c. Reassign to senior agent if Priya unable to close
      d. Move to "Lost" if deal is dead
```

---

## Forecast View

```
Pipeline → View: [Forecast]

┌──────────────────────────────────────────────────────────────────┐
│ Pipeline Forecast                                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Expected Close Month:                                            │
│                                                                  │
│ March 2026                                                       │
│ ┌──────────┬──────────┬──────────┬──────────┐                   │
│ │ Total    │ Weighted │ Deals    │ vs Target│                   │
│ │₹4,50,000 │₹2,80,000 │ 12       │ 70% ⚠  │                   │
│ └──────────┴──────────┴──────────┴──────────┘                   │
│                                                                  │
│ April 2026                                                       │
│ ┌──────────┬──────────┬──────────┬──────────┐                   │
│ │₹5,20,000 │₹3,10,000 │ 10       │ 78% ⚠  │                   │
│ └──────────┴──────────┴──────────┴──────────┘                   │
│                                                                  │
│ May 2026                                                         │
│ ┌──────────┬──────────┬──────────┬──────────┐                   │
│ │₹2,70,000 │₹1,20,000 │ 6        │ 30% ⚠  │                   │
│ └──────────┴──────────┴──────────┴──────────┘                   │
│                                                                  │
│ Agent Breakdown (March):                                         │
│ Priya:  ₹1,50,000 (5 deals) | Weighted: ₹90,000               │
│ Ravi:   ₹1,80,000 (4 deals) | Weighted: ₹1,10,000             │
│ Ankit:  ₹1,20,000 (3 deals) | Weighted: ₹80,000               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

Weighted value = SUM(deal_value × stage_probability)
vs Target = weighted_value / workspace_monthly_target × 100
```

---

## Agent Comparison

```
Pipeline → List View → Group By: Agent

┌──────────────────────────────────────────────────────────────────┐
│ Agent Pipeline Comparison                                        │
├──────────────────────────────────────────────────────────────────┤
│ Agent    │ Deals │ Total Value │ Weighted │ Avg Deal │ Win Rate │
│ ─────────┼───────┼─────────────┼──────────┼──────────┼──────────│
│ Priya    │ 10    │ ₹3,20,000  │ ₹1,80,000│ ₹32,000  │ 38%     │
│ Ravi     │ 8     │ ₹4,50,000  │ ₹2,60,000│ ₹56,000  │ 28%     │
│ Ankit    │ 10    │ ₹4,70,000  │ ₹2,40,000│ ₹47,000  │ 30%     │
├──────────┼───────┼─────────────┼──────────┼──────────┼──────────┤
│ Total    │ 28    │ ₹12,40,000 │ ₹6,80,000│ ₹44,300  │ 32%     │
└──────────────────────────────────────────────────────────────────┘

Observations:
  → Priya: highest win rate but smallest deals → coach on upselling
  → Ravi: largest deals but lowest win rate → coach on closing technique
  → Ankit: balanced but longest avg close time → coach on urgency
```

---

## Coaching Actions

Actions a manager can take during pipeline review:

| Observation | Action | How |
|-------------|--------|-----|
| Deal stuck > 14 days | Add note to agent | Click card → add internal note |
| Deal at risk | Create follow-up | Click card → create follow-up for agent |
| Agent overloaded | Reassign deals | Select deals → bulk reassign |
| Agent underperforming | Schedule 1:1 | External (not in CRM) |
| High-value deal needs attention | Change priority | Click card → set priority to High/Urgent |
| Dead deal lingering | Close as lost | Click card → close lost with reason |
| Missing information | Request update | Add note asking agent to update fields |

---

## Pipeline Health Alerts

System can surface alerts on the pipeline view:

```
⚠ Alerts (3):
  • 5 deals stuck > 14 days in "Proposal" stage
  • 2 deals past expected close date (March 1, March 5)
  • Agent Ravi has 0 new opportunities this week (below average)
```

These alerts are generated from:
- Stage aging thresholds (workspace-configurable)
- Overdue expected close dates
- Agent activity anomalies (significantly below team average)

---

## Data Sources

| View | API Endpoint |
|------|-------------|
| Kanban/List | GET /pipelines/:id/opportunities?filters |
| Forecast | GET /pipelines/:id/forecast?months=3 |
| Agent comparison | GET /reports/pipeline-comparison?date_range |
| Stuck deals | GET /pipelines/:id/opportunities?min_age_days=14 |
| Alerts | GET /dashboard/pipeline-alerts |
