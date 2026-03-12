# Channel Specifications

> Per-channel behavior, message types, capabilities, and constraints.
> All channel logic lives in the Communication Gateway — CRM is channel-agnostic.

---

## 1. Architecture

```
CRM Service (channel-agnostic)
    │
    │ Events (NATS)
    ↓
Communication Gateway
    │
    ├── WhatsApp Adapter ←→ Meta Cloud API
    ├── Voice Adapter ←→ Smartflo / SIP Provider
    ├── Email Adapter ←→ SES / SMTP
    ├── JustDial Adapter ←→ JustDial API
    ├── Facebook Adapter ←→ Facebook Lead Ads API
    ├── IndiaMart Adapter ←→ IndiaMart API
    ├── WebForm Adapter ←→ Webhook receiver
    └── [Future adapters: SMS, Instagram, Telegram, LINE, LiveChat]
```

### Unified Message Model

All channels normalize to this structure before CRM sees the message:

```json
{
  "id": "uuid",
  "external_message_id": "wamid.abc123...",
  "workspace_id": "uuid",
  "channel": "whatsapp",
  "direction": "inbound",
  "handle_type": "phone",
  "handle_value": "+919876543210",
  "sender_type": "customer",
  "content_type": "text",
  "content": {
    "body": "Hi, I need pricing for Grade A turmeric"
  },
  "status": "received",
  "metadata": {
    "whatsapp_message_type": "text",
    "profile_name": "Rahul Verma"
  },
  "timestamp": "2026-03-12T10:30:00Z"
}
```

---

## 2. WhatsApp Business API (Cloud API)

### Capabilities

| Feature | Supported |
|---------|-----------|
| Text messages | Yes |
| Images (JPEG, PNG) | Yes (up to 5MB) |
| Videos (MP4) | Yes (up to 16MB) |
| Documents (PDF, DOCX, XLSX, etc.) | Yes (up to 100MB) |
| Audio (AAC, MP3, OGG) | Yes (up to 16MB) |
| Location | Yes (latitude, longitude, name, address) |
| Contacts (vCard) | Yes |
| Stickers | Yes (WebP) |
| Interactive buttons (up to 3) | Yes |
| Interactive list (up to 10 sections, 10 rows each) | Yes |
| Template messages | Yes (pre-approved by Meta) |
| Reactions | Yes (emoji reactions to messages) |
| Reply/quote | Yes (reply to specific message) |
| Read receipts | Yes (sent, delivered, read) |
| Typing indicators | Inbound only (customer typing) |
| Group messages | No (business API is 1:1 only) |

### Messaging Rules

| Rule | Detail |
|------|--------|
| **24-hour session window** | After last customer message, business can send free-form messages for 24 hours. After that, only template messages allowed. |
| **Template messages** | Must be pre-approved by Meta. Categories: Marketing, Utility, Authentication. Templates have variables ({{1}}, {{2}}) filled at send time. |
| **Rate limits** | Tier-based: Tier 1 (1K/day), Tier 2 (10K/day), Tier 3 (100K/day), Tier 4 (unlimited). Based on quality rating. |
| **Quality rating** | Green (high), Yellow (medium), Red (low). Affected by user blocks and reports. Low quality → messaging limit decrease. |
| **Opt-in** | Business must have customer opt-in before sending templates. Not enforced by API but required by policy. |

### Content Type Mapping

| CRM content_type | WhatsApp message_type | Notes |
|------------------|-----------------------|-------|
| text | text | Plain text, max 4096 chars |
| image | image | JPEG/PNG, caption optional |
| video | video | MP4, caption optional |
| document | document | Any file type, filename required |
| audio | audio | AAC/MP3/OGG |
| template | template | Pre-approved, variables required |
| interactive_buttons | interactive (button) | Up to 3 buttons, each max 20 chars |
| interactive_list | interactive (list) | Header, body, footer, sections with rows |
| location | location | lat, lng, name, address |

### Status Tracking

```
Outbound message lifecycle:
  Queued → Sent → Delivered → Read → [Failed]

  sent:      Message accepted by WhatsApp servers
  delivered: Message reached customer's device
  read:      Customer opened/viewed the message
  failed:    Delivery failed (reasons: invalid number, template rejected, rate limited, etc.)
```

### Webhook Events

| Event | CRM Action |
|-------|------------|
| `messages` (inbound) | Create/update conversation, store message |
| `statuses` (delivery updates) | Update message delivery_status |
| `message_template_status_update` | Update template approval status |
| `errors` | Log error, notify admin if critical |

### Configuration Required

```json
{
  "phone_number_id": "1234567890",
  "waba_id": "9876543210",
  "access_token": "EAA...(encrypted)",
  "verify_token": "custom_verify_string",
  "webhook_url": "https://gw.example.com/webhooks/whatsapp/{workspace_id}",
  "business_profile": {
    "display_name": "Climate Sales",
    "about": "B2B Spice Trading"
  }
}
```

---

## 3. Voice (Smartflo / SIP)

### Capabilities

| Feature | Supported |
|---------|-----------|
| Inbound calls | Yes |
| Outbound calls (click-to-call) | Yes |
| Call recording | Yes (configurable) |
| Call transfer | Yes (warm/cold) |
| Call hold | Yes |
| IVR menu | Future |
| Voicemail | Future |
| Conference / 3-way call | Future |
| Call queue | Yes (round-robin ring) |

### Call Flow — Inbound

```
Customer dials DID number
  → Smartflo routes to workspace (by DID mapping)
  → Communication Gateway receives call event
  → Publishes: comm.call.incoming { workspace_id, caller, did_number }
  → CRM receives event:
      - Resolves contact by phone handle
      - Finds/creates conversation
      - Determines assigned agent (or runs assignment rules)
  → CRM notifies agent via WebSocket: incoming call popup
  → Agent answers in browser (WebRTC) or desk phone
  → Call connected, recording starts (if enabled)
  → Call ends
  → Communication Gateway publishes: comm.call.ended { duration, recording_url, status }
  → CRM auto-logs activity: call type, duration, recording URL
  → Agent prompted for disposition
```

### Call Flow — Outbound

```
Agent clicks phone icon on contact
  → CRM sends: comm.call.initiate { workspace_id, agent_id, target_number }
  → Communication Gateway initiates call via provider
  → Provider calls agent first → then bridges to customer
  → Same recording + activity logging as inbound
```

### Content Type Mapping

Voice doesn't produce traditional "messages" — instead it creates call event cards:

| CRM content_type | Voice Event | Notes |
|------------------|-------------|-------|
| call_event | call.incoming | Missed/answered, caller info |
| call_event | call.outgoing | Initiated by agent |
| call_event | call.ended | Duration, recording URL, status |
| call_event | call.transferred | Transfer source/target |

### Configuration Required

```json
{
  "provider": "smartflo",
  "api_key": "(encrypted)",
  "api_secret": "(encrypted)",
  "account_id": "ACC123",
  "did_numbers": ["+918045678900", "+918045678901"],
  "recording_enabled": true,
  "max_ring_duration_seconds": 30,
  "agent_endpoints": {
    "agent_person_id_1": { "type": "webrtc" },
    "agent_person_id_2": { "type": "sip", "extension": "101" }
  }
}
```

---

## 4. Email (SES / SMTP)

### Capabilities

| Feature | Supported |
|---------|-----------|
| Send plain text email | Yes |
| Send HTML email | Yes |
| Receive inbound email | Yes (via forwarding or MX) |
| Attachments (send) | Yes (up to 10MB total) |
| Attachments (receive) | Yes (stored in File Service) |
| CC / BCC | Yes |
| Reply threading (In-Reply-To) | Yes |
| Rich text compose | Yes (HTML editor in CRM) |
| Email templates | Yes (workspace-configurable) |
| Read tracking (pixel) | Future (optional, privacy concerns) |
| Bounce handling | Yes |
| Unsubscribe | Future |

### Email Threading

```
Inbound email arrives at: crm-{workspace_id}@inbound.elcrm.com
  → Communication Gateway receives via SES inbound / webhook
  → Parses: From, To, CC, Subject, Body (text + HTML), Attachments, In-Reply-To, Message-ID
  → Threading logic:
      1. Check In-Reply-To header → match to existing conversation's Message-ID
      2. If no match → check Subject + sender → fuzzy match to existing conversation
      3. If no match → create new conversation
  → Normalize to UnifiedMessage (content_type: email)
  → Publish comm.message.received event
```

### Content Type Mapping

| CRM content_type | Email Content | Notes |
|------------------|---------------|-------|
| email | Full email | subject, html_body, text_body, attachments[], cc, bcc |

### Status Tracking

```
Outbound email lifecycle:
  Queued → Sent → Delivered → [Bounced]

  sent:      Email accepted by SES/SMTP
  delivered: No bounce received (assumed delivered)
  bounced:   Hard bounce (invalid address) or soft bounce (mailbox full)

  Note: No "read" status for email (unlike WhatsApp) unless pixel tracking enabled.
```

### Configuration Required

```json
{
  "provider": "ses",
  "aws_region": "ap-south-1",
  "aws_access_key": "(encrypted)",
  "aws_secret_key": "(encrypted)",
  "from_address": "sales@clientdomain.com",
  "from_name": "Climate Sales",
  "reply_to": "sales@clientdomain.com",
  "inbound_address": "crm-ws123@inbound.elcrm.com",
  "domain_verified": true,
  "dkim_enabled": true
}
```

---

## 5. Lead Capture Channels

### JustDial

| Aspect | Detail |
|--------|--------|
| Protocol | Webhook (JustDial pushes lead data) |
| Data received | Name, phone, email, category, area, date, lead ID |
| Deduplication | By phone number within workspace |
| Auto-actions | Create contact + conversation + assign |

### Facebook Lead Ads

| Aspect | Detail |
|--------|--------|
| Protocol | Facebook Graph API (poll or webhook) |
| Data received | Name, phone, email, custom form fields |
| Auth | Facebook OAuth (page-level access) |
| Auto-actions | Create contact + conversation + assign |

### IndiaMart

| Aspect | Detail |
|--------|--------|
| Protocol | Webhook or API polling |
| Data received | Buyer name, phone, email, product, quantity, message |
| Deduplication | By phone/email within workspace |
| Auto-actions | Create contact + conversation + assign |

### Web Form / Custom Webhook

| Aspect | Detail |
|--------|--------|
| Protocol | HTTP POST to workspace webhook URL |
| Data received | Configurable field mapping |
| Auth | API key or HMAC signature |
| Spam protection | reCAPTCHA token validation, rate limiting |
| Auto-actions | Create contact + conversation + assign |

### Lead Capture Content Type

Lead capture messages appear as structured cards in the conversation thread:

```json
{
  "content_type": "lead_capture",
  "content": {
    "source": "justdial",
    "lead_id": "JD12345",
    "fields": {
      "name": "Rahul Verma",
      "phone": "+919876543210",
      "category": "Spices",
      "area": "Mumbai",
      "message": "Looking for bulk turmeric supplier"
    },
    "captured_at": "2026-03-12T10:00:00Z"
  }
}
```

---

## 6. Channel Priority & Fallback

### Per-Contact Channel Priority

Each contact has a `channel_priority` (workspace-configurable default, contact-level override):

```
Default priority: WhatsApp → Email → SMS → Voice
Contact override: Email → WhatsApp (customer prefers email)
```

### Fallback Logic

```
Agent sends message on primary channel (WhatsApp)
  → WhatsApp send fails (number not on WhatsApp)
  → System checks contact's channel_priority
  → Next channel: Email
  → Check: does contact have email handle? → YES
  → Check: is email channel connected for workspace? → YES
  → Adapt content: if original was WhatsApp interactive buttons → convert to plain text with numbered options
  → Send via email
  → Show in thread: "Sent via Email (WhatsApp unavailable)"
  → If email also fails → next channel or notify agent: "Message could not be delivered on any channel"
```

### Content Adaptation

When falling back to a different channel, content must adapt:

| Original | Fallback Channel | Adaptation |
|----------|-----------------|------------|
| WhatsApp interactive buttons | Email | Numbered list in text |
| WhatsApp interactive buttons | SMS | Numbered list, truncated |
| Image with caption | SMS | Caption only + "Image available on WhatsApp" |
| HTML email | WhatsApp | Strip HTML, plain text only |
| Voice call | WhatsApp | "We tried calling you. Please reply here." |
| Document attachment | SMS | Link to download (via File Service URL) |

---

## 7. Adding a New Channel

Steps to add a new channel (e.g., Instagram DMs):

1. **Communication Gateway**: Implement `ChannelAdapter` interface
   - `validateWebhook()`: Verify Instagram webhook signature
   - `parseWebhook()`: Extract message data from Instagram payload
   - `normalizeInbound()`: Convert to UnifiedMessage
   - `sendMessage()`: Call Instagram Graph API to send
   - `parseStatusUpdate()`: Handle delivery receipts

2. **Communication Gateway config**: Register adapter, set up webhook URL

3. **CRM Settings UI**: Add "Instagram" to channel configuration page
   - OAuth flow for Instagram Business account
   - Store credentials (encrypted)

4. **CRM changes needed**: **NONE**
   - Inbox already renders any channel's messages
   - Filters already have dynamic channel list
   - Reports already group by channel
   - Assignment rules already support channel conditions

5. **elsdk**: No changes (channel icons can be added to icon set if needed)

---

## 8. Channel Comparison Matrix

| Feature | WhatsApp | Voice | Email | Lead Capture |
|---------|----------|-------|-------|-------------|
| Real-time messaging | Yes | No (call events) | Near-real-time | One-time |
| Rich media | Yes | No | Yes (attachments) | No |
| Templates | Required (>24h) | N/A | Optional | N/A |
| Two-way | Yes | Yes (call) | Yes | No (inbound only) |
| Read receipts | Yes | N/A | No* | N/A |
| Delivery status | Full | Call status | Bounce/delivered | Received |
| Session limits | 24-hour window | N/A | None | N/A |
| Rate limits | Tier-based | Concurrent call limit | SES sending limits | Provider-specific |
| Recording | No | Yes | No | N/A |
| Cost | Per-conversation pricing | Per-minute | Per-email (SES) | Usually free |

*Email read receipts possible via pixel tracking but not recommended due to privacy.
