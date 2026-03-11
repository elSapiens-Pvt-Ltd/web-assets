# Order & Payment Tables

> Module: `climate/database/orders`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [tbl_orders](#tbl_orders)
3. [tbl_order_items](#tbl_order_items)
4. [tbl_order_data](#tbl_order_data)
5. [tbl_payments](#tbl_payments)
6. [tbl_order_status_logs](#tbl_order_status_logs)
7. [tbl_opportunities](#tbl_opportunities)
8. [tbl_admin_approvals](#tbl_admin_approvals)
9. [Cross-References](#cross-references)

---

## Overview

The order tables manage the complete order lifecycle from draft creation through fulfillment and delivery. The `tbl_orders` table uses four independent status fields — `order_status`, `payment_status`, `fulfillment_status`, and `shipping_status` — split from a single overloaded `order_status` ENUM by migration `20251224000321_split_order_status_fields.php`.

---

## tbl_orders

The primary order table. Each order belongs to an account and optionally links to a conversation (when created from a lead).

### Status Fields

The order status was originally a single ENUM with values like `advancepending`, `paymentrequested`, `despatched`. This was split into four independent status dimensions:

**Created by**: `20251224000321_split_order_status_fields.php`

| Status Field | Values | Default | Purpose |
|-------------|--------|---------|---------|
| `order_status` | `draft`, `confirmed`, `final`, `cancellation_pending`, `cancelled` | `draft` | Order lifecycle stage |
| `payment_status` | `no_payment`, `partially_paid`, `fully_paid` | `no_payment` | Payment tracking |
| `fulfillment_status` | `pending`, `for_despatch`, `despatched` | `pending` | Warehouse/packing stage |
| `shipping_status` | `not_shipped`, `in_transit`, `out_for_delivery`, `delivered`, `returned` | `not_shipped` | Shipping lifecycle |

### Order Status Flow

```
draft → confirmed → final → cancellation_pending → cancelled
                        │
                        └── Normal flow continues through
                            fulfillment and shipping statuses
```

### Key Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `order_id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `account_id` | BIGINT UNSIGNED | Yes | NULL | FK to `temp_tbl_accounts` |
| `conversation_id` | BIGINT UNSIGNED | Yes | NULL | Source conversation |
| `agent_id` | INT | Yes | NULL | Agent who created the order |
| `order_status` | ENUM | No | `'draft'` | Order lifecycle stage |
| `payment_status` | ENUM | No | `'no_payment'` | Payment tracking |
| `fulfillment_status` | ENUM | No | `'pending'` | Fulfillment stage |
| `shipping_status` | ENUM | No | `'not_shipped'` | Shipping stage |
| `order_type` | ENUM('domestic','international') | No | `'domestic'` | Order type |
| `total_amount` | DECIMAL(12,2) | Yes | NULL | Order total including tax |
| `subtotal` | DECIMAL(12,2) | Yes | NULL | Pre-tax subtotal |
| `tax_amount` | DECIMAL(12,2) | Yes | NULL | Total tax |
| `discount_amount` | DECIMAL(12,2) | Yes | NULL | Applied discount |
| `amount_paid` | DECIMAL(12,2) | No | `0.00` | Total payment received |
| `pending_amount` | DECIMAL(12,2) | Yes | NULL | Remaining balance |
| `currency` | VARCHAR(10) | No | `'INR'` | Order currency |
| `exchange_rate` | DECIMAL(10,4) | Yes | NULL | For international orders |
| `payment_requested_at` | DATETIME | Yes | NULL | When payment was requested |
| `invoice_number` | VARCHAR(50) | Yes | NULL | Generated invoice number |
| `e_invoice_irn` | VARCHAR(255) | Yes | NULL | E-Invoice IRN from GST portal |
| `e_way_bill_number` | VARCHAR(50) | Yes | NULL | E-Way Bill number |
| `courier_id` | INT | Yes | NULL | FK to `tbl_couriers` |
| `tracking_number` | VARCHAR(100) | Yes | NULL | Shipment tracking number |
| `notes` | TEXT | Yes | NULL | Internal order notes |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Order creation time |
| `updated_on` | DATETIME | No | CURRENT_TIMESTAMP ON UPDATE | Last update time |

**Indexes**: `account_id`, `conversation_id`, `agent_id`, `order_status`, `payment_status`, `fulfillment_status`, `shipping_status`

---

## tbl_order_items

Line items for each order. Each item includes quantity, pricing, and individually calculated tax amounts.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `item_id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `order_id` | INT UNSIGNED | No | — | FK to `tbl_orders` |
| `product_id` | INT UNSIGNED | Yes | NULL | FK to product table |
| `product_name` | VARCHAR(255) | Yes | NULL | Product name snapshot |
| `quantity` | DECIMAL(10,2) | No | `0` | Ordered quantity |
| `unit` | VARCHAR(20) | Yes | NULL | Unit of measure (kg, piece, etc.) |
| `rate` | DECIMAL(12,2) | No | `0` | Unit price |
| `amount` | DECIMAL(12,2) | No | `0` | Line total (quantity × rate) |
| `cgst_rate` | DECIMAL(5,2) | Yes | NULL | Central GST rate % |
| `cgst_amount` | DECIMAL(12,2) | Yes | NULL | Central GST amount |
| `sgst_rate` | DECIMAL(5,2) | Yes | NULL | State GST rate % |
| `sgst_amount` | DECIMAL(12,2) | Yes | NULL | State GST amount |
| `igst_rate` | DECIMAL(5,2) | Yes | NULL | Integrated GST rate % |
| `igst_amount` | DECIMAL(12,2) | Yes | NULL | Integrated GST amount |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Record creation time |

### Tax Calculation Logic

Tax is calculated based on the billing address state:

| Scenario | Tax Applied | Rule |
|----------|-------------|------|
| Same state (intrastate) | CGST + SGST | Billing state matches company state |
| Different state (interstate) | IGST | Billing state differs from company state |
| Export | Zero-rated or IGST | Based on export type (with/without payment) |

---

## tbl_order_data

Stores JSON snapshots of billing and shipping addresses at the time of order creation. This preserves the address as it was when the order was placed, even if the account's address is later updated.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `order_id` | INT UNSIGNED | No | — | FK to `tbl_orders` |
| `data_type` | VARCHAR(50) | Yes | NULL | `'billing_address'`, `'shipping_address'`, `'transport_details'` |
| `data` | JSON / TEXT | Yes | NULL | JSON data blob |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Record creation time |

### Example JSON Structures

**Billing Address**:
```json
{
  "address_id": 42,
  "gst_number": "29ABCDE1234F1Z5",
  "line_1": "123 MG Road",
  "city": "Bangalore",
  "state": "Karnataka",
  "state_id": 12,
  "pincode": "560001"
}
```

---

## tbl_payments

Records individual payment transactions against orders. Multiple payments can be made against a single order (partial payment support).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `order_id` | INT UNSIGNED | No | — | FK to `tbl_orders` |
| `amount` | DECIMAL(12,2) | No | `0` | Payment amount |
| `payment_mode` | VARCHAR(50) | Yes | NULL | `bank_transfer`, `upi`, `cash`, `cheque` |
| `reference_number` | VARCHAR(100) | Yes | NULL | Transaction reference |
| `payment_date` | DATE | Yes | NULL | Date of payment |
| `notes` | TEXT | Yes | NULL | Payment notes |
| `recorded_by` | INT | Yes | NULL | FK to `tbl_users` |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Record creation time |

**Business Rules**:
- When a payment is recorded, the system updates `tbl_orders.amount_paid` and recalculates `pending_amount`
- `payment_status` on the order auto-updates: `no_payment` → `partially_paid` → `fully_paid`

---

## tbl_order_status_logs

Audit trail of every status transition for an order. Each row records who changed the status, when, and to what value.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `order_id` | INT UNSIGNED | No | — | FK to `tbl_orders` |
| `status_field` | VARCHAR(50) | Yes | NULL | Which status changed (`order_status`, `payment_status`, etc.) |
| `old_status` | VARCHAR(50) | Yes | NULL | Previous value |
| `new_status` | VARCHAR(50) | Yes | NULL | New value |
| `changed_by` | INT | Yes | NULL | FK to `tbl_users` |
| `notes` | TEXT | Yes | NULL | Change notes |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | When the change occurred |

---

## tbl_opportunities

Sales opportunities linked to conversations. When an order is created from a conversation, an opportunity record is created (or linked) to track the revenue attribution.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `opportunity_id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `account_id` | BIGINT UNSIGNED | Yes | NULL | FK to `temp_tbl_accounts` |
| `contact_id` | BIGINT UNSIGNED | Yes | NULL | FK to `temp_tbl_contacts` |
| `conversation_id` | BIGINT UNSIGNED | Yes | NULL | Source conversation |
| `order_id` | INT UNSIGNED | Yes | NULL | Linked order |
| `agent_id` | INT | Yes | NULL | Responsible agent |
| `opportunity_value` | DECIMAL(12,2) | Yes | NULL | Expected revenue |
| `stage` | VARCHAR(50) | Yes | NULL | Opportunity stage |
| `source` | VARCHAR(50) | Yes | NULL | Lead source |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Record creation time |

---

## tbl_admin_approvals

Approval requests for actions that require admin authorization — primarily discount approvals (when discount exceeds a configurable threshold) and ship-without-pay requests.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `order_id` | INT UNSIGNED | Yes | NULL | Related order |
| `approval_type` | VARCHAR(50) | Yes | NULL | `'discount'`, `'ship_without_pay'` |
| `requested_by` | INT | Yes | NULL | Agent requesting approval |
| `approved_by` | INT | Yes | NULL | Admin who approved/rejected |
| `status` | ENUM('pending','approved','rejected') | No | `'pending'` | Approval status |
| `request_data` | JSON / TEXT | Yes | NULL | Details of the request |
| `response_notes` | TEXT | Yes | NULL | Admin's response notes |
| `requested_at` | DATETIME | No | CURRENT_TIMESTAMP | When requested |
| `responded_at` | DATETIME | Yes | NULL | When approved/rejected |

---

## Cross-References

| Document | Path |
|----------|------|
| Schema Overview | `03-database-design/schema-overview.md` |
| Core Tables | `03-database-design/core-tables.md` |
| Order Flow | `06-data-flow/order-flow.md` |
| Orders API | `05-api-documentation/orders-api.md` |
| Order Module | `04-core-modules/orders.md` |
