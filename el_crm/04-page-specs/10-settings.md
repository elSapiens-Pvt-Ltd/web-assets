# Page Spec: Settings

> URL: `/settings/*`
> Role: Admin (some sections visible to Manager)
> Data source: CRM workspace config APIs, elauth (team management)

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Settings                                                         │
├────────────────┬─────────────────────────────────────────────────┤
│                │                                                 │
│ General        │  (Settings content area)                       │
│  Workspace     │                                                 │
│  Working Hours │                                                 │
│                │                                                 │
│ Pipeline       │                                                 │
│  Pipelines     │                                                 │
│  Loss Reasons  │                                                 │
│  Dispositions  │                                                 │
│                │                                                 │
│ Conversations  │                                                 │
│  Sources       │                                                 │
│  Quick Replies │                                                 │
│  SLA Policies  │                                                 │
│                │                                                 │
│ Custom Fields  │                                                 │
│                │                                                 │
│ Assignment     │                                                 │
│  Rules         │                                                 │
│                │                                                 │
│ Workflows      │                                                 │
│                │                                                 │
│ Channels       │                                                 │
│                │                                                 │
│ Team           │                                                 │
│                │                                                 │
│ Notifications  │                                                 │
│                │                                                 │
│ Import/Export  │                                                 │
│                │                                                 │
├────────────────┴─────────────────────────────────────────────────┤
└──────────────────────────────────────────────────────────────────┘
```

Left sidebar: 240px fixed. Content area: flex. URL changes with each section (e.g., `/settings/pipelines`).

---

## Section: Workspace Profile

> URL: `/settings/workspace`

```
┌─────────────────────────────────────────────────────────────────┐
│ Workspace Profile                                    [Save]     │
├─────────────────────────────────────────────────────────────────┤
│ Workspace Name:   [Climate Naturals        ]                   │
│ Industry:         [Spices & Condiments  ▾]                     │
│ Country:          [India               ▾]                      │
│ Currency:         [INR (₹)             ▾]                      │
│ Date Format:      [DD/MM/YYYY          ▾]                      │
│ Time Zone:        [Asia/Kolkata        ▾]                      │
│ Monthly Target:   [₹5,00,000             ]                     │
│ Logo:             [Upload]  [current_logo.png]                 │
└─────────────────────────────────────────────────────────────────┘
```

- All fields saved to `crm_workspace_config` as JSON key-value
- Currency affects all monetary display formatting
- Monthly target used in dashboard revenue widget and forecast
- Logo displayed in app header

---

## Section: Working Hours

> URL: `/settings/working-hours`

```
┌─────────────────────────────────────────────────────────────────┐
│ Working Hours                                        [Save]     │
├─────────────────────────────────────────────────────────────────┤
│ □ Same hours every day                                          │
│                                                                  │
│ Monday      [✓]  [09:00 AM] — [06:00 PM]                      │
│ Tuesday     [✓]  [09:00 AM] — [06:00 PM]                      │
│ Wednesday   [✓]  [09:00 AM] — [06:00 PM]                      │
│ Thursday    [✓]  [09:00 AM] — [06:00 PM]                      │
│ Friday      [✓]  [09:00 AM] — [06:00 PM]                      │
│ Saturday    [✓]  [09:00 AM] — [02:00 PM]                      │
│ Sunday      [ ]  Closed                                         │
│                                                                  │
│ Holidays                                         [+ Add]        │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Jan 26 — Republic Day                          [Delete]  │   │
│ │ Aug 15 — Independence Day                      [Delete]  │   │
│ │ Oct 2  — Gandhi Jayanti                        [Delete]  │   │
│ └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

- Working hours affect: FRT calculation (business hours only), SLA policies, follow-up default times
- "Same hours every day" checkbox sets all enabled days to same time
- Holidays: date + label, excluded from business hour calculations

---

## Section: Pipelines

> URL: `/settings/pipelines`

```
┌─────────────────────────────────────────────────────────────────┐
│ Pipelines                                     [+ New Pipeline]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Sales Pipeline (Default)                    [Edit] [⋮]     │ │
│ │                                                             │ │
│ │ New → Contacted → Qualified → Proposal → Negotiation → Won │ │
│ │                                                      → Lost│ │
│ │                                                             │ │
│ │ 28 active opportunities                                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Support Pipeline                            [Edit] [⋮]     │ │
│ │                                                             │ │
│ │ Open → In Progress → Waiting → Resolved → Closed           │ │
│ │                                                             │ │
│ │ 5 active opportunities                                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Edit Pipeline

```
┌────────────────────────────────────────────────────┐
│ Edit Pipeline: Sales Pipeline                      │
│                                                    │
│ Name: [Sales Pipeline            ]                │
│ Entity Type: [Conversation       ▾]               │
│                                                    │
│ Stages (drag to reorder):                          │
│ ┌────────────────────────────────────────────────┐ │
│ │ ≡ New           Probability: [10%]  [Delete]  │ │
│ │ ≡ Contacted     Probability: [20%]  [Delete]  │ │
│ │ ≡ Qualified     Probability: [40%]  [Delete]  │ │
│ │ ≡ Proposal      Probability: [60%]  [Delete]  │ │
│ │ ≡ Negotiation   Probability: [80%]  [Delete]  │ │
│ │ ── Terminal Stages ──                          │ │
│ │ ✓ Won           Probability: [100%]            │ │
│ │ ✗ Lost          Probability: [0%]              │ │
│ └────────────────────────────────────────────────┘ │
│ [+ Add Stage]                                      │
│                                                    │
│ [Cancel]                              [Save]       │
└────────────────────────────────────────────────────┘
```

- Drag handle (≡) to reorder stages
- Probability: used for weighted forecast
- Terminal stages (Won/Lost) cannot be deleted or reordered
- Delete stage: only if 0 opportunities in that stage, else prompt to move them
- At least 1 non-terminal stage required

---

## Section: Loss Reasons

> URL: `/settings/loss-reasons`

```
┌─────────────────────────────────────────────────────────────────┐
│ Loss Reasons                                          [+ Add]   │
├─────────────────────────────────────────────────────────────────┤
│ ≡ Price too high                                     [Delete]  │
│ ≡ Competitor chosen                                  [Delete]  │
│ ≡ No budget                                          [Delete]  │
│ ≡ No response                                        [Delete]  │
│ ≡ Requirements changed                               [Delete]  │
│ ≡ Timeline mismatch                                  [Delete]  │
│ ≡ Other                                              [Delete]  │
└─────────────────────────────────────────────────────────────────┘
```

- Drag to reorder (display order in Close Lost dialog)
- Delete: soft delete, hidden from new selections, preserved in existing records
- Used in: Close Lost dialog, Unqualified Analysis report

---

## Section: Disposition Reasons

> URL: `/settings/dispositions`

Same layout as Loss Reasons. Used when marking a contact as "Unqualified":

- Wrong number, Not interested, Competitor customer, Budget constraints, etc.
- Configurable per workspace

---

## Section: Contact Sources

> URL: `/settings/sources`

```
┌─────────────────────────────────────────────────────────────────┐
│ Contact Sources                                       [+ Add]   │
├─────────────────────────────────────────────────────────────────┤
│ JustDial        Type: Lead Capture    Status: Active  [Edit]   │
│ Facebook Ads    Type: Lead Capture    Status: Active  [Edit]   │
│ IndiaMart       Type: Lead Capture    Status: Active  [Edit]   │
│ WhatsApp        Type: Channel         Status: Active  [Edit]   │
│ Direct Call     Type: Manual          Status: Active  [Edit]   │
│ Website         Type: Web Form        Status: Active  [Edit]   │
│ Referral        Type: Manual          Status: Active  [Edit]   │
└─────────────────────────────────────────────────────────────────┘
```

- Used in: filters, reports (source breakdown), lead attribution
- Type: categorization for reporting

---

## Section: Quick Replies

> URL: `/settings/quick-replies`

```
┌─────────────────────────────────────────────────────────────────┐
│ Quick Replies                                         [+ Add]   │
├─────────────────────────────────────────────────────────────────┤
│ Category: [All ▾]                                               │
│                                                                  │
│ Greeting                                                        │
│   "Hello! Thank you for reaching out to {{company}}..."  [Edit]│
│   "Good morning! How can I help you today?"              [Edit]│
│                                                                  │
│ Pricing                                                         │
│   "Our current price for {{product}} is..."              [Edit]│
│   "I'll send you a detailed quote shortly."              [Edit]│
│                                                                  │
│ Follow-up                                                       │
│   "Just following up on our previous conversation..."    [Edit]│
│   "Have you had a chance to review the quote?"           [Edit]│
└─────────────────────────────────────────────────────────────────┘
```

- Categories: workspace-defined groupings
- Template variables: `{{company}}`, `{{contact_name}}`, `{{agent_name}}`, `{{product}}`
- Used in: chat composer (quick reply button), outbound messages

---

## Section: SLA Policies

> URL: `/settings/sla`

```
┌─────────────────────────────────────────────────────────────────┐
│ SLA Policies                                         [Save]     │
├─────────────────────────────────────────────────────────────────┤
│ First Response Time (FRT)                                       │
│   Target:     [5] minutes                                       │
│   Warning at: [3] minutes                                       │
│   Escalate:   □ Notify manager when breached                   │
│                                                                  │
│ Response Time (ongoing)                                         │
│   Target:     [1] hour (business hours)                        │
│   Warning at: [45] minutes                                      │
│   Escalate:   □ Notify manager when breached                   │
│                                                                  │
│ Stage Aging Thresholds                                          │
│   Green:  [0-7] days                                            │
│   Amber:  [7-14] days                                           │
│   Red:    [>14] days                                            │
│                                                                  │
│ Conversation Idle Threshold                                     │
│   Mark idle after: [48] hours of no activity                    │
└─────────────────────────────────────────────────────────────────┘
```

- Affects: dashboard SLA widget, pipeline card colors, workflow triggers, reports
- Business hours: uses Working Hours config for calculations

---

## Section: Custom Fields

> URL: `/settings/custom-fields`

```
┌─────────────────────────────────────────────────────────────────┐
│ Custom Fields                                    [+ Add Field]  │
├─────────────────────────────────────────────────────────────────┤
│ Entity: [Contact ▾] [Account ▾] [Opportunity ▾]               │
│                                                                  │
│ Contact Fields:                                                 │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Distribution Type   Dropdown    Required  [Edit] [Del]   │   │
│ │ Business Category   Dropdown    Optional  [Edit] [Del]   │   │
│ │ Annual Volume        Number     Optional  [Edit] [Del]   │   │
│ │ Preferred Language   Text       Optional  [Edit] [Del]   │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│ Account Fields:                                                 │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Payment Terms       Dropdown    Required  [Edit] [Del]   │   │
│ │ Credit Limit        Number      Optional  [Edit] [Del]   │   │
│ └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Add/Edit Custom Field Dialog

```
┌────────────────────────────────────────┐
│ Add Custom Field                       │
│                                        │
│ Entity Type: [Contact        ▾]       │
│ Field Name:  [Distribution Type   ]   │
│ Field Key:   [distribution_type   ]   │
│ Type:        [Dropdown           ▾]  │
│                                        │
│ Options (for dropdown):                │
│ [Wholesale     ]  [×]                 │
│ [Retail        ]  [×]                 │
│ [Distributor   ]  [×]                 │
│ [+ Add Option]                         │
│                                        │
│ Required:    [✓]                      │
│ Show in list: [✓]                     │
│ Searchable:  [✓]                      │
│                                        │
│ [Cancel]                      [Save]  │
└────────────────────────────────────────┘
```

Field types: Text, Number, Dropdown, Multi-select, Date, Checkbox, URL, Email, Phone.

---

## Section: Assignment Rules

> URL: `/settings/assignment`

```
┌─────────────────────────────────────────────────────────────────┐
│ Assignment Rules                              [+ Add Rule]      │
├─────────────────────────────────────────────────────────────────┤
│ Rules are evaluated in priority order. First matching rule wins.│
│                                                                  │
│ Priority  Rule Name              Strategy        Status         │
│ 1         JustDial Leads         Source-based     Active  [Edit]│
│           Source = JustDial → Assign to Priya                   │
│                                                                  │
│ 2         Facebook Leads         Source-based     Active  [Edit]│
│           Source = Facebook → Assign to Ravi                    │
│                                                                  │
│ 3         Default Assignment     Round Robin      Active  [Edit]│
│           All remaining → Round robin among all agents          │
│                                                                  │
│ ── Fallback ──                                                  │
│ If no rule matches: [Move to unassigned queue ▾]               │
└─────────────────────────────────────────────────────────────────┘
```

### Edit Assignment Rule

```
┌────────────────────────────────────────────────────┐
│ Edit Rule: JustDial Leads                          │
│                                                    │
│ Name:     [JustDial Leads            ]            │
│ Priority: [1                         ]            │
│ Status:   [Active                   ▾]            │
│                                                    │
│ Conditions (all must match):                       │
│ [Source        ▾] [equals    ▾] [JustDial    ▾]  │
│ [+ Add Condition]                                  │
│                                                    │
│ Strategy: [Source-based (specific agent) ▾]       │
│                                                    │
│ Assign to: [Priya Sharma             ▾]          │
│                                                    │
│ [Cancel]                              [Save]       │
└────────────────────────────────────────────────────┘
```

Strategies:
- **Round Robin**: rotate among eligible agents
- **Load Balanced**: assign to agent with fewest open conversations
- **Source-based**: specific agent(s) per source
- **Manual**: move to unassigned queue

Conditions: Source, Channel, Contact field, Business hours (in/out), Agent availability.

---

## Section: Workflows

> URL: `/settings/workflows`

```
┌─────────────────────────────────────────────────────────────────┐
│ Workflow Rules                                [+ New Rule]      │
├─────────────────────────────────────────────────────────────────┤
│ Name                        Trigger               Status        │
│ Auto-create opportunity     Stage → Qualified     Active  [Edit]│
│ Idle conversation alert     Conversation idle     Active  [Edit]│
│ Welcome message             New conversation      Active  [Edit]│
│ Deal won notification       Opp → Won             Active  [Edit]│
│ Follow-up on no response    No reply 24hr         Paused  [Edit]│
└─────────────────────────────────────────────────────────────────┘
```

Click [Edit] or [+ New Rule] → opens workflow builder (see user flow 14-workflow-configuration.md for full builder spec).

---

## Section: Channels

> URL: `/settings/channels`

```
┌─────────────────────────────────────────────────────────────────┐
│ Channels                                      [+ Add Channel]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 💬 WhatsApp                        Status: Connected ✅    │ │
│ │ Business: Climate Naturals | Phone: +91 98765 43210       │ │
│ │ Messages today: 45 | Templates: 12                         │ │
│ │                                            [Configure]     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 📞 Voice (Smartflo)                Status: Connected ✅    │ │
│ │ Numbers: 2 | Agents mapped: 4                              │ │
│ │ Calls today: 18                                             │ │
│ │                                            [Configure]     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✉️ Email                           Status: Not configured  │ │
│ │                                            [Set Up]        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

- See user flow 15-channel-configuration.md for setup flows
- Health indicators: Connected/Disconnected/Error with last check time

---

## Section: Team

> URL: `/settings/team`

```
┌─────────────────────────────────────────────────────────────────┐
│ Team Members                                  [+ Add Member]    │
├─────────────────────────────────────────────────────────────────┤
│ Name              Role       Status    Conversations  Actions   │
│ Priya Sharma      Agent      Active    42 open        [⋮]      │
│ Ravi Kumar        Agent      Active    38 open        [⋮]      │
│ Ankit Patel       Agent      Active    35 open        [⋮]      │
│ Meera Joshi       Manager    Active    —              [⋮]      │
│ Admin User        Admin      Active    —              [⋮]      │
└─────────────────────────────────────────────────────────────────┘
```

### Member Actions (⋮ menu)

| Action | Behavior |
|--------|----------|
| Edit Role | Change CRM role (delegates to elauth) |
| View Activity | Navigate to agent activity report |
| Assignment History | View all assignments for this agent |
| Reassign All | Reassign all open conversations/opportunities (see flow 10) |
| Deactivate | Remove from workspace (with reassignment flow) |

### Add Member

```
┌────────────────────────────────────────┐
│ Add Team Member                        │
│                                        │
│ Search: [Search by email or name  ]   │
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Priya Sharma                       │ │
│ │ priya@example.com                  │ │
│ │ Already a member of this workspace │ │
│ ├────────────────────────────────────┤ │
│ │ Ravi Kumar                         │ │
│ │ ravi@example.com                   │ │
│ │ Member of: Other Workspace         │ │
│ │ [+ Add to this workspace]         │ │
│ └────────────────────────────────────┘ │
│                                        │
│ Or invite new:                         │
│ Email: [                          ]   │
│ Name:  [                          ]   │
│ Role:  [Agent                    ▾]  │
│                                        │
│ [Cancel]                      [Invite]│
└────────────────────────────────────────┘
```

- Search: queries elauth for existing persons
- Add existing: creates membership in workspace (via elauth)
- Invite new: creates person in elauth + sends invite email

---

## Section: Notifications

> URL: `/settings/notifications`

```
┌─────────────────────────────────────────────────────────────────┐
│ Notification Preferences                             [Save]     │
├─────────────────────────────────────────────────────────────────┤
│ These are workspace-wide defaults. Agents can override in      │
│ their personal settings.                                        │
│                                                                  │
│ Event                        In-App  Push   Email               │
│ New conversation assigned     [✓]    [✓]    [ ]                │
│ New message received          [✓]    [✓]    [ ]                │
│ Follow-up due                 [✓]    [✓]    [ ]                │
│ Follow-up overdue             [✓]    [✓]    [✓]               │
│ SLA breach                    [✓]    [✓]    [✓]               │
│ Opportunity stage changed     [✓]    [ ]    [ ]                │
│ Opportunity won               [✓]    [✓]    [✓]               │
│ Deal stuck alert              [✓]    [ ]    [✓]               │
│ Workflow action completed     [✓]    [ ]    [ ]                │
│ Agent mentioned in note       [✓]    [✓]    [ ]                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Section: Import/Export

> URL: `/settings/import-export`

```
┌─────────────────────────────────────────────────────────────────┐
│ Import / Export                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Import Contacts                                                 │
│ Upload a CSV or Excel file to import contacts.                  │
│ [Download Template]  [Upload File]                              │
│                                                                  │
│ Import History                                                  │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ Mar 10, 2026 — contacts.csv — 150 imported, 3 errors     │   │
│ │ Feb 28, 2026 — leads.xlsx — 80 imported, 0 errors        │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│ Export Data                                                      │
│ [Export Contacts]  [Export Opportunities]  [Export Activities]   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Import Flow

1. Download template CSV (with headers matching fields + custom fields)
2. Upload filled CSV
3. Column mapping screen: map CSV columns to CRM fields
4. Preview: show first 5 rows with mapped data
5. Import: async processing with progress bar
6. Result: X imported, Y skipped (duplicates), Z errors (with download of error rows)

---

## State Management

| State | Source | Cache |
|-------|--------|-------|
| Workspace config | CRM API | React Query, 10min stale |
| Pipeline stages | CRM API | React Query, 10min stale |
| Team members | elauth via CRM | React Query, 5min stale |
| Custom fields | CRM API | React Query, 10min stale |
| Assignment rules | CRM API | React Query, 10min stale |
| Workflow rules | CRM API | React Query, 5min stale |
| Channels | CRM API | React Query, 2min stale |

All settings mutations invalidate the relevant cache key on success.

---

## API Endpoints

| Section | Method | Endpoint |
|---------|--------|----------|
| Workspace profile | GET/PUT | `/settings/workspace` |
| Working hours | GET/PUT | `/settings/working-hours` |
| Holidays | GET/POST/DELETE | `/settings/holidays` |
| Pipelines | GET/POST | `/pipelines` |
| Pipeline detail | GET/PUT/DELETE | `/pipelines/:id` |
| Pipeline stages | GET/POST/PUT/DELETE | `/pipelines/:id/stages` |
| Loss reasons | GET/POST/PUT/DELETE | `/settings/loss-reasons` |
| Dispositions | GET/POST/PUT/DELETE | `/settings/dispositions` |
| Contact sources | GET/POST/PUT/DELETE | `/settings/sources` |
| Quick replies | GET/POST/PUT/DELETE | `/settings/quick-replies` |
| SLA policies | GET/PUT | `/settings/sla` |
| Custom fields | GET/POST/PUT/DELETE | `/settings/custom-fields` |
| Assignment rules | GET/POST/PUT/DELETE | `/settings/assignment-rules` |
| Workflow rules | GET/POST/PUT/DELETE | `/settings/workflows` |
| Channels | GET/POST/PUT | `/settings/channels` |
| Team members | GET | `/settings/team` |
| Add member | POST | `/settings/team` |
| Update member role | PUT | `/settings/team/:personId` |
| Deactivate member | DELETE | `/settings/team/:personId` |
| Notification defaults | GET/PUT | `/settings/notifications` |
| Import | POST | `/imports` |
| Import status | GET | `/imports/:id` |
| Export | POST | `/exports` |

---

## Permissions

| Section | Manager | Admin |
|---------|---------|-------|
| Workspace Profile | View | Edit |
| Working Hours | View | Edit |
| Pipelines | View | Edit |
| Loss Reasons | View | Edit |
| Dispositions | View | Edit |
| Sources | View | Edit |
| Quick Replies | Edit | Edit |
| SLA Policies | View | Edit |
| Custom Fields | View | Edit |
| Assignment Rules | View | Edit |
| Workflows | View | Edit |
| Channels | View | Edit |
| Team | View | Edit |
| Notifications | Edit (own) | Edit (all) |
| Import/Export | — | Full access |
