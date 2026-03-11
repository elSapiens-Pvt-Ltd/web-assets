# Feature List

## Lead & Conversation Management

### Lead Capture
- **Multi-channel lead ingestion**: WhatsApp, JustDial, IndiaMart, Facebook, phone calls, manual entry
- **Automatic conversation creation**: Inbound messages auto-create conversations in the CRM
- **Lead source tracking**: Every conversation tracks its origin via `tbl_contact_sources`
- **Duplicate detection**: Phone number normalization prevents duplicate contacts (e.g., `0` prefix → `91` prefix)

### Conversation Lifecycle
- **Stage progression**: New → Attempted → Contacted → Nurturing → Qualified / Unqualified
- **Priority classification**: Hot / Warm / Cold with visual indicators
- **Disposition tracking**: 14+ unqualified reasons (price too high, competitor chosen, budget issues, etc.)
- **Call attempt tracking**: `call_attempts` counter per conversation
- **Follow-up scheduling**: Agents schedule follow-ups with dates; cron processes reminders
- **Notes system**: Internal notes attached to conversations for team collaboration

### Conversation Filters
- Filter by stage, priority, agent, date range, disposition status
- Filter state persisted to localStorage for session continuity
- Saved filter presets

---

## WhatsApp Integration

### Inbound Messaging
- **WhatsApp Business Cloud API** webhook integration
- Real-time message delivery to agent via WebSocket
- Supported types: text, image, video, audio, document, contact card, reactions, buttons
- Media download and storage on AWS S3
- Message delivery and read receipt tracking

### Outbound Messaging
- Agent sends messages from CRM chat window
- Template message support (Meta-approved templates)
- Rate update broadcasts to opted-in customers
- Media/file attachments via S3 pre-signed URLs

### Real-Time Chat
- WebSocket-based live chat interface
- Conversation list with unread message indicators
- Customer details side panel
- Call status indicators (calling, ringing, on call, missed, etc.)
- Multi-tab awareness

---

## Customer & Account Management

### Account Management
- **Account types**: Business and Individual
- **Business details**: GST number, FSSAI number, business type, business category
- **Financial summary**: Total orders, total revenue, total paid, order count
- **Distribution type**: Retailer / Wholesaler classification
- **Export flag**: Identifies export customers
- **Account scoring**: Numeric score for customer value
- **Region tracking**: Geographic region assignment

### Contact Management
- Multiple contacts per account
- Primary contact designation
- Contact handles: phone, email, WhatsApp, Facebook, Instagram
- Handle verification status (email_verified, mobile_verified)
- Communication preferences: daily rate WhatsApp, email opt-in/out

### Address Management
- Multiple addresses per account
- Address types: billing, shipping, billing & shipping
- Address-specific GST numbers
- Geolocation support (latitude, longitude)
- State and country references

### Account Merge
- Merge duplicate accounts (source → target)
- Approval workflow: request → review → approve/reject
- Transfers contacts, addresses, orders, conversations
- Full audit trail in merge request logs

---

## Order Processing

### Order Creation
- **Multi-step wizard**: Account → Items → Addresses → Review → Confirm
- **Domestic & international** order support
- **Multi-currency**: INR default, configurable for international
- **Order via**: Online / Offline classification

### Order Lifecycle
- **Status flow**: Draft → Confirmed → Final → Despatched → Delivered
- **Cancellation**: Cancellation Pending → Cancelled
- **Payment tracking**: No Payment → Partially Paid → Fully Paid
- **Fulfillment**: Pending → For Despatch → Despatched
- **Shipping**: Not Shipped → In Transit → Out for Delivery → Delivered / Returned

### Tax & Invoicing
- **GST calculation**: CGST + SGST (intra-state) or IGST (inter-state)
- **State cess**: Additional state-level tax
- **E-invoice generation**: Government-compliant electronic invoicing
- **E-way bill**: Transport documentation
- **Proforma invoices**: Pre-order pricing documents

### Order Features
- Admin approval workflows for special cases (discounts, credit)
- Warehouse (godown) assignment for fulfillment
- Courier selection and shipping management
- Order timeline/history tracking
- Packing and shipping details
- Ship-without-pay approval flow

---

## Sales Pipeline & Opportunities

### Opportunity Tracking
- Link opportunities to accounts and contacts
- Track actual vs. committed pricing
- Product quantity and currency tracking
- Agent allocation per opportunity
- Lead conversion date tracking

### Pipeline Stages
- Opportunity status progression
- Order mode: domestic / international
- Contact source attribution

---

## Reporting & Analytics

### CRM Reports
- **First Response Time (FRT)**: Measures agent response speed
- **Conversation Funnel**: Lead stage progression visualization
- **Conversation Aging**: How long conversations remain open
- **Unqualified Analysis**: Patterns in disqualified leads
- **Outcome Report**: Win/loss/pending deal analysis
- **Revenue Contribution**: Revenue by agent, source, region
- **Agent Activity**: Per-agent performance metrics

### Order Reports
- Daily confirmed orders summary
- Order analytics by status, courier, warehouse
- Weight and grade-wise reports

### Export
- Excel (XLSX) export via XlsxWriter
- CSV export
- Date range selection for all reports

---

## Agent & Assignment Management

### Assignment Features
- Initial assignment (auto or manual)
- Agent-to-agent transfer with reason and notes
- Round-robin distribution
- Reassignment by managers
- Assignment history timeline per contact
- Transfer count tracking

### Workload Management
- Agent workload dashboard
- Active conversation count per agent
- Historical workload analysis by date range
- Most-transferred contacts identification

---

## User & Access Control

### Role-Based Access Control (RBAC)
- Granular capability-based permissions
- DocBlock annotation enforcement on every API endpoint
- Capabilities: `module.action` format (e.g., `customers.default`)
- Super admin bypass for all capability checks
- Menu-linked capabilities for UI visibility

### User Roles
| Role | Dashboard | Description |
|------|-----------|-------------|
| Super Admin | `/dashboard` | Full system access |
| Sales Admin (9) | `/admindashboard` | Team management, all reports |
| Sales Agent (4) | `/agentdashboard` | Own conversations and tasks |
| Standard User | `/dashboard` | Configured per capabilities |
| Customer | Customer Portal | Limited external access |

### Session Management
- JWT-based authentication (HS512, 48-hour expiry)
- Inactivity timeout (configurable)
- Single-session enforcement (login hash)
- Cross-tab session synchronization
- Auto-logout with warning dialog

---

## Notifications

### Push Notifications
- Firebase Cloud Messaging (FCM) integration
- Browser push notifications
- Notification sound alerts (`notification.wav`)
- Topic-based subscription/unsubscription
- Notification count in topbar

### In-App Notifications
- Dynamic notification component
- 10-second display timeout
- Title, message, and action link
- Notification history panel

---

## Product Catalog

### Product Management
- Product CRUD with grades
- Packing options and sizes
- Sample product management
- Grade-based rate configuration
- Commodity rate tracking

### Pricing
- Advanced pricing slabs/tiers
- Shipping rate slabs
- Grade-specific pricing
- Multi-currency support

---

## Warehouse & Logistics

### Warehouse Management
- Multiple godown/warehouse support
- Godown assignment per order
- Godown change tracking with notes

### Shipping & Courier
- Courier partner management
- Shipping rate configuration
- Preferred courier per order
- Shipping status tracking

---

## Bidding/Auction System

### Lot Management
- Auction lot creation and management
- Bid lot configuration
- Bidding settings (rules, timing)
- Registered bidder tracking
- Highest bidder identification

---

## Calendar & Scheduling

### Holiday Calendar
- Company holiday management
- Employee leave tracking
- Working hours configuration

### Scheduled Tasks
- Task scheduling interface
- Cron job management
- Automated follow-up processing
- Aging snapshot generation
- FRT summary calculations

---

## Multi-Company Support

- Company selection and switching
- Company-scoped data queries
- CompanyId header in all API requests
- Per-company settings and configuration

---

## External Integrations

### WhatsApp Business Cloud API
- Webhook-based message receiving
- Template message sending
- Media upload/download
- Delivery/read receipts

### JustDial
- Lead capture integration
- API key authentication
- Automatic conversation creation

### IndiaMart
- Lead synchronization
- Cron-based lead pulling

### Facebook
- Lead form integration
- Webhook-based lead capture

### Google Sheets
- Data export/import
- Queue-based processing

### Payment Gateway (Vtransact/AWLME)
- Online payment processing
- Refund handling
- Card status checking
- Encrypted transaction security

### AWS Services
- **S3**: File/media storage
- **CloudFront**: CDN for static assets
- **SES**: Transactional email

### Firebase
- Push notifications (FCM)
- Device token management

---

## PWA & Offline Support

- Service Worker for offline capability
- App version update detection
- Automatic update prompts
- Offline mode page
