# Page Spec: Follow-Ups

> URL: `/follow-ups`
> Role: Agent (own), Manager (team), Admin (all)
> Data source: CRM (followups, conversations, contacts via accounts-api cache)

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Follow-Ups                               [+ New Follow-Up]     │
│ [Today] [Overdue] [Upcoming] [Completed]                        │
│ Agent: [All ▾]  Type: [All ▾]  [🔍 Search]                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ OVERDUE (3)                                              ⚠      │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ ☐ Call Rajesh Kumar — Acme Corp           Mar 10 (2d ago) │  │
│ │   Agent: Priya  |  Re: Pricing discussion                 │  │
│ ├────────────────────────────────────────────────────────────┤  │
│ │ ☐ Email GreenFoods — Follow up on quote    Mar 8 (4d ago) │  │
│ │   Agent: Priya  |  Re: Q2 bulk order                      │  │
│ ├────────────────────────────────────────────────────────────┤  │
│ │ ☐ WhatsApp Sneha Patel — TechParts        Mar 9 (3d ago)  │  │
│ │   Agent: Ravi  |  Re: Sample delivery                     │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│ TODAY (5)                                                        │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ ☐ Call Amit Shah — BuildRight              10:00 AM       │  │
│ │   Agent: Ravi  |  Re: Contract renewal                    │  │
│ ├────────────────────────────────────────────────────────────┤  │
│ │ ☐ WhatsApp Vivek Joshi                     2:00 PM        │  │
│ │   Agent: Ankit  |  Re: Product demo                       │  │
│ │ ...                                                        │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│ UPCOMING                                                         │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ Mar 13 (Tomorrow)                                          │  │
│ │ ☐ Call Rajesh Kumar — pricing follow-up         9:00 AM   │  │
│ │ ☐ Email TechParts — send revised quote         11:00 AM   │  │
│ ├────────────────────────────────────────────────────────────┤  │
│ │ Mar 14 (Friday)                                            │  │
│ │ ☐ WhatsApp GreenFoods — order confirmation     10:00 AM   │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│                                  Page 1 of 2  [< 1 2 >]        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Tab Bar

| Tab | Filter | Badge |
|-----|--------|-------|
| Today | `scheduled_at` = today AND `status` = pending | Count |
| Overdue | `scheduled_at` < today AND `status` = pending | Count (red) |
| Upcoming | `scheduled_at` > today AND `status` = pending | Count |
| Completed | `status` IN (completed, skipped) | — |

Default tab: **Today** (or **Overdue** if overdue count > 0).

---

## Filters

| Filter | Options | Default |
|--------|---------|---------|
| Agent | All, specific agent | All (Manager/Admin), own (Agent) |
| Type | All, Call, WhatsApp, Email, Visit, Other | All |
| Search | Contact name, account name | — |

Agent role always sees only own follow-ups (server-enforced).

---

## Follow-Up Row

Each row displays:

| Element | Source | Display |
|---------|--------|---------|
| Checkbox | — | Mark as completed |
| Type icon | `followups.followup_type` | 📞 Call, 💬 WhatsApp, ✉️ Email, 🏢 Visit |
| Contact name | accounts-api (cached) | Bold, clickable → `/contacts/:id` |
| Account name | accounts-api (cached) | Muted text |
| Description | `followups.description` | Truncated to 1 line |
| Agent name | elauth (cached) | Shown for Manager/Admin only |
| Scheduled time | `followups.scheduled_at` | Time for today, date for others |
| Overdue indicator | Computed | Red text "2d ago" for overdue |

### Row Actions (on hover or ⋮ menu)

| Action | Behavior |
|--------|----------|
| Complete | Mark as completed, optionally add outcome note |
| Snooze | Reschedule: +1hr, +4hr, Tomorrow, Next Week, Custom date/time |
| Skip | Mark as skipped with reason |
| Edit | Edit description, time, type |
| Open Conversation | Navigate to related conversation in Inbox |
| Delete | Delete follow-up (confirmation required) |

---

## Complete Follow-Up Dialog

```
┌────────────────────────────────────────┐
│ Complete Follow-Up                     │
│                                        │
│ 📞 Call Rajesh Kumar — Acme Corp      │
│                                        │
│ Outcome:                               │
│ [Discussed pricing, agreed on ₹200/kg │
│  for 500kg order. Will send formal    │
│  quote by tomorrow.                ]  │
│                                        │
│ Next Action:                           │
│ ○ No further action                    │
│ ● Create new follow-up                │
│   Type: [Email           ▾]          │
│   Date: [Mar 13, 2026   📅]          │
│   Time: [10:00 AM        ▾]          │
│   Desc: [Send formal quote      ]    │
│                                        │
│ [Cancel]                   [Complete] │
└────────────────────────────────────────┘
```

- Outcome note saved as activity on the conversation
- "Create new follow-up" immediately creates a chained follow-up

---

## Snooze Options

```
┌────────────────────────────┐
│ Snooze Follow-Up           │
│                            │
│ ○ +1 hour (11:00 AM)      │
│ ○ +4 hours (2:00 PM)      │
│ ○ Tomorrow 9:00 AM        │
│ ○ Next Monday 9:00 AM     │
│ ○ Custom:                  │
│   [Mar 15, 2026  📅]      │
│   [10:00 AM       ▾]      │
│                            │
│ [Cancel]        [Snooze]   │
└────────────────────────────┘
```

---

## New Follow-Up Dialog

```
┌────────────────────────────────────────┐
│ New Follow-Up                          │
│                                        │
│ Contact:  [Search contact...      ▾]  │
│ Type:     [Call                   ▾]  │
│ Date:     [Mar 13, 2026         📅]  │
│ Time:     [10:00 AM              ▾]  │
│                                        │
│ Description:                           │
│ [Follow up on pricing discussion  ]   │
│                                        │
│ Conversation: [Auto-detect       ▾]  │
│   Links to latest open conversation   │
│                                        │
│ Assign to: [Self                 ▾]  │
│   (Manager/Admin can assign to others)│
│                                        │
│ [Cancel]                      [Create]│
└────────────────────────────────────────┘
```

- Contact search via accounts-api
- Conversation auto-detects latest open conversation for that contact
- Time defaults to next business hour (per workspace working_hours)

---

## Bulk Actions

Select multiple follow-ups via checkboxes:

```
┌──────────────────────────────────────────────────┐
│ 5 follow-ups selected                             │
│ [Complete All] [Snooze All] [Reassign] [Delete]  │
└──────────────────────────────────────────────────┘
```

- Complete All: marks all as completed (no individual outcome notes)
- Snooze All: same snooze options applied to all
- Reassign: Manager/Admin only, select target agent

---

## State Management

| State | Source | Cache |
|-------|--------|-------|
| Follow-up list | CRM API | React Query, 30s stale |
| Tab counts | CRM API | React Query, 30s stale |
| Contact names | accounts-api cache | React Query, 5min stale |

- Checkbox completion uses optimistic update
- WebSocket event `followup.due` triggers badge update in sidebar

---

## API Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| List follow-ups | GET | `/follow-ups?status=pending&tab=today&agent_id=` |
| Get counts | GET | `/follow-ups/counts` |
| Create follow-up | POST | `/follow-ups` |
| Update follow-up | PUT | `/follow-ups/:id` |
| Complete | POST | `/follow-ups/:id/complete` |
| Snooze | POST | `/follow-ups/:id/snooze` |
| Skip | POST | `/follow-ups/:id/skip` |
| Delete | DELETE | `/follow-ups/:id` |
| Bulk complete | POST | `/follow-ups/bulk/complete` |
| Bulk snooze | POST | `/follow-ups/bulk/snooze` |
| Bulk reassign | POST | `/follow-ups/bulk/reassign` |

---

## Sidebar Badge

The sidebar "Follow-Ups" item shows a badge:
- Red badge with count if overdue > 0
- Blue badge with count if today > 0 and overdue = 0
- No badge if no pending today/overdue

Updated via WebSocket push from server-side cron that checks follow-up due times.
