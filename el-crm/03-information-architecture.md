# Information Architecture

> Navigation structure, page hierarchy, URL patterns, and sidebar layout.

---

## 1. Navigation Model

el-CRM uses a **sidebar-based navigation** built on `@elsapiens/layout` AppShell. The sidebar is persistent across all pages. A top header bar contains workspace switcher, global search, notifications, and user menu.

---

## 2. App Shell Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ HEADER                                                            │
│ [≡] [WorkspaceName ▾]    [🔍 Search... (Ctrl+K)]    [🔔 3] [👤] │
├────────┬─────────────────────────────────────────────────────────┤
│ SIDEBAR│ MAIN CONTENT AREA                                       │
│        │                                                         │
│ 📥 Inbox │                                                       │
│ 👥 Contacts│                                                     │
│ 🏢 Accounts│                                                     │
│ 📊 Pipeline│                                                     │
│ ✅ Follow-ups│                                                   │
│ 📈 Reports  │                                                    │
│ ──────── │                                                       │
│ ⚙ Settings │                                                    │
│        │                                                         │
│        │                                                         │
│        │                                                         │
│ [?]    │                                                         │
│ [v1.0] │                                                         │
├────────┴─────────────────────────────────────────────────────────┤
│ (Footer/status bar — optional)                                    │
└──────────────────────────────────────────────────────────────────┘
```

### Header Components
| Element | Component | Source |
|---------|-----------|--------|
| Hamburger (mobile) | `@elsapiens/layout` | Toggles sidebar |
| Workspace switcher | `@elsapiens/shell` OrgSwitcher | Switch workspace context |
| Global search | Custom CRM component | Search conversations, contacts, accounts |
| Notification bell | Custom CRM component | Notification center panel |
| User avatar/menu | `@elsapiens/shell` UserMenu | Profile, preferences, logout |

### Sidebar Items (Role-Dependent)

| Item | Icon | URL | Agent | Manager | Admin |
|------|------|-----|-------|---------|-------|
| Inbox | inbox | `/inbox` | Yes | Yes | Yes |
| Contacts | users | `/contacts` | Yes | Yes | Yes |
| Accounts | building | `/accounts` | Yes | Yes | Yes |
| Pipeline | kanban | `/pipeline` | Yes | Yes | Yes |
| Follow-ups | calendar-check | `/follow-ups` | Yes | Yes | Yes |
| Dashboard | chart-bar | `/dashboard` | No | Yes | Yes |
| Reports | bar-chart-2 | `/reports` | Limited | Yes | Yes |
| Settings | gear | `/settings` | No | No | Yes |

**Agent sidebar**: Inbox is first and highlighted. No Dashboard or Settings.
**Manager sidebar**: Dashboard is home. Full reports access.
**Admin sidebar**: Same as Manager + Settings.

---

## 3. URL Structure

### Core Pages

```
/                           → Redirect to /inbox (agent) or /dashboard (manager)
/inbox                      → Inbox (conversation list + chat + details)
/inbox/:conversationId      → Inbox with specific conversation selected
/contacts                   → Contact list
/contacts/:personId         → Contact detail page
/accounts                   → Account list
/accounts/:entityId         → Account detail page
/pipeline                   → Pipeline board (default pipeline)
/pipeline/:pipelineId       → Specific pipeline board
/follow-ups                 → Follow-up list (my follow-ups)
/dashboard                  → Manager dashboard
/reports                    → Reports index
/reports/frt                → First Response Time report
/reports/funnel             → Sales Funnel report
/reports/aging              → Aging report
/reports/activity           → Agent Activity report
/reports/outcome            → Outcome report
/reports/revenue            → Revenue Contribution report
/reports/unqualified        → Unqualified Analysis report
/reports/trend              → Conversation Trend report
```

### Settings Pages

```
/settings                       → Settings index (redirect to general)
/settings/general               → Workspace profile, business hours
/settings/pipelines             → Pipeline & stage configuration
/settings/pipelines/:id         → Edit specific pipeline
/settings/custom-fields         → Custom field definitions
/settings/sources               → Contact sources
/settings/dispositions          → Disposition & loss reasons
/settings/assignment            → Assignment rules
/settings/sla                   → SLA policies
/settings/channels              → Channel overview
/settings/channels/whatsapp     → WhatsApp configuration
/settings/channels/voice        → Voice configuration
/settings/channels/email        → Email configuration
/settings/channels/leads        → Lead capture configuration
/settings/workflows             → Workflow rules list
/settings/workflows/:id         → Edit workflow rule
/settings/workflows/new         → Create workflow rule
/settings/templates             → Message templates
/settings/team                  → Team member management
/settings/import-export         → Data import/export
```

---

## 4. Page Hierarchy

```
el-CRM
├── Inbox (/inbox)
│   ├── Conversation List (panel 1)
│   ├── Chat Thread (panel 2)
│   └── Contact Details (panel 3)
│       ├── Info tab
│       ├── Activities tab
│       ├── Follow-ups tab
│       ├── Opportunities tab
│       ├── Notes tab
│       └── History tab
│
├── Contacts (/contacts)
│   ├── Contact List (table view)
│   └── Contact Detail (/contacts/:id)
│       ├── Overview section
│       ├── Conversations section
│       ├── Opportunities section
│       ├── Activities section
│       └── Custom Fields section
│
├── Accounts (/accounts)
│   ├── Account List (table view)
│   └── Account Detail (/accounts/:id)
│       ├── Company Info section
│       ├── Contacts section (linked contacts)
│       ├── Opportunities section
│       └── Activities section
│
├── Pipeline (/pipeline)
│   ├── Kanban View (default)
│   ├── List View
│   ├── Forecast View
│   └── Opportunity Detail (slide-over)
│
├── Follow-ups (/follow-ups)
│   ├── Overdue section
│   ├── Today section
│   └── Upcoming section
│
├── Dashboard (/dashboard) — Manager/Admin only
│   ├── Pipeline Summary widget
│   ├── Team Activity widget
│   ├── Conversion Funnel widget
│   ├── FRT Overview widget
│   └── SLA Status widget
│
├── Reports (/reports)
│   ├── FRT Report (/reports/frt)
│   ├── Sales Funnel (/reports/funnel)
│   ├── Aging Report (/reports/aging)
│   ├── Agent Activity (/reports/activity)
│   ├── Outcome Report (/reports/outcome)
│   ├── Revenue Contribution (/reports/revenue)
│   ├── Unqualified Analysis (/reports/unqualified)
│   └── Conversation Trend (/reports/trend)
│
└── Settings (/settings) — Admin only
    ├── General
    ├── Pipelines
    ├── Custom Fields
    ├── Sources
    ├── Dispositions
    ├── Assignment Rules
    ├── SLA Policies
    ├── Channels
    │   ├── WhatsApp
    │   ├── Voice
    │   ├── Email
    │   └── Lead Capture
    ├── Workflows
    ├── Templates
    ├── Team
    └── Import/Export
```

---

## 5. Responsive Behavior

| Breakpoint | Behavior |
|------------|----------|
| Desktop (≥1280px) | Full layout: sidebar + all three inbox panels visible |
| Laptop (1024-1279px) | Sidebar collapsible to icons. Inbox: list + chat (details as slide-over) |
| Tablet (768-1023px) | Sidebar hidden (hamburger). Inbox: list or chat (toggle). Details as modal |
| Mobile (<768px) | Sidebar as overlay drawer. Single panel view. Bottom navigation for key items |

### Inbox Responsive Behavior

```
Desktop: [List] [Chat] [Details]     — all three visible
Laptop:  [List] [Chat] [Details→]    — details on demand (slide-over)
Tablet:  [List] ↔ [Chat] [Details↓]  — toggle between list and chat
Mobile:  [List] → [Chat] → [Details] — stack navigation (back buttons)
```

---

## 6. Deep Linking

All pages support direct URL access:
- `/inbox/conv_abc123` → Opens inbox with that conversation selected
- `/contacts/person_xyz` → Opens contact detail
- `/pipeline/pipe_1?stage=proposal` → Opens pipeline filtered to proposal stage
- `/reports/frt?preset=last_30_days&agent=user_5` → Opens FRT report with filters applied

Notification links use deep URLs: clicking a notification navigates to the relevant page with context.

---

## 7. State Management

| State Type | Storage | Pattern |
|------------|---------|---------|
| Auth tokens | localStorage | Managed by elsdk AuthProvider |
| Workspace context | React Context | OrganizationProvider from elsdk |
| Server data (conversations, contacts) | React Query cache | TanStack Query with stale-while-revalidate |
| UI state (selected conversation, filter selections) | URL params + React state | URL for shareable state, React for ephemeral |
| User preferences (saved filters, notification settings) | Server (CRM API) | Loaded on login, cached in React Query |
| Real-time updates | WebSocket → React Query cache invalidation | WS events trigger query refetch |
