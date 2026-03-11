# Climate CRM — Features & Descriptions

**Currency**: INR (Indian Rupee)
**Platform**: Web (PWA) — Angular 17 + CodeIgniter 3
**Company**: The Spice Factory (Climate Naturals)

---

## Lead Management & Conversations

### Multi-Source Lead Capture
- Leads arrive from six sources: WhatsApp messages, JustDial webhooks, IndiaMart API sync (cron-based), Facebook Lead Ads webhooks, website forms, and manual entry (walk-in, referral, phone call)
- Each source has a dedicated entry point — WhatsApp via `Whatsapp::webhookCloudApi()`, JustDial via `Justdial::receiveLead()`, Facebook via `Facebookleads::webhook()`, IndiaMart via `Cron::indiaMartLeads()`
- All sources converge to `ContactMessageModel::processIncomingMessage()` which handles contact creation, conversation creation, and agent assignment uniformly
- Source attribution is tracked in `tbl_contact_sources` and linked to every conversation for funnel analysis

### Conversation Lifecycle
- Conversations progress through six stages: New → Attempted → Contacted → Nurturing → Qualified/Unqualified → Converted
- Two transitions are automatic — `new` → `attempted` when the agent sends the first message, and `attempted` → `contacted` when the customer replies
- The remaining transitions (nurturing, qualified, unqualified) are manual actions by the agent
- Closing a conversation as unqualified requires selecting one of 14+ disposition reasons (price_too_high, not_interested, rnr_1/2/3, competitor_chosen, wrong_number, duplicate, etc.)
- Creating an order from a conversation automatically closes it as "converted" and creates a linked opportunity record

### Follow-Up System
- Agents can schedule follow-ups with a date, time, and notes for any conversation
- A mandatory follow-up queue forces agents to schedule a follow-up for contacted/nurturing conversations before moving to the next lead
- The `Cron::processScheduledFollowups()` job runs every 5 minutes to process due follow-ups and send push notifications to assigned agents
- Follow-ups appear in a dedicated "Scheduled" tab in the conversations list

---

## WhatsApp Integration

### Messaging
- Full WhatsApp Business Cloud API integration via webhook — both inbound and outbound messaging
- Supported inbound message types: text, image, document, video, audio, button, reaction, location
- Outbound messaging: text messages, template messages (pre-approved by WhatsApp), rate update messages, and media messages
- Media files are downloaded from WhatsApp's Media API and stored in AWS S3, served to the frontend via CloudFront CDN
- Message delivery status tracking: sent → delivered → read → failed, updated in real-time via status webhooks

### Real-Time Chat
- WebSocket-powered real-time delivery — messages appear in the chat window instantly without polling
- Redis queue acts as a broker between the PHP request lifecycle (short-lived) and the persistent WebSocket server
- Agents see typing indicators, unread counts, and message status icons (single tick, double tick, blue tick)
- The chat window supports inline notes (visible only to agents), call status logging, and follow-up scheduling

### Phone Number Normalization
- All Indian phone numbers are normalized to 10-digit format by stripping country code (+91/91), leading zeros, and spaces
- This normalization runs on every inbound message and handle lookup, ensuring consistent database matching regardless of how the number was originally entered

---

## Accounts & Contacts

### Account Management
- Accounts represent companies or individual customers with business details: GST number, FSSAI license, business type, industry
- Each account can have multiple contacts, multiple addresses (billing and shipping), and an account owner (assigned agent)
- Account creation is transactional — account, default contact, and primary handle are created in a single database transaction
- Account merge workflow handles duplicate detection and consolidation: select primary account, transfer all contacts/conversations/orders, mark duplicate as merged

### Contact Handles
- Every contact can have multiple handles: phone numbers, email addresses, social IDs (Instagram, Telegram)
- Handle uniqueness is enforced — no two active contacts can share the same phone number or email
- WhatsApp capability is tracked per phone handle with an `is_whatsapp` flag, set automatically when a WhatsApp message is received from that number
- Handle lookup is the primary mechanism for routing inbound messages to the correct contact and conversation

---

## Agent Assignment

### 4-Level Priority System
- When a new conversation is created, the `AgentAssignmentHelper` assigns an agent using four priority levels, checked in order:
  1. **Account owner** — if the contact belongs to an account with an assigned owner, that owner's agent gets the conversation
  2. **Open conversation agent** — if the contact has another open conversation with an active agent, the same agent is assigned
  3. **Previous conversation agent** — if the contact had a closed conversation, the most recent handling agent is assigned
  4. **Round-robin** — if none of the above apply, the next available agent in the rotation gets the conversation
- Round-robin checks agent availability: active status in `tbl_telecommunication_agents`, not deleted in `tbl_users`, no full-day leave, and within working hours (with half-day leave awareness)

### Conversation Transfer
- Agents can transfer conversations to other agents with a mandatory transfer reason and optional notes
- Transfers can scope to a single conversation, all conversations for an account, or a specific opportunity
- Every transfer is recorded in `tbl_unified_transfer_log` and `tbl_contact_assignment_history` for complete audit trail
- Both the sending and receiving agents get real-time WebSocket notifications

### Assignment History
- Complete timeline of all assignment events for every contact — initial assignment, transfers, reassignments, round-robin rotations, account merges
- Each event records: who was assigned, who was the previous agent, assignment method (manual/automatic/round_robin), reason, and confidence level
- Visual timeline component in the frontend with color-coded icons per assignment type
- Workload statistics endpoint shows per-agent metrics: total assignments, active conversations, transfers in/out

---

## Order Management

### Order Creation
- Multi-step wizard: select/create account → add products with quantities and pricing → select billing/shipping addresses → review and confirm
- Tax calculation is automatic based on address: CGST + SGST for same-state billing, IGST for inter-state billing
- Discounts above a configurable threshold require admin approval via `tbl_admin_approvals` before the order can proceed
- Creating an order from a conversation automatically closes the conversation as "converted" and creates a linked CRM opportunity

### Order Lifecycle
- Orders progress through a state machine: Draft → Confirmed → Final → For Despatch → Despatched → Delivered
- Cancellation has its own path: any stage → Cancellation Pending → Cancelled
- Each status transition is logged in `tbl_order_status_logs` with the user who made the change, timestamp, and notes
- Both domestic and international order types are supported, with currency conversion for international orders

### Invoicing
- Tax invoice PDF generation via wkhtmltopdf (knp-snappy library) — uploaded to S3, served via pre-signed URL
- Proforma invoice generation for quotes
- E-Invoice integration with GST portal for compliance
- E-Way Bill generation for goods transport above the threshold
- Invoices can be sent directly to customers via WhatsApp as document messages

### Payment Tracking
- Payment recording with multiple modes: bank transfer, UPI, cash, cheque
- Partial payment support — order tracks `amount_paid`, `pending_amount`, and `payment_status` (no payment / partially paid / fully paid)
- Ship-without-pay approval workflow — agent requests, admin approves/rejects via `tbl_admin_approvals`

---

## Reporting & Analytics

### CRM Reports
- **First Response Time (FRT)**: measures how quickly agents respond to new leads, with per-agent and per-source breakdowns
- **Conversation Funnel**: tracks conversion rates through each stage (new → attempted → contacted → qualified → converted)
- **Conversation Aging**: identifies stale conversations that haven't had activity in configurable time periods
- **Unqualified Analysis**: breakdown of unqualified dispositions by reason, agent, and source
- **Outcome Reports**: overall conversation outcomes (converted, unqualified, still open)
- **Revenue Reports**: revenue attribution by agent, source, and time period
- **Agent Activity**: per-agent metrics including messages sent, conversations handled, orders created

### Dashboards
- Main dashboard with key KPIs, charts, and summary widgets
- Admin dashboard with team-wide metrics and performance comparisons
- Agent dashboard with personal metrics, pending follow-ups, and conversation queue

### Export
- Excel and CSV export for all report types
- Chart visualizations using ngx-echarts and Chart.js

---

## Role-Based Access Control

### Capability System
- Permissions are stored as capabilities in `tbl_capability` with `module_name` and `capability` fields
- Capabilities are assigned to roles via `tbl_role_capability` (many-to-many)
- Every controller method declares its required capability using a PHP DocBlock `@capability` annotation
- The `PermissionCheck` hook reads the annotation via PHP Reflection and checks it against the user's JWT capabilities
- Super admin users (`is_super == "Yes"`) bypass all capability checks
- The `hasPermission` pipe in Angular templates controls UI visibility based on capabilities

### Roles
- Four default roles: Super Admin, Admin, Manager, Agent
- Custom roles can be created with any combination of capabilities
- Role hierarchy is implicit — capabilities determine access, not role names

---

## Authentication & Security

### JWT Authentication
- HS512 algorithm with a server-side secret key (`$_SERVER['JWT_KEY']`)
- Token expiration: 48 hours from issue
- JWT payload includes: user_id, user_name, role_id, capabilities (nested object), login_hash, is_super
- Single-session enforcement: each login generates a unique `login_hash` stored in `tbl_login`; if a user logs in elsewhere, the old session's hash no longer matches and is terminated

### Session Management
- Server-side inactivity tracking via `tbl_user_last_request_log` — the hook compares last request time against `tbl_settings.inactivity_setting` (in minutes)
- Frontend cross-tab activity sync via `localStorage.lastActivityTime` — all tabs share the same activity timestamp
- On session termination (inactivity, multi-device, credential change), the `ErrorInterceptor` clears localStorage and redirects to the login page with an explanatory snackbar message

### CORS
- Dynamic origin allowance — the `preflight()` hook sets `Access-Control-Allow-Origin` to the requesting origin
- Supports GET, POST, OPTIONS methods
- Credentials enabled for cookie-based session support

---

## Notifications

### Push Notifications
- Firebase Cloud Messaging (FCM) via `@angular/fire` for browser push notifications
- Notifications triggered for: new messages, conversation transfers, follow-up reminders, order status changes
- Background notification handling via `firebase-messaging-sw.js` service worker

### Real-Time Updates
- WebSocket connections per agent session for instant message delivery
- Redis pub/sub channels for conversation events: new messages, stage changes, transfers, agent updates
- Cross-tab communication via localStorage events for activity synchronization

---

## External Integrations

### JustDial
- Webhook-based lead capture with API key authentication (`tbl_api_auth`)
- Raw lead data stored in `tbl_justdial_leads` before processing into contacts and conversations
- Leads queued via Redis for real-time UI notifications to the assigned agent

### Facebook Lead Ads
- Webhook receiver with HMAC-SHA256 signature verification
- Lead form field data parsed and stored in `tbl_facebook_leads`
- Automatic contact creation and conversation assignment

### IndiaMart
- Cron-based pull integration — `Cron::indiaMartLeads()` calls the IndiaMart API periodically
- Deduplication by IndiaMart lead ID to prevent duplicate imports
- Syncs from the last successful import timestamp stored in settings

### External API (X-API-KEY)
- REST API for third-party systems to push opportunities and profiles
- Authentication via `X-API-KEY` header validated against `tbl_justdial_credentials`
- Supports creating accounts, contacts, and opportunities in a single call

---

## Infrastructure

### AWS Services
- **S3**: File storage for WhatsApp media (images, documents, audio, video), invoice PDFs, profile photos, and document uploads
- **CloudFront**: CDN delivery of all S3 files at `d1r95e2xq05b34.cloudfront.net`
- **SES**: Transactional email for password resets, order confirmations, and notifications (ap-south-1 region)

### Redis
- Message queue for real-time WebSocket delivery (channel: `message_queue`)
- Pub/sub for broadcasting conversation events to multiple connected agents
- Work hours caching for round-robin assignment performance

### Database
- MySQL/MariaDB with `utf8mb4_unicode_ci` character set (supports emojis in WhatsApp messages)
- 300+ tables with `tbl_` and `temp_tbl_` prefixes
- 326 timestamp-based migrations managed by CodeIgniter's migration system

### Cron Jobs
- Follow-up processing (every 5 minutes)
- IndiaMart lead sync (every 15 minutes)
- Order confirmation emails (every 10 minutes)
- Exchange rate updates (daily)
- Agent FRT summary calculation (daily at 00:30)
- Conversation aging snapshot (daily at 06:00)

---

## Frontend Architecture

### Angular 17
- 48 lazy-loaded feature modules via `loadChildren` for optimal initial load time
- All components use `ChangeDetectionStrategy.OnPush` with manual `cd.detectChanges()` for performance
- RxJS BehaviorSubject-based state management — no NgRx
- Angular Material 17 for UI components with Tailwind CSS for utility styling
- Shared module provides common components, pipes (`hasPermission`, `relativeTime`, `orderStatus`), directives, and services
- `rispostaAnimations` shared across all components for consistent motion design

### PWA
- Service Worker registered via `@angular/service-worker` for offline caching
- Background sync support for API calls during intermittent connectivity
- Installable web app on mobile devices
