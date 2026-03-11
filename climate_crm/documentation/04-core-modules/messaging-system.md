# Messaging System

> Module: `climate/modules/messaging`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [Message Architecture](#message-architecture)
3. [Real-Time Delivery](#real-time-delivery)
4. [Call Integration](#call-integration)
5. [Push Notifications](#push-notifications)
6. [Notes System](#notes-system)
7. [Follow-up Scheduling](#follow-up-scheduling)
8. [Media Handling](#media-handling)
9. [Cross-References](#cross-references)

---

## Overview

The messaging system provides unified multi-channel communication — WhatsApp, phone calls, email — all linked to conversations and contacts. Messages are stored centrally and delivered in real-time via WebSocket.

---

## Message Architecture

### Storage

```
tbl_whatsapp_messages (primary message store)
│
├── message_source = 'whatsapp'     → WhatsApp messages
├── message_source = 'call'         → Call records/logs
├── message_source = 'email'        → Email messages
└── message_source = 'system'       → System-generated messages

tbl_conversation_messages (conversation-linked messages)
│
└── Additional message metadata linked to tbl_open_conversations
```

### Message Fields

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | INT | Link to tbl_open_conversations |
| `handle_value` | VARCHAR(255) | Phone/email/handle identifier |
| `text` | TEXT | Message content |
| `type` | ENUM | text, image, audio, video, document, contact, etc. |
| `sender` | ENUM | customer, agent, system |
| `sender_name` | VARCHAR(255) | Display name |
| `message_source` | VARCHAR | Channel: whatsapp, call, email |
| `message_status` | VARCHAR | Delivery/read status |
| `agent_id` | INT | Sending/receiving agent |
| `media_id` | VARCHAR | Media attachment S3 key |
| `timestamp` | INT | Unix timestamp |
| `read_at` | DATETIME | Message read timestamp |
| `delivered_at` | DATETIME | Message delivered timestamp |

---

## Real-Time Delivery

### WebSocket Communication

```
Agent Browser ◄──── WebSocket ────► PHP Backend (Chat_websocket)
     │                                    │
     │                                    ├── AuthChat() → JWT verify
     │                                    ├── JoinChat() → Room join
     │                                    ├── OutgoingChat() → Send + store
     │                                    └── TimerChat() → Keep-alive
     │
     ├── Subscribe to conversation room
     ├── Receive real-time messages
     ├── Send outgoing messages
     └── Receive call status updates
```

### Message Protocol

```json
{
  "chatType": "outgoing",
  "token": "<JWT>",
  "user_id": 123,
  "message": "Hello, how can I help you?",
  "phone": "919876543210",
  "type": "text",
  "current_time": "2026-03-11T10:30:00"
}
```

### WebSocket Auto-Reconnect

- On disconnect → auto-reconnect attempt
- Exception: disconnect code `3001` → do not reconnect (intentional close)
- Reconnection restores conversation subscriptions

---

## Call Integration

### Call Tracking

Call records are stored in `tbl_call_logs` with links to conversations:

| Field | Description |
|-------|-------------|
| `customer_phone` | Customer phone number |
| `handle_value` | Normalized phone handle |
| `conversation_id` | Linked conversation |
| `contact_id` | Linked contact |
| `account_id` | Linked account |
| Duration, type, status | Call metadata |

### Call Status (Real-Time)

The WebSocket service tracks active call states with visual indicators:

| Status | Description | Auto-Clear |
|--------|-------------|------------|
| `Call Initiated` | Call being set up | No |
| `Calling` | Outgoing call in progress | No |
| `Ringing` | Phone is ringing | No |
| `On Call` | Active call | No |
| `Call Missed` | Unanswered call | 4 seconds |
| `Call Ended` | Call has ended | 4 seconds |
| `Incoming Call` | Incoming call alert | No |
| `Error` | Call error | 4 seconds |

### Call Status Lookup Strategy

Multiple fallbacks to match a call to a conversation:

```
1. Look up by conversation_id (primary, exact match)
   │ Not found?
   ▼
2. Look up by contact_id
   │ Not found?
   ▼
3. Look up by handle_value (phone number, fallback)
```

### Call Tip Display

Active call status is shown as a "call tip" in the topbar:

```
Frontend: TopbarService.callTip$ ← BehaviorSubject
    │
    └── HeaderComponent displays:
        [Phone Icon] "On Call with 919876543210" [End Call]
```

---

## Push Notifications

### Firebase Cloud Messaging (FCM)

```
New message arrives (webhook)
    │
    ▼
Backend: FirebaseController/sendNotification
    │
    ├── Build notification:
    │   {
    │     notification: { title: "New Message", body: "Customer sent..." },
    │     data: { type: "whatsapp_message", conversation_id: "123" }
    │   }
    │
    └── Send to agent's FCM token
        │
        ▼
    ┌───┼───┐
    │       │
    ▼       ▼
 Background   Foreground
 (SW handles) (FCM Service)
               ├── Play notification.wav
               ├── Show NotificationComponent (10s popup)
               └── Increment notificationCount$
```

### Notification Sound

Audio file: `/assets/sounds/notification.wav`
Played on: New message received while app is in foreground.

### Notification Component

Dynamically created component:
- Attached to DOM via `ApplicationRef`
- Shows: title, message, action data
- Auto-dismisses after 10 seconds
- Click navigates to relevant conversation

---

## Notes System

Internal notes attached to conversations (not sent to customer):

### API Endpoints

| Action | Endpoint | Method |
|--------|----------|--------|
| Save | `/whatsapp/saveNotes` | POST |
| Get All | `/whatsapp/getNotes` | POST |
| Delete | `/whatsapp/deleteNote` | POST |

### Note Fields

| Field | Description |
|-------|-------------|
| Text content | Note body |
| Agent ID | Who created the note |
| Timestamp | When created |
| Conversation ID | Linked conversation |

---

## Follow-up Scheduling

### Manual Scheduling

Agent schedules a follow-up task:

| Action | Endpoint | Method |
|--------|----------|--------|
| Schedule | `/whatsapp/saveFollowup` | POST |
| Complete | `/whatsapp/setFollowUpCompleted` | POST |
| Check | `/openconversations/checkFollowupRequired` | GET |

### Automated Processing

```
Cron::processScheduledFollowups()
    │
    ├── Query for due follow-ups (scheduled_at <= NOW())
    ├── For each:
    │   ├── Send FCM notification to assigned agent
    │   ├── Update pendingFollowupsTrigger
    │   └── Mark as notified
    │
    └── Agent sees in UI and takes action
```

---

## Media Handling

### Inbound Media (from Customer)

```
WhatsApp webhook receives media message
    │
    ├── Extract media_id from webhook payload
    ├── GET media URL from Meta Cloud API
    ├── Download binary content
    ├── Upload to AWS S3
    ├── Store S3 key in tbl_whatsapp_messages.media_id
    └── Message displayed with media preview in chat
```

### Outbound Media (from Agent)

```
Agent selects file to send
    │
    ├── Upload to S3 via pre-signed URL (upload.service.ts)
    ├── Get S3 URL
    ├── Send to WhatsApp Cloud API as media message
    └── Store in tbl_whatsapp_messages
```

### Supported Media Types

| Type | Max Size | Formats |
|------|----------|---------|
| Image | 5MB | JPEG, PNG |
| Video | 16MB | MP4 |
| Audio | 16MB | MP3, OGG, AAC |
| Document | 100MB | PDF, DOCX, XLSX |

### Media Access

- **Private files**: Accessed via time-limited pre-signed S3 URLs
- **CDN assets**: Served via CloudFront CDN URLs
- **Download**: `whatsapp.service.ts` provides download methods

---

## Cross-References

| Document | Path |
|----------|------|
| Communication Patterns | `01-system-architecture/communication-patterns.md` |
| CRM Tables (Messages schema) | `03-database-design/crm-tables.md` |
| WhatsApp Integration | `04-core-modules/whatsapp-integration.md` |
| WhatsApp API | `05-api-documentation/whatsapp-api.md` |
| Message Flow | `06-data-flow/message-flow.md` |
