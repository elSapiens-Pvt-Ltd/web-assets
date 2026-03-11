# System Architecture — Overview

> Module: `climate/architecture`
> Last updated: 2026-03-11

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [System Components](#system-components)
3. [Technology Stack](#technology-stack)
4. [Communication Flow](#communication-flow)
5. [Infrastructure Topology](#infrastructure-topology)
6. [Security Layers](#security-layers)
7. [Cross-References](#cross-references)

---

## High-Level Architecture

Climate CRM follows a client-server architecture with three runtime processes: an Angular 17 Single Page Application served as static files, a CodeIgniter 3 PHP REST API handling all business logic and data persistence, and a persistent WebSocket server for real-time message delivery. Redis acts as the message broker between the short-lived PHP request lifecycle and the long-running WebSocket process.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SERVICES                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ WhatsApp │ │ JustDial │ │ Facebook │ │ Firebase │ │ AWS SES  │ │
│  │ Cloud API│ │   API    │ │ Lead API │ │   FCM    │ │  (Email) │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       │             │            │             │            │       │
└───────┼─────────────┼────────────┼─────────────┼────────────┼───────┘
        │             │            │             │            │
        ▼             ▼            ▼             ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     PHP BACKEND (CodeIgniter 3)                      │
│                                                                      │
│  ┌────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ Controllers │  │    Models     │  │ Libraries  │  │   Hooks    │  │
│  │  (61 APIs)  │  │  (79+ Models) │  │ (Risposta, │  │ (JWT Auth, │  │
│  │             │  │              │  │  Redis,     │  │  CORS,     │  │
│  │             │  │              │  │  WebSocket) │  │  Perms)    │  │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  └────────────┘  │
│         │                │                │                          │
│         ▼                ▼                ▼                          │
│  ┌───────────────────────────────────────────────┐                   │
│  │           MySQL / MariaDB Database            │                   │
│  │           (300+ tables, utf8mb4)              │                   │
│  └───────────────────────────────────────────────┘                   │
│         │                                                            │
│         │    ┌──────────┐    ┌──────────┐    ┌──────────┐           │
│         ├───►│  Redis   │    │  AWS S3  │    │CloudFront│           │
│         │    │ (Queues) │    │ (Files)  │    │  (CDN)   │           │
│         │    └──────────┘    └──────────┘    └──────────┘           │
└─────────┼────────────────────────────────────────────────────────────┘
          │
          │  HTTP/JSON + WebSocket
          │
┌─────────▼────────────────────────────────────────────────────────────┐
│                  ANGULAR FRONTEND (SPA - v17)                        │
│                                                                      │
│  ┌────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────┐  │
│  │  48 Lazy-  │  │   Shared     │  │   Guards   │  │Interceptors│  │
│  │  Loaded    │  │   Module     │  │  (Auth)    │  │ (JWT, Err) │  │
│  │  Modules   │  │ (Components, │  │            │  │            │  │
│  │            │  │  Pipes, etc) │  │            │  │            │  │
│  └────────────┘  └──────────────┘  └────────────┘  └────────────┘  │
│                                                                      │
│  ┌────────────┐  ┌──────────────┐  ┌────────────┐                   │
│  │  Services  │  │  WebSocket   │  │  Firebase  │                   │
│  │  (72+)     │  │  Service     │  │  FCM       │                   │
│  └────────────┘  └──────────────┘  └────────────┘                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## System Components

| # | Component | Location | Responsibility |
|---|-----------|----------|----------------|
| 1 | Angular SPA | `climate-admin/` | Admin panel — 48 lazy-loaded modules, Material UI, Tailwind CSS, WebSocket client |
| 2 | CodeIgniter API | `climate-api/` | REST API — 61 controllers, JWT auth, capability RBAC, database access |
| 3 | Permission Hook | `hooks/permission_check.php` | CORS headers (`pre_system`), JWT validation + `@capability` enforcement + inactivity + session check (`post_controller_constructor`) |
| 4 | WebSocket Server | `WhatsappChat` controller + `Chat_websocket` library | Persistent Ratchet-based WebSocket on port 8988 for real-time message delivery |
| 5 | Redis Queue | `LibRedisQueue` library | Message broker between PHP request lifecycle and WebSocket server |
| 6 | Agent Assignment | `AgentAssignmentHelper` | 4-level priority: account owner → open conversation → previous agent → round-robin with leave awareness |
| 7 | Contact Message Processor | `ContactMessageModel` | Incoming message pipeline: handle lookup → conversation management → message insertion → real-time push |
| 8 | Cron Scheduler | `Cron` controller | Background jobs: follow-up processing, IndiaMart sync, FRT calculation, exchange rates, aging snapshots |
| 9 | WhatsApp Cloud API | `Whatsapp` controller | Webhook receiver for inbound messages/statuses; outbound messaging via Graph API |
| 10 | Invoice Generator | `knp-snappy` + wkhtmltopdf | PDF generation for tax invoices, proforma invoices, e-invoices, e-way bills |
| 11 | AWS Services | S3 + CloudFront + SES | File storage (media, invoices), CDN delivery (`d1r95e2xq05b34.cloudfront.net`), transactional email |
| 12 | Firebase FCM | `@angular/fire` | Browser push notifications for new messages, transfers, follow-up reminders |

---

## Technology Stack

### Frontend

| Technology | Version | Purpose |
|-----------|---------|---------|
| Angular | 17.0.5 | Single-page application framework |
| Angular Material | 17.0.2 | Material Design UI components |
| Tailwind CSS | 3.4.17 | Utility-first CSS styling |
| RxJS | 7.8.0 | Reactive state via BehaviorSubjects (no NgRx) |
| @auth0/angular-jwt | 5.1.2 | JWT token handling and route guards |
| @angular/fire | 17.0.0 | Firebase Cloud Messaging push notifications |
| @ngx-translate | 14.0.0 | Multi-language support (`en-IN`) |
| ngx-echarts + Chart.js | latest | Dashboard and report visualizations |
| TinyMCE | 7.0.0 | Rich text editing for notes and emails |

### Backend

| Technology | Version | Purpose |
|-----------|---------|---------|
| CodeIgniter | 3.x | PHP MVC framework with REST API routing |
| PHP | 7.4+ / 8.x | Server-side runtime |
| firebase/php-jwt | latest | HS512 JWT token generation and validation |
| predis/predis | 2.x | Redis client for queue and pub/sub |
| knp-snappy | 1.2+ | HTML-to-PDF via wkhtmltopdf |
| aws/aws-sdk-php | 3.x | S3, SES, CloudFront integration |
| Ratchet | latest | WebSocket server (via `Chat_websocket` library) |

### Infrastructure

| Service | Purpose |
|---------|---------|
| MySQL / MariaDB | Primary data store — 300+ tables, `utf8mb4_unicode_ci` |
| Redis | Message queue, pub/sub, work hours caching |
| AWS S3 | File storage — WhatsApp media, invoices, documents |
| AWS CloudFront | CDN delivery at `d1r95e2xq05b34.cloudfront.net` |
| AWS SES | Transactional email (ap-south-1) |
| Firebase FCM | Browser push notifications |

---

## Communication Flow

The system uses three communication patterns between frontend and backend:

### 1. HTTP REST API

All business operations flow through standard HTTP POST/GET requests with JSON payloads. The `JwtInterceptor` adds authentication headers, and the `ErrorInterceptor` handles session errors:

```
Angular Service → HttpClient.post(url, body)
                       │
                  JwtInterceptor
                  ├── Authorization: Bearer <JWT>
                  ├── CompanyId: <company_id>
                  └── InAs: <impersonation_id>
                       │
                  [HTTP to Backend]
                       │
                  ErrorInterceptor
                  ├── 400 → Session timeout check
                  ├── 401 → Multi-device logout
                  ├── 403 → Permission denied
                  └── 200 → Update lastActivityTime
                       │
                  Component receives response
```

### 2. WebSocket (Real-Time Chat)

A persistent WebSocket connection delivers messages instantly. The Angular `WebSocketService` connects on login and auto-reconnects on disconnect:

```
WebSocketService.wssConnect()
       │
       ├── onopen → Send chatjoin { token, user_id }
       ├── onmessage → communicationWss.next(data)
       ├── onclose → Auto-reconnect (unless code 3001)
       └── onerror → Log error
```

### 3. Push Notifications (Firebase FCM)

Background notifications via Firebase Cloud Messaging for events that occur when the agent isn't actively viewing the conversation:

```
Backend Event → FCM API → Service Worker → Browser Notification
                                │
                          Foreground:
                          FcmService.listenForMessages()
                          ├── Play notification.wav
                          ├── triggerNotification()
                          └── incrementNotificationCount()
```

---

## Infrastructure Topology

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
```

### Application URLs

| Environment | Frontend | Backend API | WebSocket |
|-------------|----------|-------------|-----------|
| Development | `http://localhost:4302` | `http://climate.loc/index.php` | `ws://localhost:8988` |
| Production | `https://admin.climatenaturals.com` | `https://api.climatenaturals.com/index.php` | `wss://api.climatenaturals.com/chat` |

---

## Security Layers

| Layer | Mechanism | Implementation |
|-------|-----------|----------------|
| **Transport** | HTTPS/TLS | Enforced via Nginx/Apache |
| **Authentication** | JWT (HS512) | 48-hour expiry, `firebase/php-jwt` library |
| **Single-Session** | `login_hash` | Each login generates unique hash in `tbl_login`; old sessions invalidated |
| **Authorization** | Capability-based RBAC | `@capability` DocBlock annotations checked via PHP Reflection in `PermissionCheck` hook |
| **Inactivity** | Server-side timeout | `tbl_user_last_request_log` compared against `tbl_settings.inactivity_setting` |
| **Cross-Tab Sync** | localStorage events | `lastActivityTime` and `multiTabLogoutFlag` shared across browser tabs |
| **CORS** | Dynamic origin | `PermissionCheck::preflight()` sets `Access-Control-Allow-Origin` from request origin |
| **Webhook Auth** | Varies by source | WhatsApp: verify_token challenge; JustDial: X-API-KEY header; Facebook: HMAC-SHA256 |

---

## Cross-References

| Document | Path |
|----------|------|
| Backend Architecture | `01-system-architecture/backend-architecture.md` |
| Frontend Architecture | `01-system-architecture/frontend-architecture.md` |
| Security & Auth | `01-system-architecture/security.md` |
| Communication Patterns | `01-system-architecture/communication-patterns.md` |
| Database Schema | `03-database-design/schema-overview.md` |
| API Authentication | `05-api-documentation/authentication.md` |
| Message Flow | `06-data-flow/message-flow.md` |
| Deployment Guide | `07-deployment-guide/environment-setup.md` |
