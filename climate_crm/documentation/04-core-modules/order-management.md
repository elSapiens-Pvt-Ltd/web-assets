# Order Management Module

> Module: `climate/modules/orders`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [Order Status State Machine](#order-status-state-machine)
3. [Order Types](#order-types)
4. [Order Creation Flow](#order-creation-flow)
5. [Tax Calculation](#tax-calculation)
6. [Invoice Generation](#invoice-generation)
7. [Payment Tracking](#payment-tracking)
8. [Fulfillment](#fulfillment)
9. [Admin Approvals](#admin-approvals)
10. [CRM Integration](#crm-integration)
11. [Frontend Components](#frontend-components)
12. [Backend Controller](#backend-controller)
13. [Cross-References](#cross-references)

---

## Overview

The Order module handles the complete lifecycle of customer orders — from creation through fulfillment and delivery. It is the most complex frontend module with 40+ sub-components. Four independent status dimensions track order progress: order status, payment status, fulfillment status, and shipping status.

---

## Order Status State Machine

```
                    ┌──────────┐
                    │  draft   │ ← Initial creation
                    └────┬─────┘
                         │ confirm
                    ┌────▼──────┐
                    │ confirmed │
                    └────┬──────┘
                         │ finalize
                    ┌────▼──────┐
                    │   final   │
                    └────┬──────┘
                         │
              ┌──────────┼──────────────┐
              │          │              │
              ▼          ▼              ▼
    ┌──────────────┐  ┌──────────┐  ┌──────────────────┐
    │for_despatch  │  │despatched│  │cancellation_     │
    └──────┬───────┘  └────┬─────┘  │pending           │
           │               │        └──────┬───────────┘
           │               ▼               │ approve cancel
           │         ┌──────────┐          ▼
           └────────►│delivered │    ┌───────────┐
                     └──────────┘    │ cancelled │
                                     └───────────┘


Payment:    no_payment ──► partially_paid ──► fully_paid

Shipping:   not_shipped ──► in_transit ──► out_for_delivery
                                │                │
                                │           ┌────┴────┐
                                │           ▼         ▼
                                │      delivered   returned
                                └──────────────────────┘
```

---

## Order Types

| Type | Description | Currency | Tax |
|------|-------------|----------|-----|
| **Domestic** | Within India | INR | CGST+SGST or IGST |
| **International** | Export orders | Multi-currency | Export rules |

### Order Via

| Value | Description |
|-------|-------------|
| `Online` | Placed through digital channels |
| `Offline` | Placed via phone/in-person |

---

## Order Creation Flow

### Multi-Step Wizard (Frontend)

```
Step 1: Account Selection
├── Search/select existing account
├── Or create new account inline
└── Verify account details

Step 2: Order Items
├── Add products from catalog
├── Set quantities and pricing
├── Apply discounts (may require approval)
├── Calculate taxes:
│   ├── CGST + SGST (same state)
│   ├── IGST (different state)
│   └── State Cess
└── Calculate totals

Step 3: Addresses
├── Select billing address (from account)
├── Select shipping address (from account)
├── Address-specific GST validation
└── Determine inter-state vs intra-state

Step 4: Review & Confirm
├── Review all order details
├── Apply shipping charges
├── Set courier preference
├── Select warehouse (godown)
└── Confirm order
```

### Backend Processing (`Orders::save`)

The controller loads multiple models and handles CRM integration after order save:

```php
class Orders extends CI_Controller
{
    public function __construct()
    {
        parent::__construct();
        $this->load->model('OrdersModel', "_orders");
        $this->load->model('CompanyModel', "_company");
        $this->load->model('WhatsappModel', "_whatsapp");
        $this->load->model('OpenConversationsModel', "_openConversations");
        $this->load->model('ConversationMessagesModel', "_messages");
    }

    /**
     * @capability user
     */
    public function save()
    {
        $CI = &get_instance();
        $userDts = $CI->AuthData;

        $request = json_decode(file_get_contents('php://input'), true);
        $company_id = $request['orderFor']['company_id']
            ?: ($request['order_company_id'] ?: 1);
        $order_company = $this->_company->getDetail($company_id);
        $status = $this->_orders->save($request, $order_company);

        // Handle conversation or create opportunity for CRM tracking
        if ($status['success']) {
            // Auto-close linked conversation, create opportunity
        }
    }
}
```

```
Order save request
    │
    ├── Validate order data
    ├── Calculate taxes and totals
    ├── Create/update tbl_orders
    ├── Create/update tbl_order_items
    ├── Snapshot addresses into tbl_order_data (JSON)
    │
    ├── CRM Integration:
    │   ├── Auto-close linked conversation
    │   │   └── Set tbl_open_conversations.status = 'closed'
    │   │       conversation_stage = 'qualified'
    │   │
    │   └── Create/update opportunity
    │       └── tbl_opportunities linked to order
    │
    └── Return order details
```

---

## Tax Calculation

### Indian GST System

```
Determine tax type:
├── Same state (billing address state = company state)
│   ├── CGST = rate / 2
│   └── SGST = rate / 2
│
└── Different state
    └── IGST = full rate
```

### Tax Fields in tbl_orders

| Field | Description |
|-------|-------------|
| `total_cgst` | Central GST total |
| `total_sgst` | State GST total |
| `total_igst` | Integrated GST total |
| `total_state_cess` | Additional state cess |

### GST Validation

- Account GST number validated during order
- Address-specific GST used for tax determination
- Inter-state vs intra-state based on state_id comparison

---

## Invoice Generation

### Tax Invoice

**Endpoint**: `POST /orders/generateInvoice`

- Generated after order is confirmed
- `invoice_number` assigned
- Uses PDF generation (knplabs/knp-snappy + wkhtmltopdf)

### Proforma Invoice

- Pre-order pricing document
- `proforma_number` assigned
- Generated during Draft stage

### E-Invoice

Electronic invoice for GST compliance:

| Field | Description |
|-------|-------------|
| `e_invoice` | E-invoice reference number |
| `e_invoice_pdf` | PDF document path |
| `e_invoice_qr` | QR code data |
| `e_invoice_path` | Storage path |

### E-Way Bill

Transport documentation for goods movement:

| Field | Description |
|-------|-------------|
| `e_way_bill` | E-way bill number |
| `e_way_bill_pdf` | PDF document path |
| `e_way_bill_qr` | QR code data |

---

## Payment Tracking

### Payment Status Flow

```
no_payment → partially_paid → fully_paid
```

| Status | Condition |
|--------|-----------|
| `no_payment` | `amount_paid = 0` |
| `partially_paid` | `0 < amount_paid < grand_total` |
| `fully_paid` | `amount_paid >= grand_total` |

### Payment Fields

| Field | Description |
|-------|-------------|
| `amount_paid` | Total amount received |
| `pending_amount` | Outstanding amount |
| `payment_requested_at` | Payment request timestamp |
| `due_date` | Payment due date |

### Ship Without Pay

Special approval flow for shipping before full payment:

| Field | Description |
|-------|-------------|
| `ship_without_pay_requested_at` | Request timestamp |
| `ship_without_pay_approved_at` | Approval timestamp |
| `ship_without_pay_rejected_at` | Rejection timestamp |

---

## Fulfillment

### Warehouse Assignment

| Field | Description |
|-------|-------------|
| `godown_id` | Assigned warehouse |
| `godown_change_note` | Reason for warehouse change |

### Courier Assignment

| Field | Description |
|-------|-------------|
| `courier_id` | Assigned courier partner |
| `preferred_courier_id` | Customer's preferred courier |

### Order Data (tbl_order_data)

Stores order metadata as JSON:

| Field | Type | Content |
|-------|------|---------|
| `transport_details` | JSON | Transport/logistics information |
| `billing_address` | JSON | Snapshot of billing address at order time |
| `shipping_address` | JSON | Snapshot of shipping address at order time |

**Address Snapshot**: Addresses are stored as JSON snapshots to preserve the exact address used at order time, even if the account address changes later.

---

## Admin Approvals

### Approval Workflow

Certain order actions require admin approval:

```
Agent performs action requiring approval
    │
    ├── Discount exceeds threshold
    ├── Credit terms requested
    ├── Ship without full payment
    └── Special pricing
        │
        ▼
tbl_admin_approvals (status = 'pending')
        │
        ▼
Admin reviews in /adminapprovals
        │
    ┌───┼───┐
    ▼       ▼
 Approve  Reject
    │       │
    ▼       ▼
 Execute  Notify
 action   agent
```

The `Orders::getDetail()` method includes approval data:

```php
public function getDetail()
{
    $request = json_decode(file_get_contents('php://input'), true);
    $id = $request['id'];
    $order = $this->_orders->getDetail($request);
    $order['items'] = $this->_orders->getOrderItems($id);
    $order['payments'] = $this->_orders->getOrderPayments($id);
    $order['approvals'] = $this->_orders->getApprovalPayments($id);
    $order['total_pending'] = 0;
    if (!empty($order['approvals'])) {
        foreach ($order['approvals'] as $key => $val) {
            $order['total_pending'] += $val['payment_status'] == 'Pending'
                ? $val['payment_amount'] : 0;
        }
    }
    echo Risposta::json_encode($order);
}
```

---

## CRM Integration

### Auto-Close Conversation

When an order is created from a conversation:
1. The linked conversation is closed (`status = 'closed'`)
2. `conversation_stage` set to `'qualified'`
3. `closed_at` timestamp recorded

### Auto-Create Opportunity

Order creation triggers opportunity tracking:
1. Find or create `tbl_opportunities` record
2. Link to account and contact
3. Set `opportunity_status` based on order status
4. Track actual vs committed pricing

---

## Frontend Components

### Order Module Structure (`views/orders/`)

```
orders/
├── orders.component.ts          # Order list (main view)
├── order-create/                # Multi-step creation wizard
│   ├── step-account/            # Account selection
│   ├── step-items/              # Item management
│   ├── step-addresses/          # Address selection
│   └── step-review/             # Final review
├── order-detail/                # Order detail view
├── order-items/                 # Line item management
├── order-timeline/              # Status change history
├── packing/                     # Packing management
├── shipping/                    # Shipping details
├── admin-approvals/             # Approval interface
├── order.service.ts             # API service
└── ... (40+ components total)
```

### Order Service (`order.service.ts`)

- Filter state persistence: `localStorage['orderListFilters']`
- Deep-clones filters to prevent mutation
- Tracks last viewed order ID for navigation
- BehaviorSubjects: `genericOrderFormSub`, `isPreviewSub`, `orderItemsSub`, `stepperSub`, `orderDetailsSub`, `deliveryType`

---

## Backend Controller

### Orders Controller

| Method | Capability | Description |
|--------|------------|-------------|
| `getList()` | `public` | List with filters (type, status, date) |
| `getCustomerNonDespatchedOrders()` | `public` | Pending orders for customer |
| `getDetail()` | `public` | Full details with items, payments, approvals |
| `save()` | `user` | Create/update (auto-close convo, create opportunity) |
| `status()` | `orders` | Update order status |
| `generateInvoice()` | `orders` | Generate tax invoice PDF |
| `adminApprove()` | `adminapprovals` | Process admin approval |

### Related Models

| Model | Purpose |
|-------|---------|
| `OrdersModel` | Order CRUD and queries |
| `OrderStatusLogsModel` | Status change logging |
| `OrderHistoryModel` | Order history tracking |
| `PaymentsModel` | Payment operations |
| `InvoiceModel` | Invoice generation |

---

## Cross-References

| Document | Path |
|----------|------|
| Order Tables (Schema) | `03-database-design/order-tables.md` |
| Contacts & Accounts | `04-core-modules/contacts-accounts.md` |
| Conversations | `04-core-modules/conversations.md` |
| Orders API | `05-api-documentation/orders-api.md` |
| Order Flow | `06-data-flow/order-flow.md` |
