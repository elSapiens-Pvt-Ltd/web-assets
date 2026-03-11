# Climate CRM — System Overview

> Module: `climate/crm`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Vision](#vision)
2. [Design Principles](#design-principles)
3. [System Components](#system-components)
4. [Technology Stack](#technology-stack)
5. [Data Flow](#data-flow)
6. [Deployment Topology](#deployment-topology)
7. [Cross-References](#cross-references)

---

## Vision

Climate CRM is a full-featured Customer Relationship Management platform built for **The Spice Factory (Climate Naturals)**, a B2B/B2C spice manufacturing and export company based in India. The system manages the complete customer lifecycle — from initial lead capture through WhatsApp, JustDial, IndiaMart, and Facebook, through conversation nurturing and qualification, to order placement, invoicing, and fulfillment.

The platform replaces manual lead tracking, siloed communication channels, and paper-based order processing with a unified real-time system. All customer interactions — WhatsApp messages, phone calls, notes, follow-ups — flow through a single conversation interface with intelligent agent assignment and workload distribution.

### Key Goals

- **Unified Communication**: All customer touchpoints (WhatsApp, phone, email, walk-in, web leads) consolidated into one conversation interface
- **Real-Time Operations**: WebSocket-powered live chat with Redis queue for instant message delivery and agent notifications
- **Intelligent Assignment**: 4-level priority agent assignment (account owner → active conversation → previous agent → round-robin) with leave/availability awareness
- **End-to-End Order Lifecycle**: Draft → Confirmed → Final → Despatched → Delivered with tax calculation (GST), invoicing, and payment tracking
- **Multi-Source Lead Capture**: Automatic contact creation from WhatsApp messages, JustDial webhooks, Facebook Lead Ads, IndiaMart API, and external partners
- **Capability-Based RBAC**: Fine-grained permissions via PHP DocBlock `@capability` annotations enforced at the hook level before controller execution
- **CRM Analytics**: First Response Time, conversation funnel, aging, revenue attribution, and agent activity reporting
- **PWA Support**: Service Worker-enabled Progressive Web App with offline caching and push notifications via Firebase Cloud Messaging

### User Roles

| Role | Description |
|------|-------------|
| **Super Admin** | Full system access — bypasses all capability checks (`is_super == "Yes"`) |
| **Sales Admin** (role_id: 9) | Manages sales team, views all reports, admin dashboard |
| **Sales Agent** (role_id: 4) | Handles conversations, creates orders, agent dashboard |
| **Standard Users** | Access based on assigned capabilities per role |
| **Customers** | External customer portal access (limited, separate layout) |

### Application URLs

| Environment | Frontend | Backend API | WebSocket |
|-------------|----------|-------------|-----------|
| Development | `http://localhost:4302` | `http://climate.loc/index.php` | `ws://localhost:8988` |
| Production | `https://admin.climatenaturals.com` | `https://api.climatenaturals.com/index.php` | `wss://api.climatenaturals.com/chat` |

### Localization

- **Locale**: `en-IN` (Indian English)
- **Currency**: `INR` (Indian Rupee)
- **Timezone**: `Asia/Kolkata` (UTC +5:30)
- **i18n**: Translation files in `/assets/i18n/` via `@ngx-translate`

---

## Design Principles

| # | Principle | Description |
|---|-----------|-------------|
| 1 | **Single Conversation View** | All messages (WhatsApp, notes, system events, calls) for a customer appear in one chronological chat thread |
| 2 | **Automatic Stage Transitions** | Conversation stages advance automatically — `new` → `attempted` on first agent message, `attempted` → `contacted` on customer reply |
| 3 | **Capability-Based Authorization** | Every controller method declares its required capability via `@capability` DocBlock — enforced by the `PermissionCheck` hook before execution |
| 4 | **Real-Time First** | All message delivery uses WebSocket push via Redis queue — no polling. Frontend receives events within milliseconds |
| 5 | **Phone Normalization** | All Indian phone numbers normalized to 10-digit format (strip +91, leading 0, spaces) for consistent database lookups |
| 6 | **Lazy-Loaded Modules** | All 48 frontend feature modules are lazy-loaded via `loadChildren` for fast initial page load |
| 7 | **OnPush Change Detection** | All Angular components use `ChangeDetectionStrategy.OnPush` with manual `detectChanges()` for optimal rendering performance |
| 8 | **Webhook Audit Trail** | All incoming webhook payloads (WhatsApp, JustDial, Facebook) are stored raw before processing for debugging and replay |
| 9 | **Session Security** | JWT with `login_hash` for single-device enforcement, server-side inactivity timeout, cross-tab activity synchronization |

---

## System Components

| # | Component | Location | Responsibility |
|---|-----------|----------|----------------|
| 1 | Angular SPA | `climate-admin/` | Admin panel — 48 lazy-loaded modules, Material UI, Tailwind CSS, WebSocket client |
| 2 | CodeIgniter API | `climate-api/` | REST API — 61 controllers, JWT auth, capability RBAC, database access |
| 3 | Permission Hook | `hooks/permission_check.php` | `pre_system`: CORS headers. `post_controller_constructor`: JWT validation, `@capability` enforcement, inactivity timeout, single-session check |
| 4 | WebSocket Server | `Chat_websocket` library | Persistent connections for real-time message delivery to agents |
| 5 | Redis Queue | `LibRedisQueue` library | Message broker between PHP request lifecycle and WebSocket server |
| 6 | Agent Assignment | `agent_assignment_helper.php` | 4-level priority system: account owner → open conversation → previous agent → round-robin with leave awareness |
| 7 | Contact Message Processor | `ContactMessageModel` | Incoming message pipeline: handle lookup → conversation management → message insertion → real-time push |
| 8 | Cron Scheduler | `Cron` controller | Background jobs: follow-up processing, IndiaMart sync, FRT calculation, exchange rates, aging snapshots |
| 9 | WhatsApp Cloud API | `Whatsapp` controller | Webhook receiver for inbound messages/statuses; outbound messaging via Graph API |
| 10 | Invoice Generator | `knp-snappy` + wkhtmltopdf | PDF generation for tax invoices, proforma invoices, e-invoices, e-way bills |
| 11 | AWS Services | S3 + CloudFront + SES | File storage (media, invoices), CDN delivery, transactional email |
| 12 | Firebase FCM | `@angular/fire` | Push notifications for new messages, transfers, follow-up reminders |

### Hook Registration

The two critical hooks are registered in `application/config/hooks.php`:

```php
// application/config/hooks.php

$hook['post_controller_constructor'] = array(
    'class'    => 'PermissionCheck',
    'function' => 'CheckAccess',
    'filename' => 'permission_check.php',
    'filepath' => 'hooks',
);

$hook['pre_system'] = array(
    'class'    => 'PermissionCheck',
    'function' => 'preflight',
    'filename' => 'permission_check.php',
    'filepath' => 'hooks',
);
```

`pre_system` fires before any controller loads — it sets CORS headers and handles OPTIONS preflight requests. `post_controller_constructor` fires after the controller is instantiated but before the method runs — it validates JWT, checks capabilities, enforces session rules, and tracks inactivity.

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Frontend Framework | Angular | 17.0.5 | Single-page application |
| UI Components | Angular Material | 17.0.2 | Material Design component library |
| CSS Framework | Tailwind CSS | 3.4.17 | Utility-first styling |
| State Management | RxJS | 7.8.0 | BehaviorSubject-based reactive state (no NgRx) |
| i18n | ngx-translate | 14.0.0 | Multi-language support |
| Charts | ngx-echarts + Chart.js | latest | Dashboard and report visualizations |
| Rich Text | TinyMCE | 7.0.0 | Rich text editing for notes and emails |
| Auth Library | @auth0/angular-jwt | 5.1.2 | JWT token handling and route guards |
| Firebase | @angular/fire | 17.0.0 | Push notifications (FCM) |
| Backend Framework | CodeIgniter | 3.x | PHP MVC with REST API routing |
| PHP Runtime | PHP | 7.4+ / 8.x | Server-side execution |
| Database | MySQL / MariaDB | 5.7+ / 10.x+ | Primary data store (utf8mb4_unicode_ci) |
| JWT Library | firebase/php-jwt | latest | HS512 JWT token generation and validation |
| Redis Client | predis/predis | 2.x | Queue system and real-time message broker |
| PDF Generation | knp-snappy | 1.2+ | HTML-to-PDF via wkhtmltopdf |
| AWS SDK | aws/aws-sdk-php | 3.x | S3, SES, CloudFront integration |
| WebSocket | codeigniter-websocket | 1.0 | Custom WebSocket server library |
| Mobile | Service Worker | - | PWA with offline caching |

### External Integrations

| Service | Type | Purpose |
|---------|------|---------|
| WhatsApp Business Cloud API | Webhook (push) | Customer messaging — inbound/outbound text, media, templates |
| JustDial | Webhook (push) | B2B lead capture via API key authentication |
| IndiaMart | Cron (pull) | B2B lead capture via periodic API sync |
| Facebook Lead Ads | Webhook (push) | Social media lead capture |
| Google Sheets | REST API | Data export/import |
| Google Maps API | REST API | Address geocoding and location services |
| Vtransact / AWLME | REST API | Payment gateway integration |
| AWS S3 | SDK | File storage (media, invoices, documents) |
| AWS CloudFront | CDN | Static asset and media delivery (`d1r95e2xq05b34.cloudfront.net`) |
| AWS SES | SMTP | Transactional email (ap-south-1) |

---

## Data Flow

### Inbound WhatsApp Message Flow

```
1. WhatsApp Cloud API sends webhook POST
       │
2. Whatsapp::webhookCloudApi() receives payload
   ├── Store raw JSON in tbl_whatsapp_callback (audit)
   ├── Download media to S3 (if non-text message)
   └── Build message + contact data structures
       │
3. ContactMessageModel::processIncomingMessage()
   ├── Normalize phone number to 10-digit format
   ├── Look up handle in temp_tbl_contact_handles
   │   └── If not found → create contact + handle
   ├── Find or create conversation (tbl_open_conversations)
   │   └── Auto-transition: attempted → contacted (on customer reply)
   └── Insert message into tbl_whatsapp_messages
       │
4. Redis queue push
   ├── queue::pushNewConversation() → conversation list UI
   └── queue::pushChatIncoming() → chat window UI
       │
5. WebSocket server delivers to connected agent
       │
6. Angular ChatWindowComponent renders message in real-time
```

### Order Creation Flow

```
1. Agent creates order from conversation or Orders module
       │
2. Multi-step wizard: Account → Items → Addresses → Review
   ├── Tax auto-calculated: CGST+SGST (same state) or IGST (inter-state)
   └── Discount above threshold → admin approval required
       │
3. POST /orders/save
   ├── Insert tbl_orders + tbl_order_items
   ├── Close linked conversation (stage → 'converted')
   ├── Create/link tbl_opportunities record
   └── Insert system message: "Order Created - Order #: {id}"
       │
4. Status progression: Draft → Confirmed → Final → Despatched → Delivered
   └── Each transition logged in tbl_order_status_logs
```

### Agent Assignment Flow

```
1. New message arrives for contact without open conversation
       │
2. AgentAssignmentHelper::getAgentForHandle()
   ├── Priority 1: Account owner (temp_tbl_accounts.account_owner_id)
   ├── Priority 2: Agent on open conversation for this contact
   ├── Priority 3: Agent on most recent closed conversation
   └── Priority 4: Round-robin from tbl_settings.agent_allocation
       ├── Check tbl_telecommunication_agents.is_active
       ├── Check tbl_user_leaves (full_day / first_half / second_half)
       └── Check tbl_company_work_hours
       │
3. Create conversation with assigned agent
   └── Record in tbl_contact_assignment_history
```

---

## Deployment Topology

```
┌────────────────────────────────────────────────────────────────────┐
│                        Load Balancer                                │
│                       (Nginx/Apache)                               │
└───────────────┬──────────────────────┬─────────────────────────────┘
                │                      │
      ┌─────────┴──────────┐ ┌────────┴──────────┐
      │  Angular SPA       │ │  CodeIgniter API   │
      │  (static files)    │ │  (PHP-FPM)         │
      │                    │ │                    │
      │  - 48 lazy modules │ │  - 61 controllers  │
      │  - Material + TW   │ │  - 79+ models      │
      │  - Service Worker  │ │  - JWT + RBAC      │
      │  - Firebase FCM    │ │  - Cron scheduler  │
      └────────────────────┘ └──┬──────────┬──────┘
                                │          │
                                │          │
      ┌─────────────────────────┤          ├──────────────────────┐
      │                         │          │                      │
┌─────┴──────────┐  ┌──────────┴──┐  ┌────┴─────────┐  ┌────────┴──────┐
│  MySQL/MariaDB │  │  Redis      │  │  WebSocket   │  │  AWS Services │
│  (port 3306)   │  │  (port 6379)│  │  (port 8988) │  │               │
│                │  │             │  │              │  │  S3 (files)   │
│  - 300+ tables │  │  - Queue    │  │  - Real-time │  │  CloudFront   │
│  - utf8mb4     │  │  - Pub/Sub  │  │    messages  │  │  SES (email)  │
│  - 326 migr.   │  │  - Caching  │  │  - Agent     │  │               │
│                │  │             │  │    sessions  │  │               │
└────────────────┘  └─────────────┘  └──────────────┘  └───────────────┘

External Integrations:
┌───────────────┐  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐
│ WhatsApp      │  │ JustDial      │  │ Facebook     │  │ IndiaMart    │
│ Cloud API     │  │ (webhook)     │  │ (webhook)    │  │ (cron pull)  │
│ (webhook)     │  │               │  │              │  │              │
└───────────────┘  └───────────────┘  └──────────────┘  └──────────────┘
```

### Key Metrics

| Metric | Count |
|--------|-------|
| Angular Feature Modules | 48 (lazy-loaded) |
| Backend Controllers | 61 |
| Backend Models | 79+ |
| Database Migrations | 326 |
| Frontend Services | 72+ |
| API Endpoints | 150+ |
| Database Tables | 300+ |

---

## Cross-References

| Document | Path |
|----------|------|
| Feature List | `docs/FEATURE-LIST.md` |
| Technologies Detail | `docs/00-project-overview/technologies.md` |
| Features Detail | `docs/00-project-overview/features.md` |
| Frontend Architecture | `docs/01-system-architecture/frontend-architecture.md` |
| Backend Architecture | `docs/01-system-architecture/backend-architecture.md` |
| Security & Auth | `docs/01-system-architecture/security.md` |
| Communication Patterns | `docs/01-system-architecture/communication-patterns.md` |
| Folder Structure | `docs/02-folder-structure/overview.md` |
| Database Schema | `docs/03-database-design/schema-overview.md` |
| Core Modules | `docs/04-core-modules/overview.md` |
| API Endpoints | `docs/05-api-documentation/authentication.md` |
| Data Flows | `docs/06-data-flow/message-flow.md` |
| Deployment Guide | `docs/07-deployment-guide/environment-setup.md` |
| Development Guidelines | `docs/08-development-guidelines/coding-standards.md` |
