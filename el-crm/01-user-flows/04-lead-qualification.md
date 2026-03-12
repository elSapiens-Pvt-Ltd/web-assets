# Lead Qualification

> Role: Sales Agent
> Trigger: New conversation created (from inbound message or lead capture)
> Primary screen: Inbox → Contact Details panel

---

## Flow Summary

Agent receives a new lead (conversation in "New" stage), engages with the customer to understand their needs, and moves them through qualification stages. The outcome is either an opportunity (qualified) or a disposition (unqualified).

---

## Qualification Pipeline (Default — Workspace Configurable)

```
┌──────┐   ┌───────────┐   ┌───────────┐   ┌─────────────┐   ┌────────────┐
│ New  │──→│ Contacted │──→│ Qualified │──→│ Opportunity │──→│ Won / Lost │
└──────┘   └───────────┘   └───────────┘   └─────────────┘   └────────────┘
    │           │                │                                   │
    └───────────┴────────────────┘                                   │
              ↓                                                      │
    ┌──────────────┐                                                 │
    │ Unqualified  │←────────────────────────────────────────────────┘
    └──────────────┘
```

**Stage transitions are workspace-configurable.** The above is the default. A workspace can have different stages (e.g., "Discovery → Demo → Proposal → Negotiation → Closed").

---

## Step-by-Step Flow

### 1. New Lead Arrives

```
System auto-assigns conversation to Agent Priya
  → Priya's inbox shows new conversation:
      Contact: "+919876543210" or "Rahul Verma" (if name captured from lead)
      Stage badge: "New" (blue)
      Source: WhatsApp / JustDial / Facebook / ...
      Message: initial enquiry text
```

### 2. First Contact

```
Priya opens conversation → reads initial message
  → Replies with greeting + qualifying questions
  → Clicks "Change Stage" in Contact Details panel
  → Selects: "Contacted"
  → System logs:
      - Stage change activity (New → Contacted)
      - Timestamps for pipeline velocity tracking
      - First Response Time (if this is first agent reply)
```

### 3. Qualification Assessment

Agent gathers information through conversation. Key qualification criteria (workspace-configurable):

| Criteria | Example Questions |
|----------|-------------------|
| Budget | "What's your expected order volume?" |
| Authority | "Are you the decision maker?" |
| Need | "What products are you looking for?" |
| Timeline | "When do you need delivery?" |

```
Agent updates contact details as information is gathered:
  → Contact Details → Edit
  → Updates: Company name, designation, location
      → These go to accounts-api via CRM backend gRPC
  → Updates custom fields (workspace-configured):
      "Expected Monthly Volume": "500 kg"
      "Product Interest": "Grade A Turmeric"
      → These are stored in CRM custom_field_values table
```

### 4A. Qualify → Create Opportunity

```
Agent determines lead is qualified
  → Changes stage: "Contacted" → "Qualified"
  → System behavior (workspace-configurable):
      Option A (auto): Workflow rule creates opportunity automatically
      Option B (manual): Agent clicks "Create Opportunity" in Contact Details

Creating opportunity:
  → Pipeline: "Sales Pipeline" (default, or agent selects if multiple pipelines)
  → Stage: "New Opportunity" (first stage in selected pipeline)
  → Expected Value: ₹50,000
  → Expected Close Date: 2026-04-15
  → Notes: "Interested in bulk Grade A turmeric, 500kg/month"
  → Save

  → Opportunity appears in:
      - Contact Details → Opportunities tab
      - Pipeline board (kanban view)
      - Reports (funnel, revenue)
```

### 4B. Mark as Unqualified

```
Agent determines lead is not a fit
  → Changes stage: "New/Contacted" → "Unqualified"
  → Disposition dialog appears:
      Reason (workspace-configurable list):
        - Not Interested
        - Budget Too Low
        - Wrong Product Category
        - Competitor Chosen
        - Duplicate
        - Spam / Irrelevant
        - Location Not Serviceable
        - Not Decision Maker
        - Custom reasons...
      Notes: optional free text
  → Agent selects reason, adds notes, confirms
  → Conversation status: closed
  → Conversation archived (removed from active inbox, searchable in "Closed" filter)
  → System logs: stage change + disposition reason + notes
  → Data feeds into: Unqualified Analysis Report
```

### 4C. Needs Nurturing (Not Ready Yet)

```
Lead shows interest but not ready to buy
  → Agent keeps stage at "Contacted" (or workspace may have a "Nurturing" stage)
  → Creates follow-up: "Check in after 2 weeks"
  → Adds note: "Interested but current supplier contract ends in March"
  → Conversation remains in inbox at lower priority
  → Follow-up reminder triggers in 2 weeks
```

---

## Stage Change Rules (Workspace-Configurable)

| Rule | Example |
|------|---------|
| Required fields per stage | "Qualified" requires: contact name, company, phone |
| Mandatory disposition on terminal stages | "Unqualified" and "Lost" require reason selection |
| Auto-actions on stage change | "Qualified" → auto-create opportunity |
| Notifications on stage change | "Opportunity" → notify manager |
| Stage restrictions | Agent can only move forward; backward requires manager |

---

## Conversion Tracking

The system automatically tracks for reports:

| Metric | Calculation |
|--------|-------------|
| Lead → Contacted rate | conversations moved past "New" / total conversations |
| Contacted → Qualified rate | conversations reaching "Qualified" / conversations at "Contacted" |
| Qualified → Opportunity rate | opportunities created / conversations at "Qualified" |
| Time in each stage | timestamp difference between stage transitions |
| Qualification rate by source | qualified / total per source_id |
| Qualification rate by agent | qualified / total per agent_id |

---

## Custom Fields During Qualification

Workspace admins configure custom fields that appear during qualification:

```
Custom Field Configuration (Settings → Custom Fields):
  Entity: Contact
  Fields:
    - "Business Type" (dropdown: Manufacturer, Trader, Retailer, Distributor)
    - "Expected Monthly Volume" (text)
    - "Product Interest" (multi-select from product catalog)
    - "Preferred Payment Terms" (dropdown: Advance, 30 days, 60 days)

  Entity: Opportunity
  Fields:
    - "Competitor Quote" (currency)
    - "Decision Timeline" (date)
    - "Procurement Process" (dropdown: Direct, Tender, Comparison)
```

These fields appear in the Contact Details panel and are filterable in reports.
