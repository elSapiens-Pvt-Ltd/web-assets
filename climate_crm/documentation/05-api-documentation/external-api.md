# External & Integration API

> Module: `climate/api/external`
> Last updated: 2026-03-11

---

## Table of Contents

1. [External API Endpoints](#external-api-endpoints)
2. [Firebase Endpoints](#firebase-endpoints)
3. [User Management Endpoints](#user-management-endpoints)
4. [Role & Permission Endpoints](#role--permission-endpoints)
5. [Settings Endpoints](#settings-endpoints)
6. [Notification Endpoints](#notification-endpoints)
7. [Cross-References](#cross-references)

---

## External API Endpoints

These endpoints are designed for third-party consumers. They use **X-API-KEY** header authentication instead of JWT.

### Authentication

```
Header: X-API-KEY: <api_key>
Verified against: tbl_justdial_credentials
```

The API key must be active (`active = 1`) in the credentials table.

---

### POST /externalapi/saveUser

Creates or updates a user account via external system.

**Request**:
```json
{
  "name": "External User",
  "email": "external@partner.com",
  "phone": "919876543210",
  "password": "generatedPassword"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": { "user_id": 50 },
  "message": "User created successfully"
}
```

---

### POST /externalapi/opportunityAndProfile

Creates an account and opportunity from an external system in a single call.

**Request**:
```json
{
  "account_name": "External Customer",
  "contact_name": "John Doe",
  "phone": "919876543210",
  "email": "john@external.com",
  "product_interest": "Turmeric Powder",
  "quantity": 500,
  "source": "Partner API"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "account_id": 200,
    "contact_id": 400,
    "opportunity_id": 75
  }
}
```

---

### POST /externalapi/getStatesList

Returns geographic state/province data.

**Response** (200):
```json
{
  "success": true,
  "data": [
    { "state_id": 1, "state_name": "Andhra Pradesh" },
    { "state_id": 2, "state_name": "Arunachal Pradesh" },
    { "state_id": 12, "state_name": "Karnataka" }
  ]
}
```

---

## Firebase Endpoints

### POST /firebase/saveFcmToken

**Capability**: `@capability user`

Saves an FCM device token for push notifications.

**Request**:
```json
{
  "token": "fcm_device_token_xxx",
  "user_id": 5,
  "platform": "web"
}
```

---

### POST /firebase/unsubscribeFromTopic

**Capability**: `@capability user`

Unsubscribes a device from an FCM topic.

**Request**:
```json
{
  "token": "fcm_device_token_xxx",
  "topic": "new_orders"
}
```

---

## User Management Endpoints

### POST /users/index

**Capability**: `@capability users.view`

Lists system users with pagination.

**Request**:
```json
{
  "page": 1,
  "per_page": 25,
  "search": "",
  "status": "Active"
}
```

---

### POST /users/save

**Capability**: `@capability users.edit`

Create or update a system user.

**Request**:
```json
{
  "user_id": null,
  "user_name": "New Agent",
  "email": "agent@climate.com",
  "password": "securePassword",
  "role_id": 4,
  "company_id": 1,
  "status": "Active"
}
```

---

### POST /users/delete

**Capability**: `@capability users.delete`

Deactivate a user.

---

### POST /users/getRoles

**Capability**: `@capability users.view`

Returns available roles for user assignment.

---

## Role & Permission Endpoints

### POST /roles/index

Lists roles with capabilities.

### POST /roles/save

Create or update a role with capability assignments.

### POST /menu/

Returns menu structure with capability definitions for role configuration.

---

## Settings Endpoints

### POST /settings/index

**Capability**: `@capability settings`

Get system settings.

### POST /settings/save

**Capability**: `@capability settings`

Update system settings.

---

## Notification Endpoints

### POST /notifications/index

**Capability**: `@capability user`

Get notifications for the current user.

**Request**:
```json
{
  "page": 1,
  "per_page": 20,
  "status": "pending"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": 100,
      "event": "new_order",
      "message": "New order ORD-5001 from Sunrise Spices",
      "target_url": "/orders/5001",
      "status": "pending",
      "created_at": "2026-03-11T10:30:00"
    }
  ],
  "total": 15
}
```

---

## Cross-References

| Document | Path |
|----------|------|
| Authentication | `05-api-documentation/authentication.md` |
| Configuration Tables | `03-database-design/configuration-tables.md` |
| Security | `01-system-architecture/security.md` |
| Backend Architecture | `01-system-architecture/backend-architecture.md` |
