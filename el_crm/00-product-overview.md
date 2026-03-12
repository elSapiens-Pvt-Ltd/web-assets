# el-CRM Product Overview

> Version: 0.1 (Product Bible Draft)
> Last updated: 2026-03-12

---

## 1. What is el-CRM?

el-CRM is a **multi-tenant, omnichannel CRM platform** built for businesses that manage customer relationships across multiple communication channels — B2B, B2C, or hybrid. It is designed to be configured and delivered to any client as a product — not a one-off build.

The platform is part of the **elSapiens ecosystem** — a suite of 20+ microservices and apps (auth, accounts, telephony, finance, geolocation, product catalog, ops management) that work together. el-CRM plugs into this ecosystem, consuming existing services rather than rebuilding functionality.

---

## 2. Vision

**Build once, configure for many.** Every client gets the same codebase with workspace-level configuration that adapts the CRM to their industry, sales process, team structure, and channel preferences — without code changes.

### What We're NOT Building
- A horizontal CRM competing with Salesforce/HubSpot on breadth
- A marketing automation platform
- A customer support ticketing system (though conversations can serve support use cases)

### What We ARE Building
- A **sales-focused, conversation-driven CRM** optimized for teams that sell through direct communication (WhatsApp, phone, email)
- Think: **respond.io's messaging inbox** + **HubSpot's pipeline management** + **Freshsales' agent productivity tools** — unified in one workspace-configurable platform

---

## 3. Target Users

### Primary: Sales & Customer-Facing Teams (SMB to Mid-Market)
- **B2B**: Manufacturing, trading, distribution, wholesale, services
- **B2C**: Retail chains, salons, automotive services, real estate, education
- **Hybrid**: Businesses selling to both companies and individuals
- **Team size**: 5-100 agents per workspace
- **Sales model**: Relationship-driven, high-touch, multi-channel communication
- **Typical flow**: Lead capture → qualification → opportunity → order → account management

### User Roles

| Role | Description | Key Activities |
|------|-------------|----------------|
| **Sales Agent** | Front-line — talks to customers daily | Inbox, conversations, follow-ups, pipeline management |
| **Sales Manager** | Team lead — monitors agent performance | Reports, agent activity, pipeline review, assignment overrides |
| **Admin** | Workspace administrator — configures the CRM | Settings, pipeline config, custom fields, user management, workflow rules |
| **Super Admin** | Platform-level (elSapiens internal) | Workspace provisioning, cross-workspace analytics, system health |

---

## 4. Core Modules

| Module | Purpose | Key Capabilities |
|--------|---------|-----------------|
| **Inbox** | Omnichannel conversation hub | 3-panel layout (conversation list, chat thread, contact details), real-time messaging, channel switching, quick replies, media sharing |
| **Contacts & Accounts** | Customer data management | Contact profiles, account (company) management, contact handles (phone/email/social), merge, lifecycle stages — *delegates to accounts-api* |
| **Pipeline** | Visual deal tracking | Kanban board, configurable stages per workspace, drag-and-drop, opportunity values, win/loss tracking |
| **Activities** | Agent work tracking | Notes, follow-up tasks, call dispositions, activity timeline, scheduled reminders |
| **Assignment Engine** | Intelligent lead routing | Round-robin, load-balanced, source-based, manual — configurable rules per workspace |
| **Reports & Analytics** | Performance visibility | FRT reports, sales funnel, aging analysis, agent activity, revenue contribution, outcome tracking |
| **Workflows** | Automation rules | Trigger → condition → action chains, stage-change automations, notification rules, SLA escalations |
| **Settings** | Workspace configuration | Pipeline stages, custom fields, business hours, SLA thresholds, contact sources, assignment rules, templates |

---

## 5. Key Differentiators

### 5.1 Omnichannel-Native (Not Bolted On)
Unlike CRMs that add WhatsApp/voice as integrations, el-CRM is built channel-agnostic from day one. **Unibox (elunibox)** — a dedicated omnichannel communication platform — handles all messaging across 11+ channels. The CRM embeds Unibox for its inbox view and delegates all send/receive operations to it. Adding a new channel requires zero CRM code changes — just a new adapter in Unibox.

**Supported channels** (via Unibox):
- **Email**: Microsoft 365, Google Workspace (Gmail), iCloud Mail, AOL/Yahoo Mail
- **Messaging**: WhatsApp Business API, Telegram Bot API, SMS (Twilio)
- **Social**: Facebook (Pages + Messenger), Instagram (DMs + Comments), X/Twitter (DMs + Mentions), LinkedIn (Messages + Comments), TikTok (Comments), YouTube (Comments + Live Chat)
- **Lead capture**: JustDial, Facebook Lead Ads, IndiaMart, web forms
- **Internal**: Built-in team chat (within Unibox)
- **Support tickets**: Also handled via Unibox

All Meta channels (WhatsApp, Messenger, IG, FB) share a single OAuth flow.

**Future channels** (adapter-only additions in Unibox):
- LINE, live chat widget, additional social platforms

### 5.2 Conversation-Centric (Not Record-Centric)
Traditional CRMs are record-centric — you create a contact, then work from the contact record. el-CRM is **conversation-centric** — the inbox is the primary workspace. Agents respond to conversations, and the CRM structures data around those conversations (pipeline stage, assignment, activities, follow-ups).

This matches how sales actually works — whether B2B or B2C: a customer messages on WhatsApp, calls, or emails — the agent picks up the conversation wherever it happens.

### 5.3 Workspace-Configurable
Every aspect of the CRM adapts per workspace without code changes:
- Pipeline stages (number, names, order, terminal states)
- Custom fields on contacts, accounts, opportunities
- Assignment rules and strategies
- Business hours and SLA thresholds
- Contact sources and disposition reasons
- Notification templates and workflow automations

### 5.4 Ecosystem-Integrated
el-CRM is not a standalone product. It runs within the elSapiens ecosystem of 20+ services:
- **elauth**: Authentication, MFA, workspace-scoped RBAC — no separate login
- **accounts-api**: Shared contact/account data across all elSapiens services
- **Workspace Service**: Workspace metadata, plan limits, cross-app config
- **elGeolocations**: Address validation, pincode → city/state lookup, location-based profiling
- **elCurrency Rates**: Multi-currency opportunity values, conversion for reports
- **Goods & Services**: Product catalog linked to opportunities
- **elPBX**: Click-to-call, agent phone mapping, call routing
- **Logger**: Centralized audit logging and error reporting
- **App Registry**: Service discovery, cross-app navigation
- **el-tracker**: Ops management (tasks, travel, attendance) for the same team
- **elBooks** (future): Accounting, invoicing linked to won opportunities
- **Inventory Management** (future): Stock-aware opportunity management

### 5.5 Agent-First UX
Inspired by respond.io's messaging-first approach:
- The inbox is the home screen, not a dashboard
- Quick-reply templates, canned responses, keyboard shortcuts
- Contact details and conversation history always visible alongside the chat
- Follow-up reminders without leaving the conversation
- Mobile-responsive for field sales agents

---

## 6. Technical Foundation

| Aspect | Choice |
|--------|--------|
| Backend | Go (Golang) — matches elauth, high performance, single binary |
| Frontend | React 18 + @elsapiens/elsdk (60+ shared components) |
| Database | PostgreSQL with Row-Level Security (workspace isolation) |
| Inter-service | gRPC + Protobuf (matches elauth ↔ accounts-api pattern) |
| Messaging Platform | Unibox (elunibox) — omnichannel send/receive across all channels |
| Notification Delivery | elmessagehub — transactional alerts, reminders, SLA notifications |
| Event Bus | Kafka (shared with Unibox and elmessagehub) |
| Real-time | WebSocket for inbox, message delivery status |
| Multi-tenancy | `workspace_id` column + PostgreSQL RLS + application-layer guards |
| Auth | JWT from elauth (HS256, 24hr access / 7-30 day refresh tokens) |

---

## 7. Success Metrics

### For the Platform
- Time to onboard a new client workspace: < 1 day (configuration only, no code)
- Zero cross-workspace data leakage (automated RLS tests)
- < 500ms p95 latency for inbox message display
- Support 50+ concurrent workspaces on shared infrastructure

### For Each Client Workspace
- First Response Time (FRT) — tracked and reportable per agent
- Lead-to-opportunity conversion rate
- Pipeline velocity (days per stage)
- Agent activity metrics (calls, messages, follow-ups per day)
- Revenue attribution by source and agent

---

## 8. Document Map

This Product Bible contains the following specifications:

| Document | Description |
|----------|-------------|
| [01-user-flows/](01-user-flows/) | Step-by-step user journeys for every role |
| [02-feature-inventory.md](02-feature-inventory.md) | Complete feature checklist by module |
| [03-information-architecture.md](03-information-architecture.md) | Page hierarchy, navigation, URL structure |
| [04-page-specs/](04-page-specs/) | Per-page layout, components, behavior, interactions |
| [05-data-model.md](05-data-model.md) | CRM-owned tables, relationships, accounts-api references |
| [06-api-contracts.md](06-api-contracts.md) | REST + gRPC endpoint specifications |
| [07-integration-map.md](07-integration-map.md) | Service-to-service connections and data flow |
| [08-rbac-matrix.md](08-rbac-matrix.md) | Roles, capabilities, data scoping rules |
| [09-workflow-engine.md](09-workflow-engine.md) | Automation triggers, conditions, actions |
| [10-channel-specs.md](10-channel-specs.md) | Per-channel message types, behavior, fallbacks |
| [11-report-specs.md](11-report-specs.md) | Report definitions, data sources, filters |
| [12-configuration-spec.md](12-configuration-spec.md) | Workspace-level configurable settings |
