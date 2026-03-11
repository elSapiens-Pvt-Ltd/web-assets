# WhatsApp Integration Module

> Module: `climate/modules/whatsapp`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Inbound Message Processing](#inbound-message-processing)
4. [Outbound Message Sending](#outbound-message-sending)
5. [Real-Time Chat Interface](#real-time-chat-interface)
6. [Notes & Follow-ups](#notes--follow-ups)
7. [Call Integration](#call-integration)
8. [Frontend Service](#frontend-service)
9. [Backend Components](#backend-components)
10. [Cross-References](#cross-references)

---

## Overview

The WhatsApp module provides full integration with the **Meta WhatsApp Business Cloud API**, enabling real-time customer communication directly within the CRM. It is the primary communication channel for the sales team.

---

## Architecture

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐
│   Customer   │     │  Meta WhatsApp    │     │   PHP Backend    │
│  WhatsApp    │────►│  Cloud API        │────►│  Webhook         │
│  App         │     │                   │     │  /whatsapp/      │
└──────────────┘     └───────────────────┘     │  webhookCloudApi │
                                               └────────┬─────────┘
                                                        │
                         ┌──────────────────────────────┤
                         │              │               │
                  ┌──────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
                  │   MySQL     │ │  Redis    │ │  AWS S3     │
                  │  (Messages) │ │  (Queue)  │ │  (Media)    │
                  └─────────────┘ └─────┬─────┘ └─────────────┘
                                        │
                                 ┌──────▼──────┐
                                 │  WebSocket  │
                                 │  Server     │
                                 └──────┬──────┘
                                        │
                  ┌─────────────────────┤─────────────────────┐
                  │                     │                     │
           ┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
           │  Agent 1    │      │  Agent 2    │      │  Agent 3    │
           │  Browser    │      │  Browser    │      │  Browser    │
           └─────────────┘      └─────────────┘      └─────────────┘
```

---

## Inbound Message Processing

### Webhook Receiver

**Endpoint**: `POST /whatsapp/webhookCloudApi`
**Capability**: `@capability public` (no auth — Meta sends webhooks)

### Processing Steps

```
1. Receive webhook POST from Meta
   │
   ├── Verify webhook structure
   │
   ├── Extract message data:
   │   ├── Phone number (wa_id)
   │   ├── Message type (text/image/video/audio/document/contact/reaction/button)
   │   ├── Message content
   │   ├── Timestamp
   │   └── Message ID (wamid)
   │
   ├── Handle media (if applicable):
   │   ├── Get media URL from Meta API
   │   ├── Download binary content
   │   └── Upload to AWS S3
   │
   ├── Find/create conversation:
   │   ├── Look up phone in temp_tbl_contact_handles
   │   ├── If found → get existing conversation
   │   └── If not → create new conversation in tbl_open_conversations
   │
   ├── Store message:
   │   └── Insert into tbl_whatsapp_messages
   │       ├── conversation_id
   │       ├── handle_value = phone number
   │       ├── text = message content
   │       ├── type = message type
   │       ├── sender = 'customer'
   │       └── message_source = 'whatsapp'
   │
   ├── Real-time notification:
   │   ├── Push to Redis queue
   │   └── WebSocket broadcast to assigned agent
   │
   └── Push notification:
       └── FCM notification to assigned agent's device
```

### Supported Message Types

| Type | Processing | Storage |
|------|-----------|---------|
| `text` | Direct text extraction | `text` column |
| `image` | Download from Meta → S3 upload | S3 key in `media_id` |
| `video` | Download from Meta → S3 upload | S3 key in `media_id` |
| `audio` | Download from Meta → S3 upload | S3 key in `media_id` |
| `document` | Download from Meta → S3 upload | S3 key in `media_id` |
| `contact` | Parse vCard data | JSON in `text` |
| `reaction` | Extract emoji + referenced message | Emoji in `text` |
| `button` | Extract button payload | Button text in `text` |

### Webhook Verification (GET)

Meta verifies the webhook URL during setup:

```
GET /whatsapp/webhookCloudApi?
    hub.mode=subscribe&
    hub.verify_token=climate&
    hub.challenge=CHALLENGE_STRING

Response: echo CHALLENGE_STRING (plain text)
```

---

## Outbound Message Sending

### Text Messages

**Endpoint**: `POST /whatsapp/sendTextMessage`

```json
{
  "phone": "919876543210",
  "message": "Hello! Your order has been confirmed.",
  "conversation_id": 123
}
```

Flow:
1. Agent types message in chat window
2. Frontend sends via WebSocket (`OutgoingChat` event)
3. Backend sends to WhatsApp Cloud API
4. Message stored in `tbl_whatsapp_messages` (sender = 'agent')
5. Delivery/read receipts update `message_status`

### Template Messages

**Endpoint**: `POST /whatsapp/sendTemplateMessage`

Pre-approved templates (by Meta) for proactive outreach:

```json
{
  "phone": "919876543210",
  "template_name": "order_confirmation",
  "template_language": "en",
  "components": [
    {
      "type": "body",
      "parameters": [
        { "type": "text", "text": "John" },
        { "type": "text", "text": "ORD-12345" }
      ]
    }
  ]
}
```

### Rate Update Broadcasts

**Endpoint**: `POST /whatsapp/sendRateUpdates`

Sends commodity rate updates to customers who have `daily_rate_whatsapp = 1` in their contact record.

### Media Uploads

**Endpoint**: `POST /whatsapp/mediaUpload`

For sending images, documents, etc. from agent to customer:
1. Upload file to S3 via pre-signed URL
2. Get S3 URL
3. Send media message via WhatsApp Cloud API

---

## Real-Time Chat Interface

### WebSocket Connection

The Angular `WebSocketService` maintains a persistent WebSocket connection for live chat:

```
Chat Window opened
    │
    ├── WebSocket.connect(environment.wssUrl)
    ├── Send 'auth' message with JWT token
    ├── On success: Send 'join' for current conversation
    │
    ├── Incoming messages → Display in chat window
    │   └── Play notification sound for new messages
    │
    └── Outgoing messages → Send via 'outgoing' event
        └── Broadcast to WhatsApp + database
```

### Chat Window Components

```
┌─────────────────────────────────────────────────────────┐
│  WhatsApp Module Layout                                  │
│                                                          │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────┐  │
│  │ Conversations│  │                  │  │ Customer  │  │
│  │ List         │  │  Chat Window     │  │ Details   │  │
│  │              │  │                  │  │           │  │
│  │ - Filters    │  │  - Message list  │  │ - Account │  │
│  │ - Search     │  │  - Media preview │  │ - Contacts│  │
│  │ - Status     │  │  - Call status   │  │ - Orders  │  │
│  │ - Agent      │  │                  │  │ - Notes   │  │
│  │ - Priority   │  │  ──────────────  │  │ - Followup│  │
│  │              │  │  [Message Input] │  │           │  │
│  │              │  │  [Attach] [Send] │  │           │  │
│  └──────────────┘  └──────────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Conversation List Features

The `ConversationsListComponent` uses `OnPush` change detection and manages filter state, search with debounce, WebSocket subscriptions, and a mandatory follow-up queue:

```typescript
@Component({
  selector: 'app-conversations-list',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ConversationsListComponent implements OnInit, OnDestroy {
  conversations: WhatsAppContact[] = [];
  filters: any;
  start = 0;
  limit = 50;

  // Mandatory followup queue management
  pendingFollowupQueue: PendingFollowupConversation[] = [];
  private readonly MAX_QUEUE_SIZE = 20;
  private processedFollowupConversations = new Set<number>();
}
```

- **Filters**: By stage, priority, agent, date range
- **Search**: By customer name, phone number (debounced)
- **Real-time updates**: New messages update list position and unread count via WebSocket
- **Filter persistence**: Saved to localStorage for session continuity

---

## Notes & Follow-ups

### Notes

Agents can attach internal notes to conversations (not sent to the customer):

| Action | Endpoint |
|--------|----------|
| Save Note | `POST /whatsapp/saveNotes` |
| Get Notes | `POST /whatsapp/getNotes` |
| Delete Note | `POST /whatsapp/deleteNote` |

### Follow-ups

Agents can schedule follow-up reminders:

| Action | Endpoint |
|--------|----------|
| Schedule Follow-up | `POST /whatsapp/saveFollowup` |
| Complete Follow-up | `POST /whatsapp/setFollowUpCompleted` |
| Check Pending | `GET /openconversations/checkFollowupRequired` |

Follow-up processing is automated via `Cron::processScheduledFollowups`.

---

## Call Integration

### Call Status Tracking

The WebSocket service tracks call states in real-time:

| Status | Description | Auto-Clear |
|--------|-------------|------------|
| Call Initiated | Call being set up | No |
| Calling | Outgoing call in progress | No |
| Ringing | Phone is ringing | No |
| On Call | Active call | No |
| Call Missed | Unanswered call | 4 seconds |
| Call Ended | Call has ended | 4 seconds |
| Incoming Call | Incoming call alert | No |
| Error | Call error | 4 seconds |

Call status is displayed as a **call tip** in the topbar via `TopbarService.callTip$`.

### Call Status Lookup

The WebSocket service uses multiple fallback strategies to match a call to a conversation:
1. By `conversation_id` (primary)
2. By `contact_id`
3. By `handle_value` (phone number)

---

## Frontend Service

### WhatsAppService (`whatsapp.service.ts`)

40+ API endpoints organized by domain:

**Messaging**: `sendTextMessage()`, `sendTemplateMessage()`, `sendRateUpdates()`, `mediaUpload()`

**Conversations**: `getConversationsList()`, `getOpenConversations()`, `closeConversation()`, `getMessages()`

**Customer/Account**: `getAccountDetails()`, `customerBasicDetails()`, `linkCustomer()`, `addCustomerToWhatsapp()`

**Notes/Follow-ups**: `saveNotes()`, `getNotes()`, `deleteNote()`, `saveFollowup()`, `setFollowUpCompleted()`

**State Management**:
- `conversationFiltersState`: BehaviorSubject for filter persistence
- `initiateNewChatTrigger`: Trigger to start new chat
- `refreshTrigger`: Force refresh conversation list
- `agentNumberChangedTrigger`: Agent phone number changed
- `pendingFollowupsTrigger`: Pending follow-ups notification
- `conversationUpdatedTrigger`: Conversation updated (from WebSocket)

### File Downloads

Media files are accessed via pre-signed S3 URLs for security:

```typescript
this.whatsappService.getMediaUrl(mediaKey).subscribe(url => {
  window.open(url, '_blank');
});
```

---

## Backend Components

### Controllers

| Controller | Purpose |
|------------|---------|
| `Whatsapp` | WhatsApp webhook, messaging, conversation management |
| `WhatsappChat` | WebSocket real-time chat server (Ratchet) |

### Models

| Model | Purpose |
|-------|---------|
| `WhatsappModel` | WhatsApp-specific database operations |
| `ConversationMessagesModel` | Message storage and retrieval |
| `OpenConversationsModel` | Conversation lifecycle management |

### Key Database Tables

| Table | Purpose |
|-------|---------|
| `tbl_whatsapp_messages` | All messages (inbound + outbound) |
| `tbl_open_conversations` | Active conversations |
| `tbl_whatsapp_callback` | Webhook event log |
| `tbl_whatsapp_contacts` | Legacy WhatsApp contact records |

---

## Cross-References

| Document | Path |
|----------|------|
| Communication Patterns | `01-system-architecture/communication-patterns.md` |
| CRM Tables (Messages schema) | `03-database-design/crm-tables.md` |
| WhatsApp API | `05-api-documentation/whatsapp-api.md` |
| Message Flow | `06-data-flow/message-flow.md` |
| Webhook Flow | `06-data-flow/webhook-flow.md` |
| Messaging System | `04-core-modules/messaging-system.md` |
