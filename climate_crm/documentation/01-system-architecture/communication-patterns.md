# Communication Patterns

> Module: `climate/communication`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [HTTP REST API](#http-rest-api)
3. [WebSocket Real-Time](#websocket-real-time)
4. [Push Notifications (Firebase FCM)](#push-notifications-firebase-fcm)
5. [Webhook Integrations](#webhook-integrations)
6. [Redis Queue Bridge](#redis-queue-bridge)
7. [Cross-Tab Communication](#cross-tab-communication)
8. [External API Integration](#external-api-integration)
9. [File Upload/Download](#file-uploaddownload)
10. [Cross-References](#cross-references)

---

## Overview

The Climate CRM platform uses five distinct communication patterns to connect its components. HTTP REST handles all business operations. WebSocket provides real-time message delivery. Firebase FCM delivers push notifications when agents aren't actively viewing a conversation. Redis acts as a broker between the short-lived PHP request lifecycle and the persistent WebSocket server. External webhooks receive inbound leads from WhatsApp, JustDial, Facebook, and IndiaMart.

---

## HTTP REST API

All business operations between the Angular frontend and CodeIgniter backend flow through standard HTTP requests with JSON payloads.

### Request Format

```
Method:  POST (data operations), GET (retrieval)
URL:     {AppConfig.settings.apiServer.dataServer}/{Controller}/{method}
Headers:
  Authorization: Bearer <JWT_TOKEN>
  Content-Type: application/json
  User-Type: admin | customer
  CompanyId: <company_id>
  InAs: <impersonated_user_id>  (optional)
  web-version: <app_version>
Body:    JSON payload
```

The `JwtInterceptor` adds authentication headers automatically:

```typescript
// src/app/shared/helpers/jwt.interceptor.ts

intercept(request: HttpRequest<any>, next: HttpHandler) {
  if (!request.url.includes('.json')) {
    const currentUser = JSON.parse(localStorage.getItem("currentUserDetails"));
    request = request.clone({
      setHeaders: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
        InAs: localStorage.getItem("InAs") || '',
        CompanyId: currentUser?.company_id || ''
      }
    });
  }
  return next.handle(request);
}
```

### Response Format

All API responses use a consistent JSON structure encoded via `Risposta::json_encode()` which preserves numeric types:

**Success**:
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "total": 150,
  "page": 1,
  "per_page": 25
}
```

**Error**:
```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "field_name": "Specific field error"
  }
}
```

### Pagination Pattern

List endpoints accept pagination, search, sort, and filter parameters in the request body:

```json
{
  "page": 1,
  "per_page": 25,
  "search": "search term",
  "sort_by": "created_at",
  "sort_order": "desc",
  "filters": {
    "status": "active",
    "date_from": "2026-01-01",
    "date_to": "2026-03-11"
  }
}
```

### Error Handling

The `ErrorInterceptor` centralizes HTTP error handling:

```typescript
// src/app/shared/helpers/error.interceptor.ts

catchError(err => {
  switch (err.status) {
    case 400:
      this.snackBar.open(err.statusText, 'OK');
      // Session timeout or session change → auto-logout
      if (err.statusText?.includes('Session expired')
          || err.statusText?.includes('Session Change')) {
        this.clearSessionAndRedirect();
      }
      break;
    case 401:
      this.snackBar.open('Logged in on another device', 'OK');
      this.clearSessionAndRedirect();
      break;
    case 403:
      this.snackBar.open('Permission denied', 'OK');
      break;
  }
  return throwError(err);
})
```

| HTTP Status | Meaning | Frontend Behavior |
|-------------|---------|-------------------|
| `200` | Success | Update `lastActivityTime`, pass to component |
| `400` | Bad request / session error | Show snackbar, check for session timeout |
| `401` | Another device logged in | Clear session, redirect to login |
| `403` | Insufficient capability | Show "Permission denied" snackbar |
| `404` | Endpoint not found | Show "Not implemented" error |
| `422` | Validation error | Show field-level errors |

---

## WebSocket Real-Time

The WebSocket connection provides instant message delivery between the backend and connected agents. The Angular `WebSocketService` establishes a persistent connection on login and auto-reconnects on disconnect.

### Connection Flow

```
Frontend                              Backend
────────                              ───────
WebSocketService.wssConnect()
    │
    ├── new WebSocket(wssUrl) ──────► WhatsappChat (Chat_websocket)
    │                                      │
    ├── onopen                             │
    │   └── Send chatjoin ────────────────►│
    │       { chatType, token, user_id }   ├── AuthChat() → verify JWT
    │                                      ├── JoinChat() → register client
    │◄──── Welcome message ───────────────┘
    │
    ├── onmessage
    │   └── communicationWss.next(data)    TimerChat() polls Redis queue
    │       │                              └── Pushes new messages to
    │       └── Components subscribe           connected agents
    │
    └── onclose
        └── Auto-reconnect after 1s
            (unless code 3001 = intentional)
```

### Client-Side Implementation

```typescript
// src/app/shared/services/web-socket.service.ts

wssConnect() {
  this.connection = new WebSocket(environment.wssUrl);

  this.connection.onopen = (event) => {
    const joinMessage = {
      current_time: Date.now(),
      chatType: 'chatjoin',
      token: this.token,
      user_id: this.user.user_id,
    };
    this.connection.send(JSON.stringify(joinMessage));
  };

  this.connection.onmessage = (event) => {
    const data = JSON.parse(event.data);
    this.communicationWss.next(data);
  };

  this.connection.onclose = (e) => {
    if (e.code != 3001) {
      setTimeout(() => this.wssConnect(), 1000);
    }
  };
}
```

### Server-Side Callbacks

```typescript
// application/controllers/WhatsappChat.php

$this->chat_websocket->set_callback('chatauth', array($this, 'AuthChat'));
$this->chat_websocket->set_callback('chatjoin', array($this, 'JoinChat'));
$this->chat_websocket->set_callback('chatoutgoing', array($this, 'OutgoingChat'));
$this->chat_websocket->set_callback('chattimer', array($this, 'TimerChat'));
$this->chat_websocket->run();
```

| Callback | Direction | Purpose |
|----------|-----------|---------|
| `chatauth` | Client → Server | Authenticate WebSocket connection with JWT |
| `chatjoin` | Client → Server | Register client, send welcome message |
| `chatoutgoing` | Client → Server | Route outgoing message to WhatsApp API + broadcast |
| `chattimer` | Server → Client | Periodic tick — reads Redis queue, delivers pending messages |

### Message Protocol

All WebSocket messages use JSON:

```json
{
  "chatType": "chatjoin",
  "token": "<JWT_TOKEN>",
  "user_id": 123,
  "message": "Message content",
  "phone": "919876543210",
  "type": "text",
  "current_time": 1710145800000
}
```

---

## Push Notifications (Firebase FCM)

Firebase Cloud Messaging delivers browser push notifications for events that occur when the agent isn't actively viewing the relevant conversation.

### Notification Flow

```
Backend Event (new message, order update, transfer)
       │
       ▼
FirebaseController → Firebase Cloud Messaging API
       │                    │
       │               ┌────┴────────────────┐
       │               │                     │
       ▼               ▼                     ▼
  Service Worker    Foreground App       Topic Subscribers
  (background)     (app is open)
       │               │
       │          FcmService.listenForMessages()
       │               ├── Play notification.wav
       │               ├── triggerNotification()
       │               └── incrementNotificationCount()
       │
  firebase-messaging-sw.js
  └── Display browser notification
```

### Frontend Implementation

```typescript
// src/app/shared/services/firebase/fcm.service.ts

listenForMessages() {
  onMessage(this.messaging, (payload) => {
    if (payload?.notification) {
      const audio = new Audio('assets/sounds/notification.wav');
      audio.play().catch(() => {});
      this._notification.triggerNotification(
        payload.notification.title,
        payload.notification.body,
        payload.data
      );
      this._topbarService.incrementNotificationCount();
    }
  });
}
```

### FCM Token Lifecycle

```
Login:
  1. Request browser notification permission
  2. Get FCM device token via getToken()
  3. POST /firebase/saveFcmToken { token, user_id }
  4. Subscribe to relevant topics

Logout:
  1. POST /firebase/unsubscribeFromTopic { token, topic }
  2. Remove local FCM state
```

---

## Webhook Integrations

External services push data to the backend via webhooks. All incoming webhook payloads are stored raw before processing for debugging and replay.

### WhatsApp Cloud API

```
Meta Cloud API ──── POST ────► /whatsapp/webhookCloudApi (@capability public)
                                    │
                                    ├── Verify webhook (GET with challenge token)
                                    │
                                    ├── Store raw JSON in tbl_whatsapp_callback
                                    │
                                    ├── Parse message:
                                    │   ├── Normalize phone to 10-digit
                                    │   ├── Determine type (text/image/video/audio/document)
                                    │   └── Download media → AWS S3 (if applicable)
                                    │
                                    ├── ContactMessageModel::processIncomingMessage()
                                    │   ├── Look up handle in temp_tbl_contact_handles
                                    │   ├── Find or create conversation
                                    │   ├── Auto-transition: attempted → contacted
                                    │   └── Insert into tbl_whatsapp_messages
                                    │
                                    ├── Push to Redis queue → WebSocket delivery
                                    │
                                    └── FCM notification to assigned agent
```

**Supported Inbound Message Types**: text, image, video, audio, document, contact, reaction, button (quick reply)

### JustDial

```
JustDial API ──── POST ────► /justdial/receiveLead
                                │
                                ├── Verify API key (X-API-KEY header vs tbl_api_auth)
                                ├── Store raw lead in tbl_justdial_leads
                                ├── Create contact + handle
                                └── Create conversation with agent assignment
```

### Facebook Lead Ads

```
Facebook ──── POST ────► /facebookleads/webhook
                            │
                            ├── Verify HMAC-SHA256 signature
                            ├── Parse lead form field data
                            ├── Store in tbl_facebook_leads
                            └── Create contact + conversation
```

### IndiaMart (Cron-Based Pull)

```
Cron::indiaMartLeads() ──── GET ────► IndiaMart API
                                          │
                                          ├── Fetch leads since last sync timestamp
                                          ├── Deduplicate by IndiaMart lead ID
                                          ├── Create contacts + conversations
                                          └── Update last sync timestamp in tbl_settings
```

---

## Redis Queue Bridge

Redis bridges the gap between the short-lived PHP request lifecycle and the persistent WebSocket server. When a message is sent or received via HTTP, the controller pushes it to a Redis channel. The WebSocket server's `TimerChat` callback reads from the queue on a periodic interval and delivers messages to connected agents.

```
HTTP Request (message sent/received)
       │
       ▼
Controller pushes to Redis
  $this->redis->push('message_queue', $data)
       │
       ▼
Redis Queue (LibRedisQueue)
       │
       ▼
WebSocket TimerChat callback reads queue
       │
       ▼
Broadcast to connected agent's WebSocket
       │
       ▼
Frontend: communicationWss.next(data)
```

### Queue Channels

| Channel | Events |
|---------|--------|
| `message_queue` | New messages, message status updates |
| Conversation events | Stage changes, transfers, agent updates |
| Notification events | Follow-up reminders, order status changes |

---

## Cross-Tab Communication

The application synchronizes state across multiple browser tabs using localStorage events — no server-side coordination required.

```
Tab 1                    localStorage                Tab 2
─────                    ────────────                ─────
Activity detected ──► lastActivityTime ──► Timer reset
                        update (throttled 30s)

Logout ─────────────► multiTabLogoutFlag ──► Auto-logout
                        = true

Error response ─────► lastActivityTime ──► Session sync
                        update
```

The `IdleService` listens for `storage` events on `window` to detect changes from other tabs:

```typescript
private initStorageListener(): void {
  window.addEventListener('storage', (event) => {
    if (event.key === this.LOGOUT_FLAG_KEY) {
      this.logoutUser();
    }
    if (event.key === this.LAST_ACTIVITY_KEY) {
      this.resetTimers();
    }
  });
}
```

---

## External API Integration

### Outbound Calls

The backend makes outbound HTTP calls to external services:

| Service | Purpose | Authentication |
|---------|---------|----------------|
| WhatsApp Cloud API | Send messages, download media | Bearer token (Meta Graph API) |
| AWS S3 | Upload/download files | AWS SDK credentials |
| AWS SES | Transactional emails | AWS SDK credentials (ap-south-1) |
| Firebase FCM | Push notifications | Firebase service account |
| IndiaMart API | Pull leads | API key |
| Google Sheets API | Data export/import | Google service account |

### Inbound API (ExternalApiController)

The backend exposes REST endpoints for third-party systems:

```
POST /externalapi/saveUser
POST /externalapi/opportunityAndProfile
POST /externalapi/getStatesList

Authentication: X-API-KEY header
Verified against: tbl_justdial_credentials
```

---

## File Upload/Download

### S3 Pre-Signed URL Upload

The upload flow uses pre-signed URLs for direct browser-to-S3 uploads, avoiding the backend as a file proxy:

```
Frontend                    Backend                    AWS S3
────────                    ───────                    ──────

1. POST /images/getUploadUrl
   { extension, file_type }
                    ─────────────────►
                                        Generate pre-signed URL
                    ◄─────────────────
                    { uploadUrl, key }

2. PUT file binary
   (with progress)
                    ──────────────────────────────────────►

3. POST /images/postImage
   { key }
                    ─────────────────►
                                        Return CDN URL
                    ◄─────────────────
                    { url: 'https://d1r95e2xq05b34.cloudfront.net/...' }
```

```typescript
// src/app/shared/services/upload.service.ts

getUploadUrl(fileItem: FileItem) {
  const formData = new FormData();
  formData.append('extension', fileItem.file.type.replace(/.*\//, ""));
  formData.append('file_type', fileItem.file_type);
  return this.http.post<any>(
    AppConfig.settings.apiServer.dataServer + "/images/getUploadUrl",
    formData,
    { observe: 'events' }
  );
}

uploadS3File(file: File, url: string) {
  return this.http.put(url, file, {
    headers: { "Content-Type": file.type },
    reportProgress: true,
    observe: 'events'
  });
}
```

### WhatsApp Media Download

When a WhatsApp webhook delivers a media message, the backend downloads the file from Meta's API and stores it in S3:

```
WhatsApp webhook → media message
    │
    ├── GET media URL from Meta Graph API
    ├── Download binary content
    ├── Upload to S3 bucket
    ├── Store S3 key in tbl_whatsapp_messages
    └── Frontend accesses via CloudFront CDN URL
```

---

## Cross-References

| Document | Path |
|----------|------|
| System Architecture Overview | `01-system-architecture/overview.md` |
| Backend Architecture | `01-system-architecture/backend-architecture.md` |
| Frontend Architecture | `01-system-architecture/frontend-architecture.md` |
| Security & Auth | `01-system-architecture/security.md` |
| API Authentication | `05-api-documentation/authentication.md` |
| Message Flow (detailed) | `06-data-flow/message-flow.md` |
| Webhook Flow (detailed) | `06-data-flow/webhook-flow.md` |
| Backend Deployment | `07-deployment-guide/backend-setup.md` |
