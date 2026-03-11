# Accounts & Contacts API

> Module: `climate/api/accounts`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Account Endpoints](#account-endpoints)
2. [Contact Endpoints](#contact-endpoints)
3. [Contact Handle Endpoints](#contact-handle-endpoints)
4. [Cross-References](#cross-references)

---

## Account Endpoints

### POST /accounts/createAccount

**Capability**: `@capability customers.default`

Creates or updates an account with contacts and addresses in a single transaction.

**Request**:
```json
{
  "account_id": null,
  "account_name": "Sunrise Spices Pvt Ltd",
  "account_type": "Business",
  "gst_number": "29ABCDE1234F1Z5",
  "account_fssai_number": "12345678901234",
  "business_type": "Private Limited Company",
  "business_category": "Wholesale Trading",
  "distribution_type": "wholesaler",
  "region": "South",
  "is_export": 0,
  "contacts": [
    {
      "contact_name": "Rajesh Kumar",
      "designation": "Owner",
      "is_primary_contact": 1,
      "handles": [
        { "handle_type": "phone", "handle_value": "919876543210", "is_primary": 1 },
        { "handle_type": "email", "handle_value": "rajesh@sunrise.com", "is_primary": 1 }
      ]
    }
  ],
  "addresses": [
    {
      "address_type": "billing & shipping",
      "line_1": "123 Spice Market",
      "line_2": "Gandhi Nagar",
      "city": "Bangalore",
      "state": "Karnataka",
      "state_id": 12,
      "country": "India",
      "country_id": 101,
      "pincode": "560001",
      "gst_number": "29ABCDE1234F1Z5"
    }
  ]
}
```

**Success Response** (200):
```json
{
  "success": true,
  "data": {
    "account_id": 150,
    "contacts": [{ "contact_id": 300, "handles": [{ "handle_id": 450 }] }],
    "addresses": [{ "address_id": 75 }]
  },
  "message": "Account created successfully"
}
```

**Error — Duplicate GST** (409):
```json
{
  "success": false,
  "message": "GST number already exists for another account",
  "errors": { "gst_number": "Duplicate GST: 29ABCDE1234F1Z5" }
}
```

**Business Rules**:
- GST number uniqueness validated across all accounts
- Phone numbers normalized (0 prefix → 91)
- At least one contact required
- Transaction: all-or-nothing (rollback on any failure)

---

### POST /customers/index

**Capability**: `@capability customers.default`

Lists customer accounts with pagination and filters.

**Request**:
```json
{
  "page": 1,
  "per_page": 25,
  "search": "sunrise",
  "filters": {
    "status": "active",
    "region": "South",
    "distribution_type": "wholesaler"
  },
  "sort_by": "updated_on",
  "sort_order": "desc"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": [
    {
      "account_id": 150,
      "account_name": "Sunrise Spices Pvt Ltd",
      "account_type": "Business",
      "status": "active",
      "total_orders": 12,
      "total_revenue": 245000.00,
      "region": "South",
      "primary_contact": "Rajesh Kumar",
      "primary_phone": "919876543210"
    }
  ],
  "total": 85,
  "page": 1,
  "per_page": 25
}
```

---

### POST /customers/getDetail

**Capability**: `@capability customers.default`

Gets full account details including contacts, addresses, and summary.

**Request**:
```json
{ "account_id": 150 }
```

---

### POST /customers/save

**Capability**: `@capability customers.default`

Create or update a customer record.

---

### POST /customers/delete

**Capability**: `@capability customers.delete`

Delete (soft-delete) a customer account.

---

### POST /customers/reactivateAccount

**Capability**: `@capability customers.default`

Reactivates a previously closed account.

---

### POST /customers/addresses

**Capability**: `@capability customers.default`

Gets all addresses for an account.

---

### POST /customers/updateCustomerAddress

**Capability**: `@capability customers.default`

Updates an account address and syncs with related orders.

---

## Contact Endpoints

### POST /contact/getList

**Capability**: `@capability contacts.view`

Lists contacts with pagination.

**Request**:
```json
{
  "page": 1,
  "per_page": 25,
  "search": "rajesh",
  "account_id": 150
}
```

---

### POST /contact/getDetail

**Capability**: `@capability contacts.view`

Gets full contact details with handles.

---

### POST /contact/save

**Capability**: `@capability contacts.edit`

Create or update a contact.

**Request**:
```json
{
  "contact_id": null,
  "account_id": 150,
  "contact_name": "Priya Sharma",
  "designation": "Purchase Manager",
  "is_primary_contact": 0,
  "handles": [
    { "handle_type": "phone", "handle_value": "919123456789", "is_primary": 1 }
  ]
}
```

---

### POST /contact/status

**Capability**: `@capability contacts.edit`

Update contact status (active/inactive/deleted).

---

## Contact Handle Endpoints

### POST /contacthandles/create

Create a new contact handle.

**Request**:
```json
{
  "contact_id": 300,
  "handle_type": "whatsapp",
  "handle_value": "919876543210",
  "phone_code": "91",
  "country_code": "IN",
  "is_primary": 1
}
```

---

### POST /contacthandles/update

Update an existing handle.

---

### GET /contacthandles/get/{handleId}

Retrieve handle details by ID.

---

### POST /contacthandles/validateForCall

Validate that a handle can be used for calling (requires country_code).

**Response**:
```json
{
  "success": true,
  "data": { "valid": true, "phone": "+919876543210" }
}
```

---

### POST /contacthandles/validateForMessage

Validate that a handle can receive messages.

---

## Cross-References

| Document | Path |
|----------|------|
| Contacts & Accounts Module | `04-core-modules/contacts-accounts.md` |
| Core Tables (Schema) | `03-database-design/core-tables.md` |
| Authentication | `05-api-documentation/authentication.md` |
