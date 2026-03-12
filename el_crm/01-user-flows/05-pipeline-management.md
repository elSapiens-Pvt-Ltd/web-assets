# Pipeline Management

> Role: Sales Agent (own pipeline), Sales Manager (team pipeline)
> Primary screen: Pipeline (Kanban board)

---

## Flow Summary

Opportunities move through configurable pipeline stages on a visual kanban board. Agents drag cards between stages, update values, and track deals to close. Managers review the full team pipeline for forecasting and bottleneck identification.

---

## Pipeline Board Layout

```
┌───────────────────────────────────────────────────────────────────────────┐
│ Pipeline: Sales Pipeline ▾    Filter: [Agent ▾] [Source ▾] [Date ▾]     │
├──────────────┬──────────────┬──────────────┬──────────────┬──────────────┤
│ New          │ Discovery    │ Proposal     │ Negotiation  │ Closed       │
│ ₹2,50,000   │ ₹4,80,000   │ ₹3,20,000   │ ₹1,50,000   │ ₹8,40,000   │
│ (12 deals)   │ (8 deals)    │ (5 deals)    │ (3 deals)    │ (15 deals)   │
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ ┌──────────┐ │ ┌──────────┐ │ ┌──────────┐ │              │ ┌──────────┐ │
│ │Acme Corp │ │ │TechParts │ │ │GreenFoods│ │              │ │SteelMax  │ │
│ │₹50,000   │ │ │₹1,20,000 │ │ │₹80,000  │ │              │ │₹2,00,000 │ │
│ │Priya     │ │ │Ravi      │ │ │Priya    │ │              │ │Won ✓     │ │
│ │15 Mar    │ │ │20 Mar    │ │ │18 Mar   │ │              │ │10 Mar    │ │
│ └──────────┘ │ └──────────┘ │ └──────────┘ │              │ └──────────┘ │
│ ┌──────────┐ │ ┌──────────┐ │              │              │ ┌──────────┐ │
│ │BuildRight│ │ │FreshMart │ │              │              │ │NovaTrade │ │
│ │₹35,000   │ │ │₹2,00,000 │ │              │              │ │Lost ✗    │ │
│ │Ankit     │ │ │Ankit     │ │              │              │ │₹60,000   │ │
│ └──────────┘ │ └──────────┘ │              │              │ └──────────┘ │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

### Card Information
Each opportunity card shows:
- Account/contact name
- Expected value (currency, workspace-configured)
- Assigned agent
- Expected close date
- Age in current stage (color-coded: green < 7d, amber 7-14d, red > 14d)
- Source icon
- Custom field badges (workspace-configurable, e.g., priority flag)

---

## Agent Flow: Manage Own Pipeline

### Move Opportunity Between Stages

```
Agent drags "Acme Corp" card from "New" → "Discovery"
  → Drop zone highlights on valid target columns
  → On drop:
      - System updates opportunity.current_stage_id
      - Logs stage change activity with timestamp
      - Publishes crm.opportunity.stage_changed event
      - If workflow rule exists (e.g., "On Discovery → send intro email") → executes
  → Card moves to new column
  → Column totals update in real-time
```

### Close Won

```
Agent drags opportunity to "Closed" column (or clicks card → "Close")
  → Close dialog:
      Outcome: Won ✓ | Lost ✗
      → Agent selects "Won"
      → Won Amount: ₹50,000 (pre-filled from expected, editable)
      → Close Date: today (pre-filled, editable)
      → Notes: "Order confirmed, PO received"
      → Link Order (optional): if Commerce service is integrated
  → Save
  → Card shows green "Won ✓" badge
  → System:
      - Updates opportunity status to "won"
      - Logs activity
      - Publishes crm.opportunity.won event → Commerce can create order
      - Updates reports (conversion rate, revenue)
```

### Close Lost

```
Agent selects "Lost"
  → Lost Reason (workspace-configurable):
      - Price Too High
      - Competitor Won
      - Customer Went Silent
      - Budget Cut
      - Timeline Mismatch
      - Custom reasons...
  → Competitor Name (optional text field)
  → Notes: optional
  → Save
  → Card shows red "Lost ✗" badge
  → System logs for loss analysis reports
```

### Update Opportunity Details

```
Agent clicks opportunity card → detail panel opens (slide-over or modal):
  ┌─────────────────────────────────────┐
  │ Acme Corp — ₹50,000                │
  │ Pipeline: Sales Pipeline            │
  │ Stage: Discovery                    │
  │ Agent: Priya                        │
  │ Created: 2026-03-01                 │
  │ Expected Close: 2026-03-20         │
  │                                     │
  │ Contact: Rahul Verma               │
  │ Account: Acme Corp Pvt Ltd         │
  │                                     │
  │ [Custom Fields]                     │
  │ Product Interest: Grade A Turmeric  │
  │ Volume: 500 kg/month               │
  │                                     │
  │ [Activities] [Notes] [Conversations]│
  │                                     │
  │ [Edit] [Transfer] [Delete]          │
  └─────────────────────────────────────┘

  → Agent can:
      - Edit value, close date, notes, custom fields
      - View linked conversation(s)
      - Jump to inbox for this contact
      - Transfer to another agent
      - Add notes directly
```

---

## Manager Flow: Team Pipeline Review

### Filter & Aggregate View

```
Manager opens Pipeline
  → Defaults to: All Agents, Current Month
  → Filters:
      - Agent: [All | Priya | Ravi | Ankit | ...]
      - Date range: opportunities created / expected close within range
      - Source: [All | WhatsApp | JustDial | ...]
      - Value range: min-max
  → Summary bar at top:
      Total Pipeline Value: ₹12,40,000
      Weighted Value: ₹6,80,000 (stage-weighted probabilities)
      Win Rate (this period): 32%
      Avg Deal Size: ₹45,000
      Avg Time to Close: 18 days
```

### Stage-Weighted Forecasting

Each pipeline stage has a configurable probability (set in workspace settings):

| Stage | Default Probability |
|-------|-------------------|
| New | 10% |
| Discovery | 25% |
| Proposal | 50% |
| Negotiation | 75% |
| Closed Won | 100% |
| Closed Lost | 0% |

Weighted pipeline value = SUM(opportunity_value × stage_probability)

### Identify Bottlenecks

```
Manager sees: "Proposal" column has 5 deals, some with red age indicators (> 14 days)
  → Clicks "Proposal" column header → sorted by age (oldest first)
  → Identifies stalled deals
  → Can: reassign, add comment, or message agent about the deal
```

---

## Multiple Pipelines

A workspace can have multiple pipelines for different sales processes:

```
Settings → Pipelines:
  Pipeline 1: "New Business" (New → Discovery → Proposal → Negotiation → Closed)
  Pipeline 2: "Renewals" (Upcoming → Contacted → Renewed / Churned)
  Pipeline 3: "Partnerships" (Identified → Outreach → Discussion → Agreement → Active)
```

Agent selects which pipeline to view via dropdown. Opportunities belong to exactly one pipeline.

---

## Pipeline Views

| View | Description |
|------|-------------|
| **Kanban** (default) | Drag-and-drop columns, visual card-based |
| **List** | Table view with sortable columns: contact, value, stage, agent, age, close date |
| **Forecast** | Grouped by expected close month, weighted values, comparison to targets |

---

## Data & Events

| Action | System Behavior |
|--------|----------------|
| Stage change | Log activity, publish event, evaluate workflow rules |
| Close won | Update status, publish event, feed revenue reports |
| Close lost | Update status, log reason, feed loss analysis reports |
| Value change | Log activity, update pipeline totals |
| Transfer | Log assignment change, notify new agent |
| Create opportunity | Check for duplicates (same contact + pipeline), warn if exists |

---

## Pipeline Configuration (Admin — Settings)

```
Settings → Pipelines → Edit "Sales Pipeline"
  Stages:
    1. New (probability: 10%, color: blue)
    2. Discovery (probability: 25%, color: cyan)
    3. Proposal (probability: 50%, color: yellow)
    4. Negotiation (probability: 75%, color: orange)
    5. Closed (probability: n/a, terminal: true, outcomes: Won/Lost)

  Rules:
    - Required fields to enter "Proposal": Expected Value, Expected Close Date
    - Mandatory lost reason on "Closed Lost"
    - Auto-notification to manager when deal > ₹1,00,000 enters "Negotiation"

  Add Stage | Remove Stage | Reorder (drag)
```
