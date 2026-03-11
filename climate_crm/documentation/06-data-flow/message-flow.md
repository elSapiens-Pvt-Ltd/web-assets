> Module: climate/data-flow/message-flow
> Last updated: 2026-03-11

# Message Flow

## Table of Contents

- [Overview](#overview)
- [Inbound WhatsApp Message Flow](#inbound-whatsapp-message-flow)
- [Outbound Message Flow](#outbound-message-flow)
- [Template Message Flow](#template-message-flow)
- [Media Message Flow](#media-message-flow)
  - [Inbound Media](#inbound-media)
  - [Outbound Media](#outbound-media)
- [Message Status Updates](#message-status-updates)
- [Phone Number Normalization](#phone-number-normalization)
- [Database Tables Involved](#database-tables-involved)
- [Real-Time Architecture](#real-time-architecture)
- [Cross-References](#cross-references)

---

## Overview

This document traces how messages flow through the system — from external sources (WhatsApp, JustDial, etc.) through backend processing, database storage, real-time delivery, and frontend rendering.

---

## Inbound WhatsApp Message Flow

```
WhatsApp Cloud API
    │
    ▼
┌──────────────────────────────────────────────────┐
│ Whatsapp::webhookCloudApi()                      │
│                                                  │
│ 1. Verify webhook (GET):                         │
│    hub_verify_token == 'climate'                  │
│    → echo hub_challenge                          │
│                                                  │
│ 2. Receive message (POST):                       │
│    entry[].changes[].value.messages[]             │
│    entry[].changes[].value.statuses[]             │
│    entry[].changes[].value.contacts[]             │
└──────────┬───────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│ Parse Message                                    │
│                                                  │
│ Extract:                                         │
│ ├── message_id (WhatsApp UUID)                   │
│ ├── message.from (sender phone)                  │
│ ├── message.text / message.{type}.* (content)    │
│ ├── message.timestamp                            │
│ └── message.type (text/image/document/video/     │
│                   audio/button/reaction)          │
│                                                  │
│ Media handling (if non-text):                    │
│ ├── WhatsappModel::getMedia($media_id)           │
│ └── Upload to S3 → get media_key                 │
└──────────┬───────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│ Save raw webhook to tbl_whatsapp_callback        │
│ (audit log of all webhook payloads)              │
└──────────┬───────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│ ContactMessageModel::processIncomingMessage()    │
│                                                  │
│ Step 1: Handle Lookup                            │
│ ├── Search temp_tbl_contact_handles              │
│ │   (by normalized 10-digit phone)               │
│ ├── If found → get contact_id, account_id        │
│ └── If not found:                                │
│     ├── Create temp_tbl_contacts record          │
│     └── Create temp_tbl_contact_handles record   │
│         (handle_type='phone', is_whatsapp=1)     │
│                                                  │
│ Step 2: Conversation Management                  │
│ ├── Find open conversation for contact           │
│ │   (tbl_open_conversations WHERE contact_id)    │
│ ├── If exists:                                   │
│ │   ├── Update last_activity_at                  │
│ │   ├── Increment unread count                   │
│ │   ├── Auto-transition: attempted → contacted   │
│ │   └── Clear RNR disposition                    │
│ └── If not exists:                               │
│     ├── AgentAssignmentHelper::getAgentForHandle()│
│     └── Create new conversation:                 │
│         status='open', stage='new'               │
│                                                  │
│ Step 3: Insert Message                           │
│ └── tbl_whatsapp_messages:                       │
│     message_id, conversation_id, contact_id,     │
│     handle_id, text, type, sender='customer',    │
│     media_key                                    │
│                                                  │
│ Step 4: Real-Time Push                           │
│ ├── queue::pushNewConversation()                 │
│ └── queue::pushChatIncoming()                    │
└──────────┬───────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│ Redis Queue → WebSocket Server                   │
│                                                  │
│ Channels:                                        │
│ ├── 'new_conversation' → conversation list UI    │
│ └── 'chat_incoming' → chat window UI             │
│                                                  │
│ Data includes:                                   │
│ ├── conversation_id, contact_name                │
│ ├── message text/type                            │
│ ├── agent_id (target agent)                      │
│ ├── unread count                                 │
│ └── timestamp                                    │
└──────────┬───────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│ Frontend (Angular)                               │
│                                                  │
│ WebSocketService receives event:                 │
│ ├── ConversationsListComponent:                  │
│ │   ├── Update conversation in list              │
│ │   ├── Move to top (most recent)                │
│ │   └── Show unread badge                        │
│ └── ChatWindowComponent:                         │
│     ├── Append message to chat                   │
│     └── Scroll to bottom                         │
└──────────────────────────────────────────────────┘
```

---

## Outbound Message Flow

```
Agent types message in ChatWindowComponent
    │
    ▼
┌──────────────────────────────────────────────────┐
│ WhatsappService::sendWhatsappMessage()           │
│                                                  │
│ POST /Whatsapp/sendTextMessage                   │
│ Body: { handle_id, text, uuid }                  │
└──────────┬───────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│ Backend: Whatsapp::sendTextMessage()             │
│                                                  │
│ 1. Insert message in tbl_whatsapp_messages:      │
│    sender='agent', type='text'                   │
│                                                  │
│ 2. Call WhatsApp Cloud API:                      │
│    POST https://graph.facebook.com/v18.0/        │
│    {phone_number_id}/messages                    │
│    Body: { to: phone, type: 'text',              │
│            text: { body: message } }             │
│                                                  │
│ 3. Update message with WhatsApp message_id       │
│                                                  │
│ 4. Update conversation:                          │
│    last_activity_at = NOW()                      │
│                                                  │
│ 5. Queue status update for UI                    │
└──────────┬───────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│ WhatsApp Cloud API delivers message              │
│                                                  │
│ Status webhooks received:                        │
│ ├── sent → message queued                        │
│ ├── delivered → reached device                   │
│ ├── read → customer opened                       │
│ └── failed → delivery error                      │
│                                                  │
│ Each status update:                              │
│ ├── Stored in tbl_whatsapp_messages              │
│ └── Pushed via WebSocket to update UI            │
└──────────────────────────────────────────────────┘
```

---

## Template Message Flow

```
Agent selects template in ChatWindowComponent
    │
    ▼
POST /Whatsapp/sendTemplateMessage
    │
    ├── Validate template name and parameters
    ├── Build template payload for Cloud API
    ├── Send via WhatsApp Cloud API
    ├── Store in tbl_whatsapp_messages (type='template')
    └── Push status to UI
```

---

## Media Message Flow

### Inbound Media

```
WhatsApp sends media message
    │
    ├── Webhook contains media_id (not actual file)
    ├── Backend calls WhatsApp Media API:
    │   GET /{media_id} → returns download URL
    ├── Download media from URL
    ├── Upload to AWS S3:
    │   bucket/{media_key}
    ├── Store media_key in tbl_whatsapp_messages
    └── Frontend renders media:
        ├── image → <img> with CloudFront CDN URL
        ├── document → download link
        ├── video → <video> player
        └── audio → <audio> player
```

### Outbound Media

```
Agent attaches file in ChatWindowComponent
    │
    ├── Frontend uploads to S3 via pre-signed URL
    ├── POST /Whatsapp/sendMediaMessage
    │   { handle_id, media_key, type, caption }
    ├── Backend sends media via WhatsApp Cloud API
    └── Store in tbl_whatsapp_messages
```

---

## Message Status Updates

```
WhatsApp Cloud API sends status webhook
    │
    ▼
Whatsapp::webhookCloudApi()
    │
    ├── Parse: entry[].changes[].value.statuses[]
    ├── Extract: message_id, status, timestamp
    ├── Update tbl_whatsapp_messages:
    │   ├── status = 'sent' / 'delivered' / 'read' / 'failed'
    │   └── status_timestamp
    └── Push via WebSocket:
        └── ChatWindowComponent updates message indicators
            ├── ✓  sent
            ├── ✓✓ delivered
            ├── ✓✓ (blue) read
            └── ✕  failed
```

---

## Phone Number Normalization

All phone numbers are normalized before lookup/storage:

```
Input              → Normalized
+919876543210      → 9876543210
919876543210       → 9876543210
09876543210        → 9876543210
9876543210         → 9876543210
+91 98765 43210    → 9876543210
```

The `PhoneNumberHelper` strips country code (+91), leading zeros, and spaces to produce a consistent 10-digit Indian mobile number for database lookups.

---

## Database Tables Involved

| Table | Role |
|-------|------|
| `tbl_whatsapp_callback` | Raw webhook payload audit log |
| `tbl_whatsapp_messages` | Processed message storage |
| `tbl_open_conversations` | Conversation state |
| `temp_tbl_contacts` | Contact records |
| `temp_tbl_contact_handles` | Phone/email handles |
| `temp_tbl_accounts` | Account linkage |
| `tbl_whatsapp_token` | WhatsApp Cloud API credentials |

---

## Real-Time Architecture

```
Backend (PHP)
    │
    ├── Redis Queue (Predis)
    │   queue::push('channel', data)
    │
    ▼
WebSocket Server (Chat_websocket library)
    │
    ├── Reads from Redis queue
    ├── Routes to connected clients by agent_id
    │
    ▼
Frontend (Angular)
    │
    └── WebSocketService
        ├── Dev:  ws://localhost:8988
        └── Prod: wss://api.climatenaturals.com/chat
```

Messages flow through Redis as a broker between the PHP request lifecycle and the persistent WebSocket connections, enabling real-time delivery without polling.

---

## Cross-References

**Core Modules**
- [`04-core-modules/whatsapp-integration.md`](../04-core-modules/whatsapp-integration.md) — WhatsApp Cloud API integration, webhook handling, and media processing
- [`04-core-modules/conversations.md`](../04-core-modules/conversations.md) — Conversation state management and stage transitions
- [`04-core-modules/messaging-system.md`](../04-core-modules/messaging-system.md) — Real-time WebSocket and Redis queue architecture

**API Documentation**
- [`05-api-documentation/whatsapp-api.md`](../05-api-documentation/whatsapp-api.md) — Send message, send template, and media upload endpoints
- [`05-api-documentation/conversations-api.md`](../05-api-documentation/conversations-api.md) — Conversation retrieval and update endpoints

**Database Design**
- [`03-database-design/crm-tables.md`](../03-database-design/crm-tables.md) — `tbl_whatsapp_messages`, `tbl_whatsapp_callback`, `tbl_open_conversations` schema

**System Architecture**
- [`01-system-architecture/communication-patterns.md`](../01-system-architecture/communication-patterns.md) — WebSocket, Redis queue, and real-time delivery patterns

**Related Data Flows**
- [`06-data-flow/webhook-flow.md`](./webhook-flow.md) — Inbound webhook processing from WhatsApp and other sources
- [`06-data-flow/conversation-lifecycle.md`](./conversation-lifecycle.md) — Stage transitions triggered by message events
