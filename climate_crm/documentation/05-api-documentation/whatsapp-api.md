# WhatsApp API

> Module: `climate/api/whatsapp`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Webhook](#webhook)
2. [Messaging](#messaging)
3. [Conversation Management](#conversation-management)
4. [Customer Details](#customer-details)
5. [Notes & Follow-ups](#notes--follow-ups)
6. [Cross-References](#cross-references)

---

## Webhook

### GET /whatsapp/webhookCloudApi

**Capability**: `@capability public`

Webhook verification endpoint. Meta sends this during webhook setup.

**Query Parameters**:
| Parameter | Value |
|-----------|-------|
| `hub.mode` | `subscribe` |
| `hub.verify_token` | Configured token (e.g., `climate`) |
| `hub.challenge` | Challenge string from Meta |

**Response**: Returns `hub.challenge` as plain text if `verify_token` matches.

---

### POST /whatsapp/webhookCloudApi

**Capability**: `@capability public`

Receives inbound WhatsApp messages from Meta Cloud API.

**Incoming Payload** (from Meta):
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "BUSINESS_ACCOUNT_ID",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": { "phone_number_id": "PHONE_ID" },
        "contacts": [{
          "profile": { "name": "Customer Name" },
          "wa_id": "919876543210"
        }],
        "messages": [{
          "id": "wamid.xxx",
          "from": "919876543210",
          "timestamp": "1710000000",
          "type": "text",
          "text": { "body": "Hi, I need pricing for turmeric" }
        }]
      }
    }]
  }]
}
```

**Processing**:
1. Parse message type and content
2. Download media to S3 (if applicable)
3. Find/create conversation
4. Store in `tbl_whatsapp_messages`
5. Log in `tbl_whatsapp_callback`
6. Push to Redis queue (real-time)
7. FCM notification to assigned agent

**Response**: 200 OK (Meta expects acknowledgment)

---

## Messaging

### POST /whatsapp/sendTextMessage

**Capability**: `@capability user`

Sends a text message to a customer via WhatsApp.

**Request**:
```json
{
  "phone": "919876543210",
  "message": "Thank you for your interest. Our turmeric is priced at Rs 250/kg.",
  "conversation_id": 123
}
```

**Response** (200):
```json
{
  "success": true,
  "data": { "message_id": "wamid.xxx", "status": "sent" }
}
```

---

### POST /whatsapp/sendTemplateMessage

**Capability**: `@capability user`

Sends a pre-approved template message.

**Request**:
```json
{
  "phone": "919876543210",
  "template_name": "order_confirmation",
  "template_language": "en",
  "components": [
    {
      "type": "body",
      "parameters": [
        { "type": "text", "text": "Rajesh" },
        { "type": "text", "text": "ORD-12345" },
        { "type": "text", "text": "Rs 15,000" }
      ]
    }
  ]
}
```

---

### POST /whatsapp/sendRateUpdates

**Capability**: `@capability user`

Sends commodity rate update broadcast to opted-in customers (`daily_rate_whatsapp = 1`).

---

### POST /whatsapp/mediaUpload

**Capability**: `@capability user`

Uploads a media file for sending via WhatsApp. Request is multipart form data with file.

---

## Conversation Management

### POST /whatsapp/getConversationsList

**Capability**: `@capability user`

Lists conversations with filters.

**Request**:
```json
{
  "page": 1,
  "per_page": 25,
  "filters": {
    "conversation_stage": "nurturing",
    "priority": "hot",
    "agent_id": 5,
    "date_from": "2026-03-01",
    "date_to": "2026-03-11"
  },
  "search": "rajesh"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": [
    {
      "conversation_id": 123,
      "contact_name": "Rajesh Kumar",
      "phone": "919876543210",
      "conversation_stage": "nurturing",
      "priority": "hot",
      "last_message": "Please send updated pricing",
      "last_activity_at": "2026-03-11T10:30:00",
      "unread_count": 3,
      "agent_name": "Priya Sharma"
    }
  ],
  "total": 45
}
```

---

### POST /whatsapp/getMessages

**Capability**: `@capability user`

Retrieves message history for a conversation.

**Request**:
```json
{
  "conversation_id": 123,
  "page": 1,
  "per_page": 50
}
```

---

### POST /whatsapp/closeConversation

**Capability**: `@capability user`

Closes a conversation.

---

## Customer Details

### POST /whatsapp/getAccountDetails

Gets account details for the customer in a conversation.

### POST /customers/customerBasicDetails

Gets basic customer details by phone/handle.

### POST /customers/linkCustomer

Links an existing customer account to a WhatsApp conversation.

### POST /customers/addCustomerToWhatsapp

Adds a customer to the WhatsApp system.

---

## Notes & Follow-ups

### POST /whatsapp/saveNotes

**Request**:
```json
{
  "conversation_id": 123,
  "note": "Customer interested in bulk order. Needs credit terms."
}
```

### POST /whatsapp/getNotes

### POST /whatsapp/deleteNote

### POST /whatsapp/saveFollowup

**Request**:
```json
{
  "conversation_id": 123,
  "followup_date": "2026-03-15",
  "followup_time": "10:00",
  "notes": "Call to discuss bulk pricing"
}
```

### POST /whatsapp/setFollowUpCompleted

---

## Cross-References

| Document | Path |
|----------|------|
| WhatsApp Integration Module | `04-core-modules/whatsapp-integration.md` |
| Messaging System | `04-core-modules/messaging-system.md` |
| CRM Tables (Messages schema) | `03-database-design/crm-tables.md` |
| Authentication | `05-api-documentation/authentication.md` |
| Message Flow | `06-data-flow/message-flow.md` |
