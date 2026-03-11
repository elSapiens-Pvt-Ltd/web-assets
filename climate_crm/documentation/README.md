# Climate CRM - Project Documentation

> Module: `climate/documentation`
> Last updated: 2026-03-11

---

## About

Complete technical documentation for the **Climate - The Spice Factory** CRM application, built with Angular 17 (frontend) and CodeIgniter 3/PHP (backend).

---

## Documentation Structure

```
documentation/
│
├── README.md                        ← You are here
├── FEATURE-LIST.md                  ← Complete feature inventory
│
├── 00-project-overview/             ← Project purpose, features, technologies
│   ├── overview.md                  # Project overview, purpose, user roles
│   ├── features.md                  # Detailed feature list by category
│   └── technologies.md             # All dependencies and infrastructure
│
├── 01-system-architecture/          ← How the system is built
│   ├── overview.md                  # High-level architecture diagram
│   ├── frontend-architecture.md     # Angular module system, state, HTTP pipeline
│   ├── backend-architecture.md      # CodeIgniter request lifecycle, auth, models
│   ├── communication-patterns.md    # HTTP, WebSocket, webhooks, push notifications
│   └── security.md                  # JWT, RBAC, session, audit
│
├── 02-folder-structure/             ← File and directory organization
│   └── overview.md                  # Frontend + backend folder trees, module purposes
│
├── 03-database-design/              ← Database tables and relationships
│   ├── schema-overview.md           # ERD, relationships summary, indexes
│   ├── core-tables.md               # Accounts, contacts, handles, addresses
│   ├── crm-tables.md                # Conversations, messages, assignments
│   ├── order-tables.md              # Orders, payments, opportunities
│   ├── configuration-tables.md      # Users, roles, settings, reference data
│   ├── triggers-and-functions.md    # 43 MySQL triggers + 4 stored functions
│   └── migration-system.md          # Migration conventions and usage
│
├── 04-core-modules/                 ← Business logic documentation
│   ├── overview.md                  # Module summary
│   ├── contacts-accounts.md         # Account/contact CRUD, merge workflow
│   ├── conversations.md             # Conversation lifecycle, stages, dispositions
│   ├── whatsapp-integration.md      # WhatsApp Cloud API, real-time chat
│   ├── assignment-management.md     # Agent assignment, transfer, workload
│   ├── order-management.md          # Order lifecycle, tax, invoicing
│   ├── messaging-system.md          # Multi-channel messaging, calls, notifications
│   └── reporting.md                 # CRM reports, dashboards, exports
│
├── 05-api-documentation/            ← API endpoint reference
│   ├── authentication.md            # Login, JWT, session management
│   ├── accounts-api.md              # Account/contact/handle CRUD endpoints
│   ├── conversations-api.md         # Conversation stage, transfer, assignment APIs
│   ├── whatsapp-api.md              # WhatsApp webhook, messaging, notes APIs
│   ├── orders-api.md                # Order CRUD, status, invoicing APIs
│   ├── reports-api.md               # Report endpoints (FRT, funnel, aging, etc.)
│   └── external-api.md              # External/third-party API endpoints
│
├── 06-data-flow/                    ← How data moves through the system
│   ├── message-flow.md              # Inbound/outbound message processing
│   ├── assignment-flow.md           # Contact assignment and transfer flow
│   ├── conversation-lifecycle.md    # Lead capture → qualification flow
│   ├── order-flow.md                # Order creation → delivery flow
│   └── webhook-flow.md              # External webhook integrations
│
├── 07-deployment-guide/             ← Setup and deployment
│   ├── environment-setup.md         # Prerequisites and tools
│   ├── database-setup.md            # Database configuration and migration
│   ├── frontend-setup.md            # Angular build and serve
│   └── backend-setup.md             # PHP, cron, Redis, AWS setup
│
└── 08-development-guidelines/       ← Coding standards and conventions
    ├── coding-standards.md          # Naming, style, patterns
    ├── adding-modules.md            # How to add new Angular modules
    ├── adding-apis.md               # How to add new API endpoints
    └── migration-guide.md           # How to create database migrations
```

---

## Quick Start

### For New Developers

1. Start with [00-project-overview/overview.md](./00-project-overview/overview.md) to understand the project
2. Read [01-system-architecture/overview.md](./01-system-architecture/overview.md) for the big picture
3. Explore [02-folder-structure/overview.md](./02-folder-structure/overview.md) to find your way around
4. Check [07-deployment-guide/](./07-deployment-guide/) to set up your development environment
5. Read [08-development-guidelines/](./08-development-guidelines/) before writing code

### For Backend Developers

1. [01-system-architecture/backend-architecture.md](./01-system-architecture/backend-architecture.md)
2. [03-database-design/](./03-database-design/)
3. [05-api-documentation/](./05-api-documentation/)
4. [08-development-guidelines/adding-apis.md](./08-development-guidelines/adding-apis.md)

### For Frontend Developers

1. [01-system-architecture/frontend-architecture.md](./01-system-architecture/frontend-architecture.md)
2. [04-core-modules/](./04-core-modules/) — understand business logic
3. [05-api-documentation/](./05-api-documentation/) — API reference
4. [08-development-guidelines/adding-modules.md](./08-development-guidelines/adding-modules.md)

### For Understanding Data Flow

1. [06-data-flow/](./06-data-flow/) — end-to-end data flow diagrams
2. [01-system-architecture/communication-patterns.md](./01-system-architecture/communication-patterns.md)

---

## Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| **Frontend** | Angular 17 + Material Design + Tailwind CSS |
| **Backend** | PHP / CodeIgniter 3 |
| **Database** | MySQL / MariaDB (utf8mb4) |
| **Real-time** | WebSocket (custom Chat_websocket library) |
| **Queue** | Redis (LibRedisQueue) |
| **Auth** | JWT (HS512) with capability-based RBAC |
| **Storage** | AWS S3 + CloudFront CDN |
| **Email** | AWS SES |
| **Push** | Firebase Cloud Messaging |
| **Messaging** | WhatsApp Business Cloud API |

---

## Project Repositories

| Repository | Purpose |
|------------|---------|
| `climate-admin` | Angular frontend (SPA) |
| `climate-api` | CodeIgniter PHP backend (REST API) |

---

## Key Metrics

| Metric | Count |
|--------|-------|
| Angular Feature Modules | 48 (lazy-loaded) |
| Backend Controllers | 61 |
| Backend Models | 79+ |
| Database Migrations | 326 |
| Frontend Services | 72+ |
| API Endpoints | 150+ |
| Database Tables | 300+ |
