> Module: climate/data-flow/order-flow
> Last updated: 2026-03-11

# Order Flow

## Table of Contents

- [Overview](#overview)
- [Order Creation Flow](#order-creation-flow)
  - [From Conversation (Primary Path)](#from-conversation-primary-path)
  - [Direct Order (No Conversation)](#direct-order-no-conversation)
- [Order Status Transitions](#order-status-transitions)
- [Payment Flow](#payment-flow)
  - [Payment Recording](#payment-recording)
  - [Ship Without Pay (Special Flow)](#ship-without-pay-special-flow)
- [Invoice Generation Flow](#invoice-generation-flow)
- [Fulfillment Flow](#fulfillment-flow)
  - [Warehouse Assignment](#warehouse-assignment)
  - [Shipping Flow](#shipping-flow)
- [Admin Approval Flow](#admin-approval-flow)
- [CRM-Order Integration Summary](#crm-order-integration-summary)
- [Database Tables](#database-tables)
- [Cross-References](#cross-references)

---

## Overview

This document traces the complete order lifecycle from creation through fulfillment and delivery, including payment tracking, invoice generation, and CRM integration.

---

## Order Creation Flow

### From Conversation (Primary Path)

```
Agent in ChatWindowComponent clicks "Create Order"
    │
    ▼
┌──────────────────────────────────────────────────┐
│ Step 1: Account Selection                        │
│                                                  │
│ ├── Search existing accounts                     │
│ ├── Or create new account inline                 │
│ ├── Verify GST number                            │
│ └── Pre-fill from conversation contact           │
└──────────┬───────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│ Step 2: Order Items                              │
│                                                  │
│ ├── Add products from catalog                    │
│ ├── Set quantities and unit price                │
│ ├── Apply discounts:                             │
│ │   ├── Within threshold → auto-approved         │
│ │   └── Exceeds threshold → requires admin       │
│ │       approval (tbl_admin_approvals)            │
│ ├── Calculate taxes:                             │
│ │   ├── Same state billing:                      │
│ │   │   CGST = rate/2, SGST = rate/2             │
│ │   └── Different state billing:                 │
│ │       IGST = full rate                         │
│ └── Running total calculation                    │
└──────────┬───────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│ Step 3: Addresses                                │
│                                                  │
│ ├── Select billing address (from account)        │
│ ├── Select shipping address (from account)       │
│ ├── Address determines tax type:                 │
│ │   billing_state == company_state → CGST+SGST   │
│ │   billing_state != company_state → IGST        │
│ └── Validate GST for address                     │
└──────────┬───────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│ Step 4: Review & Confirm                         │
│                                                  │
│ ├── Review all order details                     │
│ ├── Set shipping charges                         │
│ ├── Select courier preference                    │
│ ├── Select warehouse (godown)                    │
│ ├── Set order type: Domestic / International     │
│ ├── Set order via: Online / Offline              │
│ └── Confirm order                                │
└──────────┬───────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│ POST /orders/save                                │
│                                                  │
│ OrdersModel::save()                              │
│ ├── Validate order data                          │
│ ├── Calculate final taxes and totals             │
│ ├── INSERT tbl_orders (status = 'draft')         │
│ ├── INSERT tbl_order_items (line items)          │
│ ├── Snapshot addresses into tbl_order_data:      │
│ │   ├── billing_address (JSON)                   │
│ │   └── shipping_address (JSON)                  │
│ │                                                │
│ ├── CRM Integration:                             │
│ │   ├── Close linked conversation:               │
│ │   │   tbl_open_conversations.status = 'closed' │
│ │   │   conversation_stage = 'converted'         │
│ │   │   closed_at = NOW()                        │
│ │   │                                            │
│ │   ├── Create/update opportunity:               │
│ │   │   tbl_opportunities linked to order        │
│ │   │   opportunity_status = 'won'               │
│ │   │                                            │
│ │   └── Insert system message in conversation:   │
│ │       "🛒 Order Created - Order #: {id}"       │
│ │                                                │
│ └── Return order details                         │
└──────────────────────────────────────────────────┘
```

### Direct Order (No Conversation)

```
Agent creates order from Orders module
    │
    ├── Same wizard steps (account, items, addresses, review)
    │
    └── POST /orders/save
        ├── Create order (same as above)
        ├── Find open conversation by contact_id:
        │   ├── If found → close as 'converted'
        │   └── If not found → skip
        └── Create opportunity for CRM tracking
```

---

## Order Status Transitions

```
┌──────────┐
│  DRAFT   │ ← Initial creation
└────┬─────┘
     │ confirm
┌────▼──────┐
│ CONFIRMED │
└────┬──────┘
     │ finalize
┌────▼──────┐
│   FINAL   │
└────┬──────┘
     │
     ├───────────────┬──────────────────┐
     ▼               ▼                  ▼
┌──────────┐   ┌──────────┐   ┌────────────────┐
│   FOR    │   │DESPATCHED│   │ CANCELLATION   │
│DESPATCH  │   │          │   │ PENDING        │
└────┬─────┘   └────┬─────┘   └───────┬────────┘
     │               │                │
     │               ▼                ▼
     │         ┌──────────┐    ┌───────────┐
     └────────►│DELIVERED │    │ CANCELLED │
               └──────────┘    └───────────┘
```

### Status Update Flow

```
POST /orders/status
{
  order_id: 123,
  status: 'confirmed',
  notes: 'Payment verified'
}
    │
    ▼
Orders::status()
    │
    ├── Validate status transition is allowed
    ├── UPDATE tbl_orders SET status = new_status
    ├── INSERT tbl_order_status_logs:
    │   ├── order_id
    │   ├── old_status, new_status
    │   ├── changed_by_user_id
    │   ├── notes
    │   └── created_at
    └── Trigger side effects:
        ├── confirmed → enable invoice generation
        ├── despatched → update shipping status
        ├── delivered → mark as complete
        └── cancelled → release inventory
```

---

## Payment Flow

```
┌───────────────┐     ┌──────────────────┐     ┌─────────────┐
│  No Payment   │────►│ Partially Paid   │────►│ Fully Paid  │
│ amount_paid=0 │     │ 0 < paid < total │     │ paid≥total  │
└───────────────┘     └──────────────────┘     └─────────────┘
```

### Payment Recording

```
POST /payments/save
{
  order_id: 123,
  amount: 5000,
  payment_mode: 'bank_transfer',
  reference_number: 'UTR12345',
  payment_date: '2026-03-11'
}
    │
    ▼
PaymentsModel::save()
    │
    ├── INSERT tbl_payments
    ├── UPDATE tbl_orders:
    │   ├── amount_paid += payment_amount
    │   ├── pending_amount = grand_total - amount_paid
    │   └── payment_status recalculated
    └── If fully paid:
        └── Clear payment_requested flag
```

### Ship Without Pay (Special Flow)

```
Agent requests ship without full payment
    │
    ├── INSERT tbl_admin_approvals:
    │   ├── type = 'ship_without_pay'
    │   ├── order_id
    │   ├── requested_by_user_id
    │   └── status = 'pending'
    │
    ├── Admin reviews in /adminapprovals
    │
    ├── Approved:
    │   ├── UPDATE tbl_orders
    │   │   ship_without_pay_approved_at = NOW()
    │   └── Allow dispatch without full payment
    │
    └── Rejected:
        └── UPDATE tbl_orders
            ship_without_pay_rejected_at = NOW()
```

---

## Invoice Generation Flow

```
POST /orders/generateInvoice
{ order_id: 123 }
    │
    ▼
Orders::generateInvoice()
    │
    ├── Validate order status (must be confirmed+)
    ├── Assign invoice_number (sequential)
    │
    ├── Generate PDF:
    │   ├── Load invoice template (HTML)
    │   ├── Populate with order data
    │   ├── knp-snappy + wkhtmltopdf → PDF
    │   └── Upload PDF to S3
    │
    ├── UPDATE tbl_orders:
    │   ├── invoice_number
    │   └── invoice_path (S3 key)
    │
    └── Return invoice URL (pre-signed S3)

Optional: Send via WhatsApp
    │
    POST /orders/sendInvoiceByWhatsapp
    { order_id: 123, handle_id: 456 }
    │
    ├── Get invoice PDF from S3
    ├── Send as WhatsApp document message
    └── Record in tbl_whatsapp_messages
```

### E-Invoice & E-Way Bill

```
For GST compliance:
    │
    ├── E-Invoice:
    │   ├── Generate via GST portal API
    │   ├── Store: e_invoice, e_invoice_pdf, e_invoice_qr
    │   └── QR code for verification
    │
    └── E-Way Bill:
        ├── Generate for goods transport
        ├── Store: e_way_bill, e_way_bill_pdf, e_way_bill_qr
        └── Required for shipments above threshold
```

---

## Fulfillment Flow

### Warehouse Assignment

```
Order confirmed
    │
    ├── Assign godown_id (warehouse)
    │   Based on: product availability, location
    │
    ├── If warehouse changed later:
    │   ├── godown_change_note = reason
    │   └── Log change in order history
    │
    └── Packing initiated at warehouse
```

### Shipping Flow

```
┌──────────────┐     ┌────────────┐     ┌──────────────────┐
│ Not Shipped  │────►│ In Transit │────►│ Out for Delivery │
└──────────────┘     └────────────┘     └────────┬─────────┘
                                                  │
                                        ┌─────────┼─────────┐
                                        ▼                    ▼
                                  ┌──────────┐       ┌───────────┐
                                  │Delivered │       │ Returned  │
                                  └──────────┘       └───────────┘
```

```
Courier assignment
    │
    ├── Set courier_id (from tbl_couriers)
    ├── Set preferred_courier_id (customer preference)
    │
    ├── Generate shipping label
    ├── Record tracking number
    │
    └── Track status updates:
        ├── In Transit → tracking API
        ├── Out for Delivery → courier update
        ├── Delivered → confirmation
        └── Returned → RTO process
```

---

## Admin Approval Flow

```
Action requiring approval
    │
    ├── Discount exceeds threshold
    ├── Credit terms requested
    ├── Ship without full payment
    └── Special pricing
        │
        ▼
INSERT tbl_admin_approvals
    ├── approval_type
    ├── order_id
    ├── requested_by_user_id
    ├── approval_data (JSON details)
    └── status = 'pending'
        │
        ▼
Admin reviews at /adminapprovals
        │
    ┌───┼───┐
    ▼       ▼
 Approve  Reject
    │       │
    ▼       ▼
 Execute  Notify
 action   agent
    │
    └── approved_by_user_id
        approved_at = NOW()
```

---

## CRM-Order Integration Summary

```
Conversation → Order:
├── conversation_stage → 'converted'
├── status → 'closed'
├── Opportunity created/updated
└── System message posted

Order → Reports:
├── Revenue attribution by agent
├── Revenue by lead source
├── Conversion rate tracking
└── Order analytics (status, courier, warehouse)
```

---

## Database Tables

| Table | Role |
|-------|------|
| `tbl_orders` | Order header (status, amounts, addresses) |
| `tbl_order_items` | Line items (product, qty, price, tax) |
| `tbl_order_data` | Metadata JSON (addresses snapshot, transport) |
| `tbl_payments` | Payment records |
| `tbl_opportunities` | CRM opportunity linked to order |
| `tbl_admin_approvals` | Approval workflow |
| `tbl_order_status_logs` | Status change audit trail |
| `tbl_open_conversations` | Conversation closed on order |
| `tbl_whatsapp_messages` | System messages for order events |

---

## Cross-References

**Core Modules**
- [`04-core-modules/order-management.md`](../04-core-modules/order-management.md) — Order creation wizard, tax calculation, and status management
- [`04-core-modules/conversations.md`](../04-core-modules/conversations.md) — Conversation closure and converted stage triggered by order save
- [`04-core-modules/whatsapp-integration.md`](../04-core-modules/whatsapp-integration.md) — Invoice delivery via WhatsApp document messages

**API Documentation**
- [`05-api-documentation/orders-api.md`](../05-api-documentation/orders-api.md) — Order save, status update, payment, and invoice generation endpoints
- [`05-api-documentation/whatsapp-api.md`](../05-api-documentation/whatsapp-api.md) — Send invoice by WhatsApp endpoint

**Database Design**
- [`03-database-design/order-tables.md`](../03-database-design/order-tables.md) — `tbl_orders`, `tbl_order_items`, `tbl_payments`, `tbl_admin_approvals` schema
- [`03-database-design/crm-tables.md`](../03-database-design/crm-tables.md) — `tbl_opportunities`, `tbl_open_conversations` schema

**Related Data Flows**
- [`06-data-flow/conversation-lifecycle.md`](./conversation-lifecycle.md) — Conversation converted stage triggered by order creation
- [`06-data-flow/webhook-flow.md`](./webhook-flow.md) — External lead sources that initiate the conversation-to-order pipeline
