# Page Spec: Inbox

> URL: `/inbox` and `/inbox/:conversationId`
> Role: All (home screen for agents)
> This is the most important page in el-CRM.

---

## Layout

Three-panel layout occupying the full content area (sidebar excluded).

```
┌──────────────────────────────────────────────────────────────────────────┐
│ PANEL 1: Conversation List   │ PANEL 2: Chat Thread    │ PANEL 3: Details│
│ Width: 300px (fixed)         │ Width: flex (fills)      │ Width: 360px    │
│                              │                          │                 │
│ ┌──────────────────────────┐ │ ┌──────────────────────┐ │ ┌─────────────┐│
│ │ Filter Bar               │ │ │ Conversation Header  │ │ │Contact Info ││
│ │ [All▾] [🔍 search]      │ │ │ Name | Stage | Agent │ │ │Name, Phone  ││
│ └──────────────────────────┘ │ └──────────────────────┘ │ │Email, Acct  ││
│ ┌──────────────────────────┐ │                          │ │Source, Agent││
│ │ Quick Filter Tabs        │ │ ┌──────────────────────┐ │ │Stage        ││
│ │ [Mine][Unread][Unassigned]│ │ │                      │ │ │Custom Fields││
│ └──────────────────────────┘ │ │  Message Thread       │ │ └─────────────┘│
│                              │ │  (scrollable)         │ │                │
│ ┌──────────────────────────┐ │ │                      │ │ ┌─────────────┐│
│ │ Conversation Item        │ │ │  📱 Customer 10:30   │ │ │Tab Bar      ││
│ │ ● Rahul Verma     2m    │ │ │  "Need pricing..."   │ │ │[Activities] ││
│ │   Can you share the...  │ │ │                      │ │ │[Follow-ups] ││
│ │   WhatsApp ● New        │ │ │  👤 Agent 10:32      │ │ │[Opportunities││
│ ├──────────────────────────┤ │ │  "Sure! What grade?" │ │ │[Notes]      ││
│ │ Conversation Item        │ │ │                      │ │ │[History]    ││
│ │   Ankit Shah       15m  │ │ │  📱 Customer 10:35   │ │ └─────────────┘│
│ │   Thanks for the...     │ │ │  "Grade A turmeric"  │ │                │
│ │   Email ● Qualified     │ │ │                      │ │ ┌─────────────┐│
│ ├──────────────────────────┤ │ └──────────────────────┘ │ │Tab Content  ││
│ │ Conversation Item        │ │                          │ │(scrollable) ││
│ │   Priya M          1h   │ │ ┌──────────────────────┐ │ │             ││
│ │   I'll check and...     │ │ │ Message Composer      │ │ │ Activity 1  ││
│ │   Voice ● Opportunity   │ │ │ [📎][📋][Ch:WA▾]    │ │ │ Activity 2  ││
│ ├──────────────────────────┤ │ │ Type a message...    │ │ │ Activity 3  ││
│ │ ...more conversations    │ │ │            [Send ➤]  │ │ │ ...         ││
│ │                          │ │ └──────────────────────┘ │ │             ││
│ └──────────────────────────┘ │                          │ └─────────────┘│
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Panel 1: Conversation List

### Components

**Filter Bar** (top of panel):
- Dropdown: Status filter (All, Open, Pending, Closed)
- Search input: searches contact name, phone, message text
- Advanced filter button → expands filter panel

**Quick Filter Tabs**:
- Mine | Unread | Unassigned | Due Follow-ups
- Active tab highlighted, counts shown: "Unread (5)"
- Manager/Admin sees additional: "All" tab

**Conversation Items** (scrollable list):
Each item is a card showing:
```
┌──────────────────────────────────┐
│ ● Rahul Verma              2m  │  ← Unread dot + contact name + time since last message
│   Can you share the quote...   │  ← Last message preview (truncated to 1 line)
│   📱 WhatsApp  ● New          │  ← Channel icon + stage badge
│   [SLA: ⚠ 3m]                 │  ← SLA indicator (if applicable)
└──────────────────────────────────┘
```

- **Selected state**: highlighted background
- **Unread**: bold name + blue dot
- **SLA states**: green (OK), amber (warning), red (breached)
- **Sorting**: configurable (newest message, oldest unanswered, priority)
- **Infinite scroll**: loads more conversations as user scrolls down
- **Empty state**: "No conversations match your filters" with suggestion to adjust

### Data Loading
- Initial load: 25 conversations, sorted by last message time
- Pagination: infinite scroll, loads 25 more
- Real-time: WebSocket pushes update conversation positions and badges
- Stale data: React Query refetch on window focus

---

## Panel 2: Chat Thread

### Conversation Header
```
┌──────────────────────────────────────────────────────────┐
│ Rahul Verma                                    [⋮ More] │
│ Stage: Qualified ▾  |  Agent: Priya  |  WhatsApp 📱     │
│ Source: JustDial  |  Priority: Normal ▾                  │
└──────────────────────────────────────────────────────────┘
```

- Contact name (clickable → opens contact detail page)
- Stage quick-change dropdown
- Assigned agent (clickable → transfer dialog)
- Active channel indicator
- [More] menu: Close conversation, Transfer, Change source, Mark as spam

### Message Thread (scrollable, auto-scrolls to bottom)

**Message types and rendering:**

| Message Type | Rendering |
|-------------|-----------|
| Text (customer) | Left-aligned bubble, channel icon, timestamp |
| Text (agent) | Right-aligned bubble, "You" or agent name, timestamp, delivery status |
| Image | Thumbnail in bubble, click to full-screen |
| Video | Thumbnail with play button |
| Document | File icon + filename, click to download |
| Audio | Audio player widget |
| Template | Special styling: template name, body with filled variables |
| Call event | Center-aligned card: "📞 Outbound call - 4m 32s" + recording link |
| Lead capture | Center-aligned structured card with lead data fields |
| Email | Email-style rendering: subject line, HTML body, attachment list |
| Stage change | Center-aligned system message: "Stage changed: New → Contacted" |
| Assignment | Center-aligned system message: "Assigned to Priya" |
| Internal note | Yellow background bubble, "📝 Internal Note" label, not sent to customer |

**Delivery status icons** (on agent messages):
- 🕐 Sending
- ✓ Sent
- ✓✓ Delivered
- ✓✓ (blue) Read
- ⚠ Failed (with retry button)

**Date separators**: "Today", "Yesterday", "March 10, 2026" between messages from different days.

**Load more**: "Load older messages ↑" at top of thread. Loads 50 at a time.

### Message Composer

```
┌──────────────────────────────────────────────────────────┐
│ [📎 Attach] [📋 Template] [💬 Quick Reply] [Ch: WA ▾]  │
├──────────────────────────────────────────────────────────┤
│ Type a message...                                        │
│                                                   [Send] │
└──────────────────────────────────────────────────────────┘
```

- **Text input**: Multi-line, auto-expand, Shift+Enter for newline, Enter or Ctrl+Enter to send (configurable)
- **Attach**: File picker + drag & drop zone
- **Template**: Opens template picker modal (WhatsApp templates)
- **Quick Reply**: Autocomplete triggered by typing `/` followed by shortcut
- **Channel selector**: Dropdown showing available channels for this contact. Default = channel of last inbound message.
- **Send button**: Disabled when empty. Shows loading spinner while sending.
- **WhatsApp 24h warning**: If session expired, show banner: "Session expired. Use a template to message." Disable free-form input.
- **Email mode**: When email channel selected, composer expands with Subject field and rich text toolbar.

---

## Panel 3: Contact Details

### Contact Info Section (top, always visible)

```
┌─────────────────────────────────────┐
│ Rahul Verma              [✏ Edit]  │
│ 📞 +91 98765 43210 [📞][💬]       │
│ 📧 rahul@acme.com  [📧]           │
│ 🏢 Acme Corp Pvt Ltd              │
│ 💼 Procurement Manager            │
│ 📍 Mumbai, Maharashtra             │
│                                     │
│ Stage: Qualified  ▾                 │
│ Source: JustDial                    │
│ Agent: Priya Sharma                 │
│ Created: Mar 1, 2026               │
│                                     │
│ Custom Fields:                      │
│ Business Type: Trader               │
│ Monthly Volume: 500 kg              │
│ Product Interest: Grade A Turmeric  │
│                                     │
│ [+ Add Handle] [🔀 Transfer]       │
│ [+ Create Opportunity]              │
│ [+ Create Follow-up]               │
│ [📝 Add Note]                      │
└─────────────────────────────────────┘
```

- Phone/email clickable → initiates call/message on that channel
- Edit opens inline editing or modal
- All contact CRUD delegates to accounts-api via CRM backend

### Tab Bar

| Tab | Content |
|-----|---------|
| Activities | Chronological activity timeline: calls, notes, stage changes, messages sent, assignments |
| Follow-ups | List of follow-ups: overdue (red), due today, upcoming. + Create new. Mark complete. |
| Opportunities | Linked opportunities: name, pipeline, stage, value, close date. + Create new. Click to open detail. |
| Notes | Free-form notes list. + Add note (rich text). Most recent first. |
| History | Past closed conversations with this contact. Click to view in read-only thread. |

---

## State Management

| State | Source | Update Mechanism |
|-------|--------|-----------------|
| Conversation list | GET /conversations?filters | React Query, refetch on filter change |
| Selected conversation | URL param :conversationId | React Router, updates on click |
| Messages | GET /conversations/:id/messages | React Query, WS pushes new messages |
| Contact details | GET /contacts/:personId | React Query (calls CRM API which calls accounts-api) |
| Activities | GET /activities?entity=conversation&id=:id | React Query |
| Follow-ups | GET /followups?conversation_id=:id | React Query |
| Opportunities | GET /opportunities?person_id=:pid | React Query |
| Real-time updates | WebSocket subscription | WS events → React Query cache invalidation |
| Filters | URL search params | Shareable URLs, React state for UI |
| Composer draft | Local React state | Lost on navigation (deliberate — no draft persistence v1) |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+K | Global search |
| ↑/↓ | Navigate conversation list |
| Enter | Select conversation / Send message (configurable) |
| Ctrl+Enter | Send message (alternative) |
| Shift+Enter | New line in composer |
| Ctrl+Shift+N | New internal note |
| Escape | Close modals/panels |
| / | Trigger quick reply autocomplete (when composer focused) |

---

## Responsive: Tablet/Mobile

**Tablet (768-1023px)**: Two panels visible — conversation list OR chat thread. Toggle between them. Details as slide-over.

**Mobile (<768px)**: Single panel. Conversation list → tap → chat thread (with back button) → tap contact → details (full screen). Bottom tabs: Inbox, Contacts, Pipeline, More.
