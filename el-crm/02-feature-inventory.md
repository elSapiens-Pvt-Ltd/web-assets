# Feature Inventory

> Complete feature checklist by module.
> Status: [Core] = must-have for launch, [Enhanced] = post-launch, [Future] = roadmap

---

## 1. Inbox (Omnichannel Conversation Hub)

### Conversation List
- [Core] Three-panel layout: conversation list, chat thread, contact details
- [Core] Real-time conversation updates via WebSocket
- [Core] Unread message badges and conversation count
- [Core] Conversation status indicators: open, pending, closed
- [Core] Channel icon per conversation (WhatsApp, voice, email, lead)
- [Core] SLA status indicators: within SLA, warning (amber), breached (red)
- [Core] Sort: newest message, oldest unanswered, priority, SLA status
- [Core] Quick filters: Mine, Unread, Open, Unassigned, Due Follow-ups
- [Core] Advanced filters: stage, channel, source, agent, priority, date range, tags
- [Core] Saved filters (per-user)
- [Enhanced] Shared team filters (manager creates, visible to all)
- [Enhanced] Conversation snooze (hide until date/time)
- [Future] Smart prioritization (ML-based urgency scoring)

### Chat Thread
- [Core] Full message history with timestamps and delivery status
- [Core] Channel indicator per message (multi-channel conversations)
- [Core] Text message sending and receiving
- [Core] Media messages: images, videos, documents, audio
- [Core] File attachment upload (drag & drop + browse)
- [Core] WhatsApp template message picker and variable filling
- [Core] Message delivery status: sending, sent, delivered, read, failed
- [Core] Failed message retry
- [Core] Call event cards in timeline (inbound/outbound, duration, recording link)
- [Core] Lead capture cards (structured data from JustDial/Facebook/etc.)
- [Core] Email message rendering (HTML body, attachments, subject)
- [Enhanced] Quick replies / canned responses (workspace-configurable)
- [Enhanced] Message scheduling (send later)
- [Enhanced] Internal notes in conversation (visible to agents only, not sent to customer)
- [Enhanced] @mention other agents in internal notes
- [Enhanced] Typing indicators (for WhatsApp)
- [Future] AI-suggested replies
- [Future] Message translation

### Contact Details Panel
- [Core] Contact info: name, phone(s), email(s), account, designation
- [Core] Edit contact inline (delegates to accounts-api)
- [Core] Current stage display and quick-change
- [Core] Source and channel info
- [Core] Assigned agent with transfer action
- [Core] Activities tab: activity timeline (calls, notes, stage changes)
- [Core] Follow-ups tab: list with status, create new
- [Core] Opportunities tab: linked opportunities with stage and value
- [Core] Notes tab: free-form notes
- [Core] Contact handles list (all phone/email/social handles)
- [Core] Custom fields display and edit
- [Enhanced] Conversation history tab (all past conversations, including closed)
- [Enhanced] Related contacts (same account)
- [Future] Customer sentiment score
- [Future] Communication preferences (preferred channel, do-not-contact)

---

## 2. Contacts & Accounts

### Contact Management
- [Core] Contact list view with search and filters
- [Core] Contact detail page
- [Core] Create contact (delegates to accounts-api)
- [Core] Edit contact fields
- [Core] Multiple handles per contact (phone, email, social)
- [Core] Add/remove contact handles
- [Core] Link contact to account (entity)
- [Core] Lifecycle stages: Lead, Customer, Inactive
- [Core] Contact source tracking
- [Core] Custom fields on contacts
- [Core] Assigned agent per contact
- [Enhanced] Merge duplicate contacts (same person, multiple records)
- [Enhanced] Contact import from CSV
- [Enhanced] Contact export to CSV/Excel
- [Enhanced] Bulk actions: assign, change stage, tag, delete
- [Future] Contact scoring (engagement-based)
- [Future] Duplicate detection (automatic, fuzzy matching)

### Account (Company) Management
- [Core] Account list view with search and filters
- [Core] Account detail page: company info, linked contacts, opportunities
- [Core] Create account (delegates to accounts-api)
- [Core] Edit account fields
- [Core] Link contacts to account
- [Core] Custom fields on accounts
- [Enhanced] Account hierarchy (parent/child companies)
- [Enhanced] Merge duplicate accounts
- [Enhanced] Account-level activity summary (across all contacts)
- [Future] Account health score

---

## 3. Pipeline & Opportunities

### Pipeline Board (Kanban)
- [Core] Visual kanban board with drag-and-drop
- [Core] Multiple pipelines per workspace
- [Core] Configurable stages per pipeline
- [Core] Opportunity cards: contact name, value, agent, close date, age
- [Core] Column totals (count + value)
- [Core] Stage probability weights and weighted pipeline value
- [Core] Filter by agent, date range, source, value
- [Core] Close won: amount, date, notes, link order
- [Core] Close lost: reason (workspace-configured), competitor, notes
- [Enhanced] Pipeline list view (table format, sortable)
- [Enhanced] Pipeline forecast view (grouped by close month, weighted values)
- [Enhanced] Age indicators on cards (color-coded by time in stage)
- [Enhanced] Required fields per stage (block progression without)
- [Enhanced] Stage-entry actions (auto-notifications, auto-follow-ups)
- [Future] Deal rotting alerts (automatic based on inactivity)
- [Future] Win probability prediction (ML-based)

### Opportunity Management
- [Core] Create opportunity (from conversation or standalone)
- [Core] Edit opportunity: value, close date, pipeline, stage, notes
- [Core] Link opportunity to contact and account
- [Core] Opportunity detail slide-over/modal
- [Core] Transfer opportunity to another agent
- [Core] Custom fields on opportunities
- [Core] Activity log per opportunity
- [Enhanced] Multiple opportunities per contact (different products/pipelines)
- [Enhanced] Opportunity timeline (visual stage progression)
- [Future] Linked quotes/proposals (Commerce integration)

---

## 4. Activities & Follow-Ups

### Activities
- [Core] Activity timeline on conversation and contact detail
- [Core] Log activity: call, note, email, meeting, task
- [Core] Auto-logged activities: stage changes, assignments, messages sent
- [Core] Call disposition logging (after calls)
- [Core] Call recording playback (if recording enabled)
- [Core] Note creation with rich text
- [Core] Activity filters: type, date range, agent
- [Enhanced] Activity templates (pre-filled forms for common activities)
- [Future] Activity suggestions (based on conversation context)

### Follow-Ups
- [Core] Create follow-up: date, time, type, note, priority
- [Core] Follow-up list view: overdue, today, upcoming
- [Core] Due notification: in-app, push, email
- [Core] Mark complete or cancel
- [Core] Snooze (reschedule)
- [Core] Link to conversation (click → opens inbox at conversation)
- [Core] Auto-created follow-ups (from workflow rules, call dispositions)
- [Enhanced] Recurring follow-ups (daily/weekly/monthly check-in)
- [Enhanced] Manager view: team follow-ups, overdue by agent
- [Future] Calendar sync (Google Calendar, Outlook)

---

## 5. Assignment Engine

- [Core] Rule-based assignment (priority order, first match wins)
- [Core] Strategies: round-robin, load-balanced, source-based, manual queue
- [Core] Agent capacity limits (max open conversations)
- [Core] Agent availability check (online/offline)
- [Core] Assignment on new conversation
- [Core] Manual reassignment by agent or manager
- [Core] Bulk reassignment (manager)
- [Core] Assignment history log
- [Core] Transfer with internal note
- [Enhanced] Team-based assignment (assign to team, then distribute within)
- [Enhanced] Skill-based routing (language, product expertise)
- [Enhanced] Business hours awareness (queue for next day if after hours)
- [Future] Performance-based routing (assign to highest-converting agents)

---

## 6. Reports & Analytics

### Dashboard (Manager Home)
- [Core] Pipeline summary: total value, weighted value, win rate
- [Core] Team activity summary: calls, messages, follow-ups today
- [Core] Conversion funnel: lead → qualified → opportunity → won
- [Core] FRT overview: average, best, worst agent
- [Core] Open conversations count with SLA status breakdown
- [Core] Date range selector with presets
- [Enhanced] Customizable dashboard widgets (drag, resize, add/remove)
- [Enhanced] Comparison: this period vs previous period
- [Future] Real-time activity feed

### Reports
- [Core] First Response Time (FRT): per-agent breakdown, summary, daily trend
- [Core] Sales Funnel: cohort view, activity view, current status view
- [Core] Aging Report: open conversations by stage and age bucket
- [Core] Aging by Source: aging grouped by lead source
- [Core] Agent Activity: calls (in/out), messages, follow-ups per agent
- [Core] Outcome Report: opportunity → order conversion, new vs existing
- [Core] Revenue Contribution: revenue by agent and source
- [Core] Unqualified Analysis: disposition reasons, agent-wise, source-wise
- [Core] Conversation Trend: daily/weekly stage transition trends
- [Core] Export all reports to Excel
- [Enhanced] Enhanced trend with agent breakdown, velocity metrics, loss analysis
- [Enhanced] Scheduled reports (email daily/weekly summary)
- [Enhanced] Custom report builder (select metrics, dimensions, filters)
- [Future] Cohort analysis (leads from same period tracked over time)
- [Future] Attribution modeling (multi-touch source attribution)

---

## 7. Workflow Automation

- [Core] Rule builder: trigger → conditions → actions
- [Core] Triggers: conversation events, opportunity events, follow-up events, time-based
- [Core] Conditions: stage, channel, source, agent, custom field values, time
- [Core] Actions: create opportunity, change stage, assign, create follow-up, notify, send template, add note, close conversation
- [Core] Rule priority ordering
- [Core] Enable/disable rules
- [Core] Execution log (audit trail)
- [Enhanced] Webhook action (call external URL)
- [Enhanced] Condition groups (AND/OR logic)
- [Enhanced] Delayed actions (execute after X hours/days)
- [Future] Visual workflow builder (flowchart-style, like respond.io)
- [Future] Branching logic (if/else paths)
- [Future] Workflow templates (pre-built for common scenarios)

---

## 8. Settings & Configuration

### Workspace General
- [Core] Workspace profile (name, logo, industry, timezone, currency)
- [Core] Business hours and working days
- [Core] Holiday calendar

### Pipeline Configuration
- [Core] Create/edit/delete pipelines
- [Core] Create/edit/delete/reorder stages
- [Core] Stage probability weights
- [Core] Terminal stage configuration (win/loss outcomes)
- [Core] Win/loss reasons (configurable list)
- [Enhanced] Required fields per stage
- [Enhanced] Stage automation (auto-actions on entry)

### Custom Fields
- [Core] Define custom fields: Contact, Account, Opportunity, Conversation
- [Core] Field types: text, number, currency, date, dropdown, multi-select, checkbox, URL, email, phone, textarea
- [Core] Required/optional toggle
- [Core] Default values
- [Core] Show in list view / detail view / both
- [Enhanced] Field validation rules (regex, min/max)
- [Enhanced] Conditional fields (show if other field = value)
- [Future] Calculated fields (formulas)

### Contact Sources & Dispositions
- [Core] Manage contact source list
- [Core] Manage unqualified disposition reasons
- [Core] Manage lost deal reasons

### Assignment Rules
- [Core] Create/edit/delete/reorder rules
- [Core] Rule conditions and strategies
- [Core] Agent capacity settings

### SLA Policies
- [Core] First response time target
- [Core] Warning and breach thresholds
- [Core] Breach actions (notify, escalate)
- [Core] Business hours awareness (SLA pauses outside hours)

### Templates
- [Core] WhatsApp template sync from Meta
- [Core] Quick reply templates (text snippets)
- [Enhanced] Email templates (rich HTML)
- [Enhanced] Template variables (merge fields)
- [Enhanced] Template categories and search

### Channels
- [Core] WhatsApp Business API connection
- [Core] Voice provider connection
- [Core] Email (SES/SMTP) connection
- [Core] Lead capture: JustDial, Facebook, IndiaMart
- [Core] Channel health monitoring
- [Enhanced] Web form / live chat widget
- [Future] SMS, Instagram, Telegram, LINE

### Team Management
- [Core] View team members with roles
- [Core] Add/invite new members (via elauth)
- [Core] Assign/change CRM roles
- [Core] Deactivate agent (with reassignment)
- [Core] Agent settings (capacity, auto-assign)
- [Enhanced] Custom role creation
- [Enhanced] Capability-level permissions editing

### Import/Export
- [Core] Import contacts from CSV
- [Core] Export contacts to CSV/Excel
- [Core] Export report data to Excel
- [Enhanced] Import opportunities from CSV
- [Enhanced] Bulk data export (all workspace data)
- [Future] API for programmatic data access

---

## 9. Cross-Cutting Features

### Authentication & Session
- [Core] Login via elauth (JWT)
- [Core] MFA support (TOTP, WebAuthn)
- [Core] Workspace switching (OrgSwitcher)
- [Core] Auto token refresh
- [Core] Session management

### Search
- [Core] Global search (contacts, conversations, accounts)
- [Core] Inbox search (within conversation list)
- [Core] Contact list search
- [Enhanced] Full-text message search
- [Future] Fuzzy search / typo tolerance

### Notifications
- [Core] In-app notification center
- [Core] Browser push notifications
- [Core] Email notifications
- [Core] Notification preferences per user
- [Enhanced] Quiet hours
- [Enhanced] Daily digest emails
- [Future] Mobile push (when mobile app exists)

### Real-Time
- [Core] WebSocket for message delivery
- [Core] WebSocket for notification delivery
- [Core] WebSocket for conversation list updates
- [Enhanced] Agent online/offline presence
- [Enhanced] Typing indicators
- [Future] Real-time collaborative editing (shared notes)

### Mobile
- [Future] Progressive Web App (responsive, installable)
- [Future] Native mobile app (React Native, shares elsdk components)

---

## Feature Count Summary

| Category | Core | Enhanced | Future | Total |
|----------|------|----------|--------|-------|
| Inbox | 22 | 7 | 3 | 32 |
| Contacts & Accounts | 20 | 9 | 4 | 33 |
| Pipeline | 17 | 7 | 3 | 27 |
| Activities & Follow-Ups | 16 | 5 | 3 | 24 |
| Assignment | 10 | 3 | 1 | 14 |
| Reports | 13 | 5 | 3 | 21 |
| Workflow | 9 | 3 | 3 | 15 |
| Settings | 33 | 12 | 4 | 49 |
| Cross-Cutting | 16 | 6 | 5 | 27 |
| **Total** | **156** | **57** | **29** | **242** |
