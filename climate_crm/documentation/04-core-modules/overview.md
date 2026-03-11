# Core Modules Overview

> Module: `climate/modules`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Module Map](#module-map)
2. [Contacts & Accounts](#contacts--accounts)
3. [Conversations](#conversations)
4. [WhatsApp Integration](#whatsapp-integration)
5. [Assignment & Agent Management](#assignment--agent-management)
6. [Messaging System](#messaging-system)
7. [Order Management](#order-management)
8. [Reporting & Analytics](#reporting--analytics)
9. [Holiday Calendar & Leave Management](#holiday-calendar--leave-management)
10. [Product Catalog](#product-catalog)
11. [Cross-References](#cross-references)

---

## Module Map

The Climate CRM is organized around nine core modules, each with its own frontend Angular feature module and backend CodeIgniter controller(s):

```
┌─────────────────────────────────────────────────────────────┐
│                     Climate CRM Modules                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Contacts &  │  │Conversations │  │     WhatsApp      │  │
│  │  Accounts    │  │              │  │   Integration     │  │
│  │              │  │  Lifecycle   │  │                   │  │
│  │  Account →   │  │  Stage mgmt  │  │  Webhook, Chat,   │  │
│  │  Contact →   │  │  Follow-ups  │  │  Templates, Media │  │
│  │  Handle      │  │  Disposition │  │                   │  │
│  └──────────────┘  └──────────────┘  └───────────────────┘  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Assignment  │  │  Messaging   │  │      Orders       │  │
│  │  & Agents    │  │   System     │  │                   │  │
│  │              │  │              │  │  Creation, Tax,    │  │
│  │  Round-robin │  │  WebSocket   │  │  Invoice, Ship,   │  │
│  │  Transfer    │  │  FCM Push    │  │  Payments, Admin   │  │
│  │  Workload    │  │  Call status │  │  Approvals        │  │
│  └──────────────┘  └──────────────┘  └───────────────────┘  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Reporting   │  │   Holiday    │  │     Product       │  │
│  │  & Analytics │  │   Calendar   │  │     Catalog       │  │
│  │              │  │              │  │                   │  │
│  │  FRT, Funnel │  │  Holidays    │  │  Produce, Grades  │  │
│  │  Aging, Rev  │  │  Leaves      │  │  Slabs, Rates     │  │
│  │  Export      │  │  Work hours  │  │                   │  │
│  └──────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

| Module | Frontend Route | Backend Controller(s) | Primary Tables |
|--------|---------------|----------------------|----------------|
| Contacts & Accounts | `/accounts`, `/contacts`, `/leads` | `Accounts`, `Customers`, `Contact`, `ContactHandles` | `temp_tbl_accounts`, `temp_tbl_contacts`, `temp_tbl_contact_handles` |
| Conversations | `/whatsapp` | `OpenConversations`, `ConversationTransfer` | `tbl_open_conversations` |
| WhatsApp Integration | `/whatsapp` | `Whatsapp`, `WhatsappChat` | `tbl_whatsapp_messages`, `tbl_whatsapp_callback` |
| Assignment & Agents | `/contacts` | `AssignmentHistory` | `tbl_contact_assignment_history` |
| Messaging System | `/whatsapp` | `Whatsapp`, `WhatsappChat` | `tbl_whatsapp_messages`, `tbl_conversation_messages` |
| Order Management | `/orders` | `Orders`, `OrderReports` | `tbl_orders`, `tbl_order_items`, `tbl_order_data` |
| Reporting & Analytics | `/crm-reports`, `/dashboard` | `ConversationReports`, `DashBoard`, `ReportExports` | Report models (7 dedicated) |
| Holiday Calendar | `/holiday-calendar` | `HolidayCalendar` | `tbl_company_holidays`, `tbl_user_leaves` |
| Product Catalog | `/produce`, `/slabs`, `/rates` | `Produce`, `Slabs`, `GradeSettings` | `tbl_produces` |

---

## Contacts & Accounts

Manages customer accounts and the individual contacts within them. An **account** represents a business or individual customer, while **contacts** are the people associated with that account. Each contact can have multiple **handles** (phone numbers, emails, WhatsApp numbers).

```
Account (temp_tbl_accounts)
├── Contact 1 (temp_tbl_contacts)
│   ├── Phone Handle (temp_tbl_contact_handles)
│   ├── Email Handle (temp_tbl_contact_handles)
│   └── WhatsApp Handle (temp_tbl_contact_handles)
├── Contact 2
│   └── ...
├── Billing Address (temp_tbl_accounts_address)
└── Shipping Address (temp_tbl_accounts_address)
```

**Frontend Components**: Account List (`/accounts`), Edit Account with tabs, Merge Account dialog, Contact List, Assignment History Dialog, Assignment Timeline, All Contacts (`/leads`), Create Profile flow.

**Backend Controllers**: `Accounts` (createAccount transaction), `Customers` (CRUD with pagination), `Contact` (CRUD), `ContactHandles` (validation for calls/messages).

**Business Rules**: Handle values are globally unique per type. GST numbers are validated for uniqueness. Account creation uses database transactions. Phone numbers are normalized (leading `0` → `91` for Indian numbers). Account merge transfers contacts, addresses, orders, and conversations, then closes the source account.

See [contacts-accounts.md](contacts-accounts.md) for full details.

---

## Conversations

Conversations are the central CRM entity representing an ongoing engagement with a customer. They track the lifecycle of a lead from initial contact through qualification or disqualification.

### Stage Progression

```
NEW → ATTEMPTED → CONTACTED → NURTURING → QUALIFIED / UNQUALIFIED
```

| Stage | Description | Trigger |
|-------|-------------|---------|
| `new` | Lead just arrived | Auto on conversation creation |
| `attempted` | Agent tried to reach out | Agent marks manually |
| `contacted` | Successful first communication | Agent marks after response |
| `nurturing` | Ongoing engagement | Agent marks during follow-up |
| `qualified` | Ready for order | Auto on order creation, or manual |
| `unqualified` | Lead disqualified | Agent marks with disposition reason |

The `OpenConversations::updateStage()` method handles stage transitions and auto-closes conversations marked as unqualified:

```php
public function updateStage()
{
    $request = json_decode(file_get_contents('php://input'), true);
    $conversationId = $request['conversation_id'];
    $stage = $request['stage'];
    $dispositionStatus = $request['disposition_status'] ?? null;

    $success = $this->_conversations->updateConversationStage(
        $conversationId, $stage, $dispositionStatus, $agentId
    );

    if ($success) {
        // If marked as unqualified, close the conversation
        if ($stage === 'unqualified') {
            $this->_conversations->closeConversation($conversationId);
        }

        // Push to queue for real-time updates
        $this->queue->push($stageData, 'conversation_stage_update');
    }
}
```

**Conversation Types**: `lead` (initial contact), `opportunity` (qualified lead), `customer` (existing customer).

**Priority**: `hot` (red), `warm` (orange), `cold` (blue).

**Disposition Statuses** (required when closing as unqualified): `rnr1`/`rnr2`/`rnr3`, `not_interested`, `price_too_high`, `wrong_timing`, `need_approval`, `competitor_chosen`, `budget_issues`, `decision_maker_unavailable`, `need_discount`, `credit_needed`, `need_more_time`, `customer_need_cod`, `non_contact`, `invalid`, `other`.

See [conversations.md](conversations.md) for full details.

---

## WhatsApp Integration

Full WhatsApp Business Cloud API integration enabling agents to communicate with customers in real-time through the CRM interface.

```
Customer WhatsApp ──► Meta Cloud API ──► Backend Webhook ──► Database + Redis
                                                                    │
                                                              WebSocket broadcast
                                                                    │
                                                              Agent UI (Chat Window)
```

**Inbound**: Webhook receives message → parse type → download media to S3 → store in `tbl_whatsapp_messages` → create/update conversation → push via Redis/WebSocket → FCM notification to agent.

**Outbound**: Agent types in chat → WebSocket `OutgoingChat` event → send via WhatsApp Cloud API → store in database → delivery/read receipts update status.

**Supported Types**: text, image, video, audio, document, contact cards, template messages, rate update broadcasts.

**Key Endpoints**: `POST /whatsapp/webhookCloudApi` (webhook), `POST /whatsapp/sendTextMessage`, `POST /whatsapp/sendTemplateMessage`, `POST /whatsapp/mediaUpload`, `POST /whatsapp/sendRateUpdates`.

See [whatsapp-integration.md](whatsapp-integration.md) for full details.

---

## Assignment & Agent Management

Tracks how contacts and conversations are assigned to agents, including transfers, reassignments, and workload distribution. The `tbl_contact_assignment_history` table stores every assignment event.

**Assignment Types**: `initial`, `transfer`, `reassignment`, `round_robin`, `contact_merged`, `contact_discarded`, `contact_reactivated`.

**Assignment Methods**: `manual`, `automatic`, `round_robin`, `system`.

The `AssignmentHistory` controller provides a paginated timeline:

```php
class AssignmentHistory extends CI_Controller
{
    /**
     * GET /AssignmentHistory/timeline/{contact_id}?limit=20&offset=0
     * @capability contacts.view_assignment_history
     */
    public function timeline($contact_id = null)
    {
        $result = $this->ContactAssignmentHistoryModel->getContactTimelinePaginated(
            $contact_id, $limit, $offset
        );
        echo Risposta::json_encode(['success' => true, 'data' => $result]);
    }
}
```

**Backfill System**: Legacy data is backfilled from `legacy_whatsapp`, `legacy_transfer_log`, `open_conversations`, `unified_transfer_log`, and `migration_contact_merge` with confidence levels (high/medium/low).

See [assignment-management.md](assignment-management.md) for full details.

---

## Messaging System

Unified multi-channel communication — WhatsApp, phone calls, email — all linked to conversations and contacts. Messages are stored centrally in `tbl_whatsapp_messages` with a `message_source` discriminator (`whatsapp`, `call`, `email`, `system`).

**Real-Time**: WebSocket connection with `auth`, `join`, `outgoing`, `timer` message types. Auto-reconnect on disconnect (except code `3001`).

**Call Integration**: Call status tracked in real-time via WebSocket with visual indicators in the topbar (`TopbarService.callTip$`). Statuses: Call Initiated, Calling, Ringing, On Call, Call Missed, Call Ended, Incoming Call, Error. Ended/Error states auto-clear after 4 seconds.

**Push Notifications**: Firebase Cloud Messaging (FCM) delivers notifications to agents. Foreground: play sound + show 10-second popup via `NotificationComponent`. Background: handled by Service Worker.

**Notes & Follow-ups**: Internal notes (`/whatsapp/saveNotes`) visible only to agents. Follow-ups scheduled by agents and processed by `Cron::processScheduledFollowups` which sends FCM reminders.

See [messaging-system.md](messaging-system.md) for full details.

---

## Order Management

Complete order lifecycle management from creation through fulfillment and delivery. The orders module is the most complex frontend module with 40+ sub-components.

### Status State Machine

```
DRAFT → CONFIRMED → FINAL → FOR DESPATCH → DESPATCHED → DELIVERED
                        └──► CANCELLATION PENDING → CANCELLED

Payment:   No Payment → Partially Paid → Fully Paid
Shipping:  Not Shipped → In Transit → Out for Delivery → Delivered / Returned
```

**Order Creation**: Multi-step wizard (account → items → addresses → review). The `Orders::save()` method auto-closes linked conversations and creates opportunities:

```php
class Orders extends CI_Controller
{
    public function save()
    {
        $request = json_decode(file_get_contents('php://input'), true);
        $company_id = $request['orderFor']['company_id'] ?: ($request['order_company_id'] ?: 1);
        $order_company = $this->_company->getDetail($company_id);
        $status = $this->_orders->save($request, $order_company);
        // Handle conversation or create opportunity for CRM tracking
    }
}
```

**Tax Calculation**: CGST + SGST for intra-state, IGST for inter-state transactions. State Cess where applicable. GST numbers validated per address.

**Invoice Generation**: Tax invoice, proforma invoice, e-invoice (GST compliance), and e-way bill generation using wkhtmltopdf.

**Admin Approvals**: Discounts, credit terms, ship-without-pay, and special pricing require admin approval via `tbl_admin_approvals`.

See [order-management.md](order-management.md) for full details.

---

## Reporting & Analytics

Comprehensive reporting across CRM operations, sales pipeline health, and agent performance. The `ConversationReports` controller loads seven dedicated report models and applies role-based data filtering:

```php
class ConversationReports extends CI_Controller
{
    public function __construct()
    {
        parent::__construct();
        $this->load->model('reports/AgentFRTReportModel', '_frtReport');
        $this->load->model('reports/ConversationFunnelModel', '_funnelReport');
        $this->load->model('reports/ConversationAgingModel', '_agingReport');
        $this->load->model('reports/UnqualifiedAnalysisModel', '_unqualifiedReport');
        $this->load->model('reports/OutcomeReportModel', '_outcomeReport');
        $this->load->model('reports/RevenueContributionModel', '_revenueContribution');
        $this->load->model('reports/AgentActivityReportModel', '_agentActivityReport');
    }

    // Sales agents (role_id=4) only see their own data
    private function applyUserFiltering(&$filters)
    {
        $authData = $CI->AuthData ?? [];
        if (isset($authData['role_id']) && $authData['role_id'] == 4) {
            if (!isset($filters['user_id']) && !isset($filters['agent_id'])) {
                $filters['user_id'] = $authData['user_id'] ?? null;
            }
        }
        return $filters;
    }
}
```

| Report | Endpoint | Model | Description |
|--------|----------|-------|-------------|
| FRT | `/conversationreports/frt_agents` | `AgentFRTReportModel` | First response time per agent |
| Funnel | `/conversationreports/funnel_report` | `ConversationFunnelModel` | Lead progression through stages |
| Aging | `/conversationreports/aging_report` | `ConversationAgingModel` | How long conversations stay open |
| Unqualified | `/conversationreports/unqualified_report` | `UnqualifiedAnalysisModel` | Disqualification patterns |
| Outcome | `/conversationreports/outcome_report` | `OutcomeReportModel` | Win/loss analysis |
| Revenue | `/conversationreports/revenue_contribution` | `RevenueContributionModel` | Revenue by agent/source/region |
| Agent Activity | `/conversationreports/agent_activity` | `AgentActivityReportModel` | Per-agent performance metrics |

**Dashboards**: Main (`/dashboard`), Admin (`/admindashboard`, role_id: 9), Agent (`/agentdashboard`, role_id: 4).

**Export**: Excel/CSV via `ReportExports` controller using `XlsxWriter`.

See [reporting.md](reporting.md) for full details.

---

## Holiday Calendar & Leave Management

Manages company holidays and employee leave records. The round-robin assignment system checks these tables to skip unavailable agents.

**Tables**: `tbl_company_holidays` (holiday calendar), `tbl_user_leaves` (full_day/first_half/second_half with pending/approved/rejected status), `tbl_company_work_hours` (per day-of-week shift times).

**Frontend**: Calendar view at `/holiday-calendar` with add/edit holiday entries and employee leave management.

**Backend**: `HolidayCalendar` controller with CRUD operations.

---

## Product Catalog

Manages the spice/commodity product catalog with grades, pricing, and inventory.

**Tables**: `tbl_produces` (product definitions), grade tables (quality grades), pricing slabs (tiered pricing).

**Frontend Modules**: Produce (`/produce`) for product CRUD, Advanced Slabs (`/slabs`) for tiered pricing, Commodity Rate (`/rates`) for live rate tracking, Grade Rates (`/graderates`) for grade-specific pricing.

**Backend Controllers**: `Produce` (catalog CRUD), `Slabs` (pricing tiers), `GradeSettings` (grade configuration).

---

## Cross-References

| Document | Path |
|----------|------|
| Contacts & Accounts | `04-core-modules/contacts-accounts.md` |
| Conversations | `04-core-modules/conversations.md` |
| WhatsApp Integration | `04-core-modules/whatsapp-integration.md` |
| Assignment Management | `04-core-modules/assignment-management.md` |
| Messaging System | `04-core-modules/messaging-system.md` |
| Order Management | `04-core-modules/order-management.md` |
| Reporting & Analytics | `04-core-modules/reporting.md` |
| Database Schema | `03-database-design/schema-overview.md` |
| API Documentation | `05-api-documentation/` |
| Data Flows | `06-data-flow/` |
