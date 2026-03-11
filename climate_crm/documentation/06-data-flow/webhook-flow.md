> Module: climate/data-flow/webhook-flow
> Last updated: 2026-03-11

# Webhook Flow

## Table of Contents

- [Overview](#overview)
- [WhatsApp Cloud API Webhook](#whatsapp-cloud-api-webhook)
  - [Verification (One-Time Setup)](#verification-one-time-setup)
  - [Message Reception](#message-reception)
  - [Status Updates](#status-updates)
  - [Supported Message Types](#supported-message-types)
- [JustDial Webhook](#justdial-webhook)
  - [Registration](#registration)
  - [Lead Reception](#lead-reception)
  - [Lead-to-Conversation Flow](#lead-to-conversation-flow)
- [Facebook Leads Webhook](#facebook-leads-webhook)
- [IndiaMart Integration](#indiamart-integration)
- [External API (X-API-KEY)](#external-api-x-api-key)
- [Webhook Security](#webhook-security)
- [Error Handling](#error-handling)
- [Data Flow Summary](#data-flow-summary)
- [Cross-References](#cross-references)

---

## Overview

This document describes how external webhook integrations deliver data into the CRM system — covering WhatsApp, JustDial, Facebook Leads, and IndiaMart.

---

## WhatsApp Cloud API Webhook

### Verification (One-Time Setup)

```
WhatsApp sends GET request to verify endpoint:

GET /whatsapp/webhookCloudApi
    ?hub.mode=subscribe
    &hub.verify_token=climate
    &hub.challenge=<random_string>
    │
    ▼
Whatsapp::webhookCloudApi()
    │
    ├── Check hub.verify_token == 'climate'
    ├── If valid → echo hub.challenge
    └── If invalid → return 403
```

### Message Reception

```
WhatsApp Cloud API sends POST on new message:

POST /whatsapp/webhookCloudApi
{
  "object": "whatsapp_business_account",
  "entry": [{
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": { "phone_number_id": "..." },
        "contacts": [{ "profile": { "name": "Customer" }, "wa_id": "919876543210" }],
        "messages": [{
          "from": "919876543210",
          "id": "wamid.xxx",
          "timestamp": "1710000000",
          "type": "text",
          "text": { "body": "Hello" }
        }]
      }
    }]
  }]
}
    │
    ▼
Processing Pipeline:
    │
    ├── 1. Store raw payload → tbl_whatsapp_callback (audit)
    │
    ├── 2. Loop: entry → changes → messages
    │   ├── Extract message fields
    │   ├── Download media (if applicable)
    │   └── Build message + contact data structures
    │
    ├── 3. ContactMessageModel::processIncomingMessage()
    │   ├── Handle lookup/creation
    │   ├── Conversation management
    │   ├── Message insertion
    │   └── Real-time push
    │
    └── 4. Return HTTP 200 (WhatsApp requires fast response)
```

### Status Updates

```
POST /whatsapp/webhookCloudApi
{
  "entry": [{
    "changes": [{
      "value": {
        "statuses": [{
          "id": "wamid.xxx",
          "status": "delivered",
          "timestamp": "1710000001",
          "recipient_id": "919876543210"
        }]
      }
    }]
  }]
}
    │
    ▼
├── Find message by wamid in tbl_whatsapp_messages
├── Update status: sent → delivered → read
└── Push status update via WebSocket → UI indicators
```

### Supported Message Types

| Type | Handling |
|------|----------|
| `text` | Store body text directly |
| `image` | Download from Media API → upload to S3 |
| `document` | Download → S3, store filename |
| `video` | Download → S3 |
| `audio` | Download → S3 |
| `button` | Store button payload text |
| `reaction` | Store emoji reaction |
| `location` | Store latitude/longitude |

---

## JustDial Webhook

### Registration

```
POST /justdial/registerClient
{
  "client_name": "JUSTDIAL"
}
    │
    ▼
├── Validate: client_name must be 'JUSTDIAL'
├── Generate API credentials:
│   └── ApiAuthModel → api_key + api_secret
└── Store in tbl_api_auth
```

### Lead Reception

```
GET/POST /justdial/receiveLead
    ?API-KEY=<api_key>
    &leadid=JD12345
    &name=Customer Name
    &mobile=9876543210
    &phone=
    &email=customer@email.com
    &category=Spices
    &city=Mumbai
    &area=Andheri
    &pincode=400053
    &date=2026-03-11
    &time=10:30
    &dncmobile=0
    &dncphone=0
    │
    ▼
Justdial::receiveLead()
    │
    ├── 1. Authenticate:
    │   └── ApiAuthModel::authenticate(api_key)
    │       Validate against tbl_api_auth
    │
    ├── 2. Validate:
    │   ├── API-KEY required
    │   └── leadid required
    │
    ├── 3. Save:
    │   └── JustDialModel::saveLead()
    │       INSERT tbl_justdial_leads:
    │       ├── lead_id (JustDial's ID)
    │       ├── raw_data (JSON of all params)
    │       ├── name, mobile, email
    │       ├── category, city, area, pincode
    │       └── created_at
    │
    ├── 4. Queue for processing:
    │   └── queue::push('justdial_lead'):
    │       ├── chatType: 'lead_created'
    │       ├── source: 'justdial'
    │       ├── lead_id, mobile, name
    │       └── timestamp
    │
    └── 5. Response: "RECEIVED" (plain text)
```

### Lead-to-Conversation Flow

```
JustDial lead in queue
    │
    ├── Background process picks up lead
    │
    ├── Normalize phone number (10-digit)
    │
    ├── Check for existing contact:
    │   ├── Exists → link to existing account
    │   └── New → create contact + handle
    │
    ├── Create conversation:
    │   ├── source_id = JustDial source
    │   ├── conversation_type = 'contact'
    │   └── Agent assigned via round-robin
    │
    └── Real-time notification to assigned agent
```

---

## Facebook Leads Webhook

```
POST /facebookleads/webhook
{
  "entry": [{
    "changes": [{
      "value": {
        "leadgen_id": "FB12345",
        "form_id": "form_xxx",
        "field_data": [
          { "name": "full_name", "values": ["Customer Name"] },
          { "name": "phone_number", "values": ["+919876543210"] },
          { "name": "email", "values": ["customer@email.com"] }
        ]
      }
    }]
  }]
}
    │
    ▼
Facebookleads::webhook()
    │
    ├── 1. Verify webhook signature
    │
    ├── 2. Parse lead data from field_data array
    │
    ├── 3. Store raw lead:
    │   └── INSERT tbl_facebook_leads
    │
    ├── 4. Process into CRM:
    │   ├── Normalize phone number
    │   ├── Create/find contact
    │   ├── Create conversation with source = 'Facebook'
    │   └── Assign agent
    │
    └── 5. Return HTTP 200
```

---

## IndiaMart Integration

Unlike webhooks, IndiaMart uses a **pull-based** approach via cron:

```
Cron::indiaMartLeads() (runs periodically)
    │
    ├── Call IndiaMart API:
    │   GET https://mapi.indiamart.com/wservce/...
    │   &glusr_crm_key=<api_key>
    │   &start_time=<last_sync_time>
    │
    ├── Parse response (JSON array of leads)
    │
    ├── For each lead:
    │   ├── Check if already imported (by indiamart_lead_id)
    │   ├── If new:
    │   │   ├── Store in tbl_indiamart_leads
    │   │   ├── Normalize phone number
    │   │   ├── Create/find contact + handle
    │   │   ├── Create conversation:
    │   │   │   source = 'IndiaMart'
    │   │   └── Assign agent
    │   └── If duplicate → skip
    │
    └── Update last_sync_time in settings
```

---

## External API (X-API-KEY)

Third-party systems can push data via the External API:

```
POST /externalapi/opportunityAndProfile
Header: X-API-KEY: <api_key>
{
  "account_name": "External Customer",
  "contact_name": "John Doe",
  "phone": "919876543210",
  "email": "john@external.com",
  "product_interest": "Turmeric Powder",
  "quantity": 500,
  "source": "Partner API"
}
    │
    ▼
ExternalApi::opportunityAndProfile()
    │
    ├── Authenticate:
    │   └── Validate X-API-KEY against tbl_justdial_credentials
    │       WHERE active = 1
    │
    ├── Create account (if not exists)
    │
    ├── Create contact + handle
    │
    ├── Create opportunity
    │
    └── Return: account_id, contact_id, opportunity_id
```

---

## Webhook Security

| Source | Authentication | Method |
|--------|---------------|--------|
| WhatsApp | `hub.verify_token` | Shared secret verification |
| JustDial | `API-KEY` header | API key from tbl_api_auth |
| Facebook | Webhook signature | HMAC-SHA256 verification |
| IndiaMart | `glusr_crm_key` | API key in request params |
| External API | `X-API-KEY` header | Key from tbl_justdial_credentials |

---

## Error Handling

All webhook handlers follow these principles:

1. **Fast response**: Return HTTP 200 quickly (WhatsApp may retry on slow responses)
2. **Raw storage**: Store raw payload before processing (tbl_whatsapp_callback, tbl_justdial_leads)
3. **Idempotency**: Check for duplicate lead_id/message_id before creating records
4. **Logging**: `log_message('error', ...)` for all failures
5. **Queue-based processing**: Heavy processing happens asynchronously via Redis queue

---

## Data Flow Summary

```
External Sources                    CRM System
─────────────────                   ──────────────

WhatsApp Cloud API ──webhook──►  Contact + Conversation + Messages
JustDial           ──webhook──►  Lead → Contact + Conversation
Facebook Leads     ──webhook──►  Lead → Contact + Conversation
IndiaMart          ──cron────►   Lead → Contact + Conversation
External API       ──POST───►   Account + Contact + Opportunity

                    All routes converge to:
                    ├── temp_tbl_contacts
                    ├── temp_tbl_contact_handles
                    ├── tbl_open_conversations
                    └── Agent assignment via AgentAssignmentHelper
```

---

## Cross-References

**Core Modules**
- [`04-core-modules/whatsapp-integration.md`](../04-core-modules/whatsapp-integration.md) — WhatsApp webhook handler, media download, and message processing pipeline
- [`04-core-modules/messaging-system.md`](../04-core-modules/messaging-system.md) — Redis queue and real-time push triggered after webhook processing
- [`04-core-modules/assignment-management.md`](../04-core-modules/assignment-management.md) — Agent assignment executed for every inbound lead source

**API Documentation**
- [`05-api-documentation/whatsapp-api.md`](../05-api-documentation/whatsapp-api.md) — Webhook endpoint specification and verification protocol

**Database Design**
- [`03-database-design/crm-tables.md`](../03-database-design/crm-tables.md) — `tbl_whatsapp_callback`, `tbl_open_conversations`, `temp_tbl_contact_handles` schema

**System Architecture**
- [`01-system-architecture/communication-patterns.md`](../01-system-architecture/communication-patterns.md) — Asynchronous queue patterns used for webhook processing and real-time delivery

**Related Data Flows**
- [`06-data-flow/message-flow.md`](./message-flow.md) — Detailed WhatsApp inbound message pipeline called from the webhook handler
- [`06-data-flow/assignment-flow.md`](./assignment-flow.md) — Round-robin and priority-based assignment triggered by each new lead
- [`06-data-flow/conversation-lifecycle.md`](./conversation-lifecycle.md) — Conversation creation and NEW stage that results from all inbound lead sources
