# Orders API

> Module: `climate/api/orders`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Endpoints](#endpoints)
2. [Status Enums Reference](#status-enums-reference)
3. [Cross-References](#cross-references)

---

## Endpoints

### POST /orders/getList

**Capability**: `@capability public`

Lists orders with pagination and filters.

**Request**:
```json
{
  "start": 0,
  "limit": 25,
  "type": "online",
  "filters": {
    "order_status": "confirmed",
    "payment_status": "partially_paid",
    "date_from": "2026-03-01",
    "date_to": "2026-03-11",
    "account_id": 150
  }
}
```

**Response** (200):
```json
{
  "total": 120,
  "orders": [
    {
      "order_id": 5001,
      "account_name": "Sunrise Spices Pvt Ltd",
      "invoice_number": "INV-2026-0342",
      "order_status": "confirmed",
      "payment_status": "partially_paid",
      "shipping_status": "not_shipped",
      "grand_total": 45000.00,
      "amount_paid": 20000.00,
      "pending_amount": 25000.00,
      "order_via": "Online",
      "order_mode": "domestic",
      "order_time": "2026-03-10T14:30:00",
      "created_by_name": "Priya Sharma"
    }
  ]
}
```

---

### POST /orders/getCustomerNonDespatchedOrders

**Capability**: `@capability public`

Gets pending (non-despatched) orders for a customer.

**Request**:
```json
{ "account_id": 150 }
```

---

### POST /orders/getDetail

**Capability**: `@capability public`

Gets full order details including items, payments, and approval status.

**Request**:
```json
{ "id": 5001 }
```

**Response** (200):
```json
{
  "order_id": 5001,
  "account_id": 150,
  "account_name": "Sunrise Spices Pvt Ltd",
  "invoice_number": "INV-2026-0342",
  "order_status": "confirmed",
  "payment_status": "partially_paid",
  "fulfillment_status": "pending",
  "shipping_status": "not_shipped",
  "order_total": 40000.00,
  "shipping_charges": 500.00,
  "total_cgst": 1800.00,
  "total_sgst": 1800.00,
  "total_igst": 0,
  "grand_total": 44100.00,
  "amount_paid": 20000.00,
  "pending_amount": 24100.00,
  "order_via": "Online",
  "order_mode": "domestic",
  "courier_id": 3,
  "godown_id": 1,
  "due_date": "2026-03-25",
  "order_time": "2026-03-10T14:30:00",
  "items": [
    {
      "item_id": 10001,
      "product_name": "Turmeric Powder",
      "grade": "Premium",
      "quantity": 100,
      "unit": "kg",
      "unit_price": 250.00,
      "total": 25000.00,
      "cgst_rate": 9,
      "sgst_rate": 9
    }
  ],
  "payments": [
    {
      "payment_id": 2001,
      "amount": 20000.00,
      "payment_type": "NEFT",
      "status": "confirmed",
      "created_at": "2026-03-10T16:00:00"
    }
  ],
  "approvals": [],
  "total_pending": 0
}
```

---

### POST /orders/save

**Capability**: `@capability user`

Creates or updates an order. This is the most complex endpoint with multiple side effects.

**Request**:
```json
{
  "order_id": null,
  "orderFor": { "company_id": 1 },
  "account_id": 150,
  "order_via": "Online",
  "order_mode": "domestic",
  "courier_id": 3,
  "godown_id": 1,
  "billing_address_id": 75,
  "shipping_address_id": 75,
  "items": [
    {
      "product_id": 10,
      "grade_id": 2,
      "quantity": 100,
      "unit_price": 250.00
    }
  ],
  "shipping_charges": 500.00,
  "due_date": "2026-03-25",
  "conversation_id": 123
}
```

**Side Effects**:
1. Calculate taxes (CGST/SGST or IGST based on state)
2. Snapshot billing and shipping addresses as JSON in `tbl_order_data`
3. Auto-close linked conversation (`conversation_id`)
4. Create/update opportunity in `tbl_opportunities`
5. Update account summary (total_orders, total_revenue)

**Response** (200):
```json
{
  "success": true,
  "data": {
    "order_id": 5001,
    "invoice_number": null,
    "order_status": "draft",
    "grand_total": 44100.00
  },
  "message": "Order created successfully"
}
```

---

### POST /orders/status

**Capability**: `@capability orders`

Updates order status.

**Request**:
```json
{
  "order_id": 5001,
  "order_status": "confirmed"
}
```

**Valid Transitions**:
```
draft → confirmed
confirmed → final
final → despatched
any → cancellation_pending
cancellation_pending → cancelled
```

---

### POST /orders/generateInvoice

**Capability**: `@capability orders`

Generates a tax invoice PDF for a confirmed order.

**Request**:
```json
{ "order_id": 5001 }
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "invoice_number": "INV-2026-0342",
    "invoice_url": "https://cdn.../invoices/INV-2026-0342.pdf"
  }
}
```

---

### POST /orders/adminApprove

**Capability**: `@capability adminapprovals`

Processes an admin approval request.

**Request**:
```json
{
  "approval_id": 50,
  "action": "approve",
  "notes": "Approved special discount for bulk order"
}
```

**Actions**: `approve`, `reject`

---

## Status Enums Reference

### Order Status
| Value | Description |
|-------|-------------|
| `draft` | Initial creation, not yet confirmed |
| `confirmed` | Order confirmed by agent |
| `final` | Finalized for processing |
| `cancellation_pending` | Cancellation requested, awaiting approval |
| `cancelled` | Order cancelled |

### Payment Status
| Value | Description |
|-------|-------------|
| `no_payment` | No payment received |
| `partially_paid` | Partial payment received |
| `fully_paid` | Full payment received |

### Fulfillment Status
| Value | Description |
|-------|-------------|
| `pending` | Not yet processed |
| `for_despatch` | Ready for shipping |
| `despatched` | Shipped |

### Shipping Status
| Value | Description |
|-------|-------------|
| `not_shipped` | Awaiting shipment |
| `in_transit` | Being delivered |
| `out_for_delivery` | On delivery vehicle |
| `delivered` | Successfully delivered |
| `returned` | Returned to sender |

---

## Cross-References

| Document | Path |
|----------|------|
| Order Management Module | `04-core-modules/order-management.md` |
| Order Tables (Schema) | `03-database-design/order-tables.md` |
| Authentication | `05-api-documentation/authentication.md` |
| Order Flow | `06-data-flow/order-flow.md` |
