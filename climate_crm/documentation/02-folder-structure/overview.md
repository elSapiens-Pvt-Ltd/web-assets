# Folder Structure — Project Overview

> Module: `climate/structure`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Project Root](#project-root)
2. [Angular Frontend](#angular-frontend-climate-admin)
3. [Feature Module Pattern](#feature-module-pattern)
4. [PHP Backend](#php-backend-climate-api)
5. [Frontend Module Reference](#frontend-module-reference)
6. [Cross-References](#cross-references)

---

## Project Root

The Climate CRM monorepo contains two application directories and a documentation directory:

```
climate-india/
├── climate-admin/          # Angular 17 frontend (SPA)
├── climate-api/            # CodeIgniter 3 PHP backend (REST API)
└── documentation/          # Project documentation
```

---

## Angular Frontend (`climate-admin/`)

```
climate-admin/
├── src/
│   ├── app/
│   │   ├── app.module.ts                 # Root module — imports, providers, bootstrap
│   │   ├── app.component.ts              # Root component
│   │   ├── app-routing.module.ts         # Top-level routing (lazy-loaded modules)
│   │   ├── app.config.ts                 # AppConfig — static settings, API URL loader
│   │   ├── boot-control.ts              # Bootstrap control utilities
│   │   │
│   │   ├── shared/                       # ── GLOBAL SHARED MODULE ──
│   │   │   ├── shared.module.ts          # SharedModule declaration & exports
│   │   │   │
│   │   │   ├── components/               # Reusable UI components
│   │   │   │   ├── layouts/
│   │   │   │   │   ├── admin-layout/     # Main admin layout (sidebar + header + footer)
│   │   │   │   │   ├── auth-layout/      # Auth pages layout (no sidebar)
│   │   │   │   │   └── customer-layout/  # Customer portal layout
│   │   │   │   ├── header/               # Top navigation bar
│   │   │   │   ├── sidebar-side/         # Left sidebar navigation
│   │   │   │   ├── sidenav/              # Material sidenav wrapper
│   │   │   │   ├── footer/               # Page footer
│   │   │   │   ├── breadcrumb/           # Dynamic breadcrumb navigation
│   │   │   │   ├── search/               # Global search component
│   │   │   │   ├── notification/         # Push notification display
│   │   │   │   ├── notifications/        # Notification list/panel
│   │   │   │   ├── call-interface/       # Call status and controls
│   │   │   │   ├── image-crop/           # Image cropping (Croppie)
│   │   │   │   ├── speed-dial/           # Material FAB speed dial
│   │   │   │   ├── loading/              # Loading state indicator
│   │   │   │   └── export-date-range-dialog/
│   │   │   │
│   │   │   ├── services/                 # Global services
│   │   │   │   ├── auth/
│   │   │   │   │   └── auth.guard.ts     # Route guard — JWT validation
│   │   │   │   ├── login.service.ts      # Authentication, capabilities, session
│   │   │   │   ├── idle.service.ts       # Inactivity detection & auto-logout
│   │   │   │   ├── web-socket.service.ts # WebSocket connection for real-time chat
│   │   │   │   ├── layout.service.ts     # Sidebar style, direction, breakpoints
│   │   │   │   ├── theme.service.ts      # Material theme switching
│   │   │   │   ├── topbar.service.ts     # Page state, filters, pagination triggers
│   │   │   │   ├── navigation.service.ts # Navigation handling
│   │   │   │   ├── route-parts.service.ts# Breadcrumb generation
│   │   │   │   ├── common.service.ts     # Common utilities
│   │   │   │   ├── upload.service.ts     # S3 pre-signed URL uploads
│   │   │   │   ├── image.service.ts      # Image processing
│   │   │   │   ├── app-updater.service.ts# PWA version update checks
│   │   │   │   ├── system.service.ts     # System-level operations
│   │   │   │   │
│   │   │   │   ├── firebase/
│   │   │   │   │   └── fcm.service.ts    # Firebase Cloud Messaging
│   │   │   │   ├── contact-handles/
│   │   │   │   │   └── contact-handles.service.ts
│   │   │   │   │
│   │   │   │   ├── app-confirm/          # Confirmation dialog service
│   │   │   │   ├── app-prompt/           # Input prompt dialog service
│   │   │   │   ├── app-view/             # Detail view dialog service
│   │   │   │   ├── app-loader/           # Loading spinner dialog service
│   │   │   │   ├── notification/         # Notification display service
│   │   │   │   └── inactivity-reminder/  # Idle timeout warning dialog
│   │   │   │
│   │   │   ├── helpers/                  # HTTP interceptors & utilities
│   │   │   │   ├── jwt.interceptor.ts    # Adds JWT token to API requests
│   │   │   │   ├── error.interceptor.ts  # Handles HTTP errors (400/401/403)
│   │   │   │   ├── url.helper.ts         # URL utilities
│   │   │   │   ├── utils.ts              # General utility functions
│   │   │   │   ├── validators.ts         # Custom form validators
│   │   │   │   └── window.helper.ts      # Browser/window utilities
│   │   │   │
│   │   │   ├── pipes/                    # Custom pipes (21+)
│   │   │   │   ├── relative-time.pipe.ts # "2 hours ago" formatting
│   │   │   │   ├── safe-html.pipe.ts     # HTML sanitization
│   │   │   │   ├── excerpt.pipe.ts       # Text truncation
│   │   │   │   ├── has-permission.pipe.ts# Capability check in templates
│   │   │   │   ├── order-status.pipe.ts  # Order status display formatting
│   │   │   │   ├── r-date.pipe.ts        # Relative date formatting
│   │   │   │   ├── date-diff.pipe.ts     # Date difference calculation
│   │   │   │   ├── seconds-to-time.pipe.ts
│   │   │   │   ├── sort.pipe.ts          # Array/object sorting
│   │   │   │   ├── timestamp-to-date.pipe.ts
│   │   │   │   └── ... (more pipes)
│   │   │   │
│   │   │   ├── directives/              # Custom directives (7)
│   │   │   │   ├── font-size.directive.ts
│   │   │   │   ├── scroll-to.directive.ts
│   │   │   │   ├── dropdown.directive.ts
│   │   │   │   ├── sidenav-toggle.directive.ts
│   │   │   │   └── forbidden-string-validator.directive.ts
│   │   │   │
│   │   │   ├── models/                   # TypeScript interfaces & models
│   │   │   │   ├── app-config.model.ts   # IAppConfig interface
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── animations/              # Angular animations (fade, slide, scale)
│   │   │   └── phone-validator/         # Phone number validation
│   │   │
│   │   └── views/                        # ── FEATURE MODULES (48) ──
│   │       │
│   │       │   # ─── CRM & Communication ───
│   │       ├── whatsapp/                 # WhatsApp messaging & chat
│   │       │   ├── chat-window/          # Real-time chat interface
│   │       │   ├── conversations-list/   # Conversation list with filters
│   │       │   ├── customer-details/     # Customer info panel in chat
│   │       │   ├── whatsapp.service.ts   # 40+ API endpoints
│   │       │   └── whatsapp.module.ts
│   │       ├── leads/                    # Lead/contact management
│   │       ├── customer-contacts/        # Customer contact records
│   │       │   ├── components/
│   │       │   │   ├── assignment-history-dialog/
│   │       │   │   └── assignment-timeline/
│   │       │   └── services/
│   │       │       └── assignment-history.service.ts
│   │       ├── opportunity-contacts/     # Sales opportunities
│   │       ├── conflict-resolution/      # CRM conflict resolution
│   │       │
│   │       │   # ─── Accounts & Customers ───
│   │       ├── customers/                # Account management
│   │       │   ├── edit-account/
│   │       │   │   └── merge-account/    # Account merge workflow
│   │       │   └── services/
│   │       │       └── customer.service.ts
│   │       │
│   │       │   # ─── Orders & Billing ───
│   │       ├── orders/                   # Order management (40+ sub-components)
│   │       │   ├── order-create/         # Multi-step order creation
│   │       │   ├── order-detail/         # Order detail view
│   │       │   ├── order-items/          # Line items management
│   │       │   └── order.service.ts
│   │       ├── invoices/                 # Invoice management
│   │       ├── payments/                 # Payment tracking
│   │       ├── adminapprovals/           # Admin approval workflows
│   │       │
│   │       │   # ─── Product & Inventory ───
│   │       ├── produce/                  # Product catalog
│   │       ├── samples/                  # Sample packs
│   │       ├── lots/                     # Auction lots
│   │       ├── godowns/                  # Warehouse management
│   │       │
│   │       │   # ─── Reports & Analytics ───
│   │       ├── dashboard/                # Main dashboard
│   │       ├── admin-dashboard/          # Admin dashboard (role 9)
│   │       ├── agent-dashboard/          # Agent dashboard (role 4)
│   │       ├── reports/                  # General reports
│   │       ├── crm-reports/              # CRM analytics (FRT, funnel, aging)
│   │       ├── order-reports/            # Order analytics
│   │       │
│   │       │   # ─── Configuration & Admin ───
│   │       ├── users/                    # User management
│   │       ├── roles/                    # Role & permission management
│   │       ├── settings/                 # System settings
│   │       ├── companies/                # Company management
│   │       ├── templates/                # Email/SMS templates
│   │       ├── holiday-calendar/         # Holiday & leave management
│   │       │
│   │       │   # ─── Pricing & Configuration ───
│   │       ├── advanced-slabs/           # Pricing slabs
│   │       ├── shipping-slabs/           # Shipping rates
│   │       ├── commodity-rate/           # Commodity rates
│   │       ├── taxes/                    # Tax configuration
│   │       │
│   │       │   # ─── Authentication ───
│   │       ├── sessions/                 # Login, signup, OTP, password reset
│   │       └── offline/                  # Offline mode support
│   │
│   ├── environments/                     # Environment configurations
│   │   ├── environment.ts                # Development
│   │   ├── environment.prod.ts           # Production
│   │   └── environment.beta.ts           # Beta/staging
│   │
│   ├── assets/
│   │   ├── config/                       # Runtime API server configs
│   │   │   ├── config.dev.json           # Dev: http://climate.loc/index.php
│   │   │   ├── config.prod.json          # Prod: https://api.climatenaturals.com
│   │   │   └── config.beta.json          # Beta
│   │   ├── i18n/                         # Translation files (en.json)
│   │   ├── styles/                       # Global SCSS styles
│   │   ├── fonts/                        # Custom fonts
│   │   ├── images/                       # Static images
│   │   └── sounds/
│   │       └── notification.wav          # Push notification sound
│   │
│   ├── main.ts                           # Angular bootstrap entry
│   ├── index.html                        # HTML shell
│   └── firebase-messaging-sw.js          # Service worker for FCM
│
├── angular.json                          # Angular CLI configuration
├── package.json                          # Node dependencies
├── tsconfig.json                         # TypeScript configuration
├── tailwind.config.js                    # Tailwind CSS configuration
├── ngsw-config.json                      # Service Worker (PWA) configuration
└── karma.conf.js                         # Test runner configuration
```

---

## Feature Module Pattern

Each feature module under `views/` follows a consistent structure. Modules declare their own routing, components, and optional feature-specific services:

```
views/<feature-name>/
├── <feature-name>.module.ts              # Module declaration
├── <feature-name>-routing.module.ts      # Feature routes
├── <feature-name>.component.ts           # Root/list component
├── <feature-name>.component.html         # Template
├── <feature-name>.component.scss         # Styles
│
├── components/                           # Sub-components
│   ├── <sub-feature>/
│   │   ├── <sub-feature>.component.ts
│   │   ├── <sub-feature>.component.html
│   │   └── <sub-feature>.component.scss
│   └── ...
│
├── pop-ups/                              # Dialog/modal components
│   └── ...
│
└── services/                             # Feature-specific services
    └── <feature>.service.ts
```

Example — the WhatsApp module:

```
views/whatsapp/
├── whatsapp.module.ts
├── whatsapp-routing.module.ts
├── whatsapp.service.ts                   # 40+ API endpoint methods
├── chat-window/                          # Real-time chat interface
│   ├── chat-window.component.ts
│   ├── chat-window.component.html
│   └── chat-window.component.scss
├── conversations-list/                   # Conversation list with filters
├── customer-details/                     # Customer info panel in chat
└── pop-ups/                              # Chat-specific dialogs
```

---

## PHP Backend (`climate-api/`)

```
climate-api/
├── index.php                             # Front controller (entry point)
├── .htaccess                             # URL rewriting & HTTPS enforcement
├── .env                                  # Environment variables
├── composer.json                         # PHP dependencies
│
├── application/                          # ── CODEIGNITER APPLICATION ──
│   │
│   ├── config/                           # Configuration files
│   │   ├── autoload.php                  # Auto-loaded libraries/helpers
│   │   ├── config.php                    # Main config (jwt_key, SMTP, timezones)
│   │   ├── database.php                  # Database connection (MySQLi, utf8mb4)
│   │   ├── hooks.php                     # Hook definitions (pre_system, post_constructor)
│   │   ├── migration.php                 # Migration settings (timestamp-based)
│   │   ├── routes.php                    # URL routing (default CI conventions)
│   │   └── firebase-service-account.json # Firebase credentials
│   │
│   ├── controllers/                      # ── API CONTROLLERS (61) ──
│   │   │
│   │   │   # ─── Authentication ───
│   │   ├── LoginCtrl.php                 # Login, OTP, signup, password reset
│   │   │
│   │   │   # ─── CRM Core ───
│   │   ├── Accounts.php                  # Account CRUD, merge, addresses
│   │   ├── Contact.php                   # Contact management
│   │   ├── ContactHandles.php            # Phone/email/WhatsApp handles
│   │   ├── OpenConversations.php         # Conversation stage management
│   │   ├── ConversationTransfer.php      # Agent-to-agent transfers
│   │   ├── AssignmentHistory.php         # Assignment timeline & statistics
│   │   │
│   │   │   # ─── Communication ───
│   │   ├── Whatsapp.php                  # WhatsApp webhook & messaging
│   │   ├── WhatsappChat.php              # WebSocket real-time chat server
│   │   ├── TeleCommunication.php         # Phone/call integration
│   │   │
│   │   │   # ─── Orders & Billing ───
│   │   ├── Orders.php                    # Order lifecycle management
│   │   ├── Invoice.php                   # Invoice generation (PDF)
│   │   ├── Payments.php                  # Payment processing
│   │   ├── Adminapprovals.php            # Admin approval workflows
│   │   │
│   │   │   # ─── Reports ───
│   │   ├── DashBoard.php                 # Dashboard data
│   │   ├── ConversationReports.php       # CRM reports (FRT, funnel, aging)
│   │   ├── OrderReports.php              # Order analytics
│   │   ├── ReportExports.php             # Excel/CSV export
│   │   │
│   │   │   # ─── External Integrations ───
│   │   ├── ExternalApiController.php     # Third-party API (X-API-KEY)
│   │   ├── FirebaseController.php        # FCM token management
│   │   ├── Justdial.php                  # JustDial lead integration
│   │   ├── FbLeads.php                   # Facebook lead integration
│   │   │
│   │   │   # ─── System ───
│   │   ├── Cron.php                      # Scheduled cron jobs
│   │   ├── Migrate.php                   # Migration runner
│   │   └── ...
│   │
│   ├── models/                           # ── DATA MODELS (79+) ──
│   │   │
│   │   │   # ─── Core Data ───
│   │   ├── ProfileAccountsModel.php      # Account profiles (temp_tbl_accounts)
│   │   ├── ProfileContactsModel.php      # Contact profiles (temp_tbl_contacts)
│   │   ├── ProfileContactHandlesModel.php# Contact handles (temp_tbl_contact_handles)
│   │   ├── ProfileAddressModel.php       # Addresses (temp_tbl_addresses)
│   │   ├── AccountMergeRequestModel.php  # Account merging
│   │   ├── ContactMessageModel.php       # Incoming message pipeline
│   │   │
│   │   │   # ─── CRM ───
│   │   ├── OpenConversationsModel.php    # Conversations (tbl_open_conversations)
│   │   ├── ConversationTransferModel.php # Transfers
│   │   ├── ContactAssignmentHistoryModel.php
│   │   ├── OpportunitiesModel.php        # Sales opportunities
│   │   │
│   │   │   # ─── Orders ───
│   │   ├── OrdersModel.php               # Order operations (tbl_orders)
│   │   ├── OrderStatusLogsModel.php      # Status change logs
│   │   ├── PaymentsModel.php             # Payment operations
│   │   ├── InvoiceModel.php              # Invoice operations
│   │   │
│   │   │   # ─── Reports ───
│   │   ├── reports/
│   │   │   ├── AgentFRTReportModel.php
│   │   │   ├── ConversationAgingModel.php
│   │   │   ├── ConversationFunnelModel.php
│   │   │   ├── RevenueContributionModel.php
│   │   │   └── ...
│   │   │
│   │   │   # ─── System ───
│   │   ├── LoginModel.php                # Authentication
│   │   ├── WhatsappModel.php             # WhatsApp operations
│   │   ├── CronModel.php                 # Cron job logic
│   │   └── ...
│   │
│   ├── hooks/                            # ── REQUEST HOOKS ──
│   │   └── permission_check.php          # JWT auth + capability RBAC + CORS
│   │
│   ├── libraries/                        # ── CUSTOM LIBRARIES ──
│   │   ├── Risposta.php                  # JSON encoding (numeric precision)
│   │   ├── Chat_websocket.php            # Ratchet WebSocket server
│   │   ├── LibRedisQueue.php             # Redis queue operations
│   │   ├── Firebase.php                  # FCM push notifications
│   │   ├── Queue_helper.php              # Background job queue
│   │   ├── XlsxWriter.php               # Excel file generation
│   │   └── ...
│   │
│   ├── helpers/                          # ── HELPER FUNCTIONS ──
│   │   ├── agent_assignment_helper.php   # 4-level agent assignment
│   │   ├── phone_number_helper.php       # Phone normalization
│   │   ├── handle_validation_helper.php  # Contact handle validation
│   │   ├── filters_helper.php            # Report query filter building
│   │   └── jwt_helper.php               # JWT utilities
│   │
│   ├── migrations/                       # ── DATABASE MIGRATIONS (326) ──
│   │   ├── 20251223000001_*.php          # Initial schema
│   │   ├── ...
│   │   └── 20260311160036_*.php          # Latest migration
│   │
│   ├── views/                            # Server-side views (minimal — API-focused)
│   ├── core/                             # Custom CI core classes
│   ├── cache/                            # Application cache
│   ├── logs/                             # Application logs
│   └── third_party/                      # Third-party CI libraries
│
├── system/                               # CodeIgniter framework core (do not modify)
│
├── pg/                                   # ── PAYMENT GATEWAY ──
│   ├── AWLMEAPI.php                      # Vtransact/AWLME payment API
│   ├── ReqMsgDTO.php                     # Request DTO
│   ├── ResMsgDTO.php                     # Response DTO
│   ├── VtransactSecurity.php             # Payment encryption
│   └── meTrnSuccess.php                  # Payment success handler
│
├── vendor/                               # Composer packages
└── scripts/
    └── truncate_tables.sql               # DB truncation utility
```

---

## Frontend Module Reference

### CRM & Communication

| Module | Route | Purpose |
|--------|-------|---------|
| `whatsapp` | `/communications` | Full WhatsApp chat interface — conversations list, chat window, customer details panel, notes, follow-ups |
| `leads` | `/leads` | Lead management — contact list, personal/demographic details, lead transfer |
| `customer-contacts` | `/contacts` | Customer contact records, assignment history, timeline |
| `opportunity-contacts` | `/opportunities` | Sales opportunity tracking |
| `conflict-resolution` | `/conflict-resolution` | CRM data conflict resolution |

### Accounts & Orders

| Module | Route | Purpose |
|--------|-------|---------|
| `customers` | `/accounts` | Account CRUD, edit profiles, shipping addresses, account merge |
| `orders` | `/orders` | Full order lifecycle — create, track, fulfill, approve |
| `invoices` | `/invoices` | Invoice generation and management |
| `payments` | `/payments` | Payment tracking and processing |
| `adminapprovals` | `/adminapprovals` | Admin approval workflows (discounts, ship-without-pay) |

### Dashboards & Reports

| Module | Route | Purpose |
|--------|-------|---------|
| `dashboard` | `/dashboard` | Main KPI dashboard |
| `admin-dashboard` | `/admindashboard` | Sales admin team dashboard (role 9) |
| `agent-dashboard` | `/agentdashboard` | Sales agent personal dashboard (role 4) |
| `crm-reports` | `/crmreports` | CRM analytics — FRT, funnel, aging, revenue, outcomes |
| `order-reports` | `/orderreports` | Order analytics |

### Configuration & Admin

| Module | Route | Purpose |
|--------|-------|---------|
| `users` | `/users` | User management and role assignment |
| `roles` | `/roles` | RBAC role and capability management |
| `settings` | `/settings` | Application settings |
| `companies` | `/companies` | Multi-company management |
| `templates` | `/templates` | Email & SMS template management |
| `holiday-calendar` | `/holiday-calendar` | Holiday calendar and leave management |

### Pricing & Reference Data

| Module | Route | Purpose |
|--------|-------|---------|
| `advanced-slabs` | `/slabs` | Pricing tier configuration |
| `shipping-slabs` | `/shippingrates` | Shipping rate tiers |
| `taxes` | `/taxes` | Tax rate configuration |
| `couriers` | `/couriers` | Shipping courier management |
| `states` | `/states` | State/region reference data |
| `countries` | `/countries` | Country reference data |

---

## Cross-References

| Document | Path |
|----------|------|
| System Architecture Overview | `01-system-architecture/overview.md` |
| Frontend Architecture | `01-system-architecture/frontend-architecture.md` |
| Backend Architecture | `01-system-architecture/backend-architecture.md` |
| Database Schema | `03-database-design/schema-overview.md` |
| Adding Modules | `08-development-guidelines/adding-modules.md` |
| Coding Standards | `08-development-guidelines/coding-standards.md` |
