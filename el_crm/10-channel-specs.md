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
    ├── Messenger Adapter ←→ Meta Graph API (Messenger Platform)
    ├── Instagram DM Adapter ←→ Meta Graph API (IG Messaging)
    ├── Facebook Comments Adapter ←→ Meta Graph API (Webhooks)
    ├── Instagram Comments Adapter ←→ Meta Graph API (Webhooks)
    ├── Voice Adapter ←→ Smartflo / SIP Provider
    ├── Email Adapter ←→ SES / SMTP
    ├── JustDial Adapter ←→ JustDial API
    ├── Facebook Lead Ads Adapter ←→ Facebook Lead Ads API
    ├── IndiaMart Adapter ←→ IndiaMart API
    ├── WebForm Adapter ←→ Webhook receiver
    └── [Future adapters: SMS, Telegram, LINE, LiveChat]
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

## 5. Facebook Messenger

> MVP Core Channel — direct messaging via Meta Messenger Platform

### Capabilities

| Feature | Supported |
|---------|-----------|
| Text messages | Yes |
| Images (JPEG, PNG, GIF) | Yes |
| Videos | Yes |
| Files / documents | Yes (up to 25MB) |
| Audio | Yes |
| Quick reply buttons (up to 13) | Yes |
| Generic templates (cards with image, title, buttons) | Yes |
| Button templates (text + up to 3 buttons) | Yes |
| Persistent menu | Yes (configurable) |
| Typing indicators | Yes (send + receive) |
| Read receipts | Yes |
| Sender actions (mark seen, typing on/off) | Yes |
| Get started button | Yes |
| Ice breakers | Yes |
| Handover protocol (bot → human) | Yes |

### Messaging Rules

```
Messaging Window:
  - Standard messaging: 24-hour window after last customer message
  - After 24h: must use Message Tags (limited use cases) or Sponsored Messages (paid)
  - Human Agent tag: 7-day window for human agent responses (applies to el-CRM)

Message Tags (allowed outside 24h window):
  - CONFIRMED_EVENT_UPDATE
  - POST_PURCHASE_UPDATE
  - ACCOUNT_UPDATE
  - HUMAN_AGENT (7-day window — primary tag for CRM use)

Rate Limits:
  - 250 messages per second per page
  - Sending limit tiers based on page quality and history
```

### Integration (Meta Graph API)

```
Auth: Facebook Page OAuth (Page Access Token)
  - Permissions: pages_messaging, pages_manage_metadata, pages_read_engagement
  - Long-lived page token stored encrypted per workspace

Webhook Events (subscribed):
  - messages: incoming text, attachments, quick replies
  - messaging_postbacks: button clicks, get started
  - messaging_referrals: m.me links, ads
  - message_deliveries: delivery receipts
  - message_reads: read receipts
  - messaging_handovers: handover protocol events

Send API:
  POST https://graph.facebook.com/v21.0/me/messages
  {
    "recipient": { "id": "<PSID>" },
    "message": { "text": "Hello!" }
  }
```

### Handle Type

```
handle_type: "facebook_psid"
handle_value: "Page-Scoped User ID (PSID)"

Note: PSID is unique per page. Same user on different pages = different PSIDs.
Contact resolution: match PSID to existing contact, or create new.
If user has also messaged on WhatsApp (phone match), contacts are merged.
```

### Content Type Mapping

| CRM content_type | Messenger Content |
|------------------|-------------------|
| text | Text message |
| image | Image attachment |
| video | Video attachment |
| document | File attachment |
| audio | Audio attachment |
| interactive | Quick replies, button templates, generic templates |
| postback | Button click / Get Started response |

### Configuration Required

```json
{
  "provider": "meta_messenger",
  "page_id": "123456789",
  "page_name": "Climate Naturals",
  "page_access_token": "(encrypted)",
  "app_id": "987654321",
  "app_secret": "(encrypted)",
  "webhook_verify_token": "(encrypted)",
  "get_started_payload": "GET_STARTED",
  "persistent_menu": [
    { "type": "postback", "title": "Talk to Sales", "payload": "SALES" },
    { "type": "postback", "title": "Check Order Status", "payload": "ORDER_STATUS" },
    { "type": "web_url", "title": "Visit Website", "url": "https://climatenaturals.com" }
  ]
}
```

---

## 6. Instagram DMs

> MVP Core Channel — direct messaging via Instagram Messaging API

### Capabilities

| Feature | Supported |
|---------|-----------|
| Text messages | Yes |
| Images (JPEG, PNG) | Yes |
| Videos | Yes (reels sharing) |
| Story replies | Yes (receive story reply as message) |
| Story mentions | Yes (receive @mention notification) |
| Quick reply buttons | Yes |
| Generic templates | Yes (cards with image + buttons) |
| Ice breakers | Yes |
| Read receipts | Yes |
| Typing indicators | Receive only |
| Audio | No (not yet supported by API) |
| Documents | No (not supported by IG) |

### Messaging Rules

```
Messaging Window:
  - 24-hour window after last customer message (same as Messenger)
  - Human Agent tag: 7-day window for human agent responses
  - Outside window: cannot send proactive messages (unlike WhatsApp templates)

Rate Limits:
  - Same as Messenger (250/sec per account)
  - Instagram-specific: may have lower limits for new accounts
```

### Integration (Meta Graph API)

```
Auth: Same Facebook OAuth (Instagram Business Account linked to Facebook Page)
  - Permissions: instagram_manage_messages, instagram_basic, pages_manage_metadata
  - Requires Instagram Business or Creator account connected to Facebook Page

Webhook Events:
  - messages: incoming text, media, story replies, story mentions
  - messaging_postbacks: ice breaker selections
  - message_deliveries: delivery receipts
  - message_reads: read receipts

Send API:
  POST https://graph.facebook.com/v21.0/me/messages
  {
    "recipient": { "id": "<IGSID>" },
    "message": { "text": "Thanks for reaching out!" }
  }
```

### Handle Type

```
handle_type: "instagram_id"
handle_value: "Instagram-Scoped User ID (IGSID)"

Note: IGSID is different from PSID (Messenger). Same person on IG and Messenger = different IDs.
Cross-channel identity: if user provides phone/email in conversation, agent can manually link contacts.
```

### Story Interactions

```
Customer replies to Instagram Story → appears as message in CRM Inbox
  - content_type: "story_reply"
  - content: { story_url: "...", reply_text: "Love this!" }
  - Displayed in chat thread with story preview thumbnail

Customer mentions business in their Story → notification in CRM
  - content_type: "story_mention"
  - content: { story_url: "...", mentioned_by: "username" }
  - Creates conversation if none exists, or adds to existing
```

### Configuration Required

```json
{
  "provider": "meta_instagram",
  "instagram_account_id": "17841400123456",
  "instagram_username": "climatenaturals",
  "page_id": "123456789",
  "page_access_token": "(encrypted)",
  "app_id": "987654321",
  "app_secret": "(encrypted)",
  "ice_breakers": [
    { "question": "I want to place an order", "payload": "ORDER" },
    { "question": "I need help with my order", "payload": "SUPPORT" },
    { "question": "Tell me about your products", "payload": "PRODUCTS" }
  ]
}
```

---

## 7. Facebook Comments

> MVP Core Channel — monitor and reply to comments on Facebook Page posts

### Capabilities

| Feature | Supported |
|---------|-----------|
| Receive comments on page posts | Yes |
| Reply to comments (public) | Yes |
| Reply via private message (Messenger) | Yes |
| Comment reactions | Receive only |
| Nested replies (threads) | Yes |
| Hide/delete comments | Yes (moderation) |
| Filter by keyword/sentiment | Future |

### How It Works

```
Customer comments on Facebook Page post
  → Meta Webhook: feed event (type: "comment")
  → Communication Gateway receives
  → Normalizes to UnifiedMessage:
    - channel: "facebook_comments"
    - content_type: "social_comment"
    - content: {
        post_id: "page_post_12345",
        post_text: "Check out our new spice range...",
        post_url: "https://facebook.com/...",
        comment_id: "comment_67890",
        comment_text: "What's the price for turmeric?",
        parent_comment_id: null,  // null = top-level, set for replies
        commenter_name: "Rahul Verma",
        commenter_id: "PSID_12345"
      }

CRM Inbox display:
  - Shows as conversation with the commenter
  - Thread shows the original post (as context) + comment chain
  - Agent can:
    a. Reply publicly (posts reply comment on Facebook)
    b. Reply privately (switches to Messenger DM with that person)
    c. Hide comment (moderation — hides from public view)
```

### Conversation Threading for Comments

```
Each post creates a "comment thread" in CRM:
  - One conversation per commenter per post (not one per comment)
  - If same person comments on multiple posts → separate conversations
  - Agent replies are threaded as replies to the specific comment

Cross-channel linking:
  - If agent clicks "Reply Privately" → new Messenger conversation
  - Both conversations linked to same contact (via PSID)
  - Contact card shows both Facebook Comments and Messenger interactions
```

### Handle Type

```
handle_type: "facebook_psid"
handle_value: "PSID_12345" (same PSID as Messenger — same user!)

Key advantage: Facebook comments use the same PSID as Messenger.
If someone comments on a post AND messages on Messenger → same contact.
```

### Configuration Required

```json
{
  "provider": "meta_fb_comments",
  "page_id": "123456789",
  "page_access_token": "(encrypted)",
  "monitored_post_types": ["all"],
  "auto_hide_spam": false,
  "keywords_alert": ["price", "order", "buy", "contact"]
}
```

Note: Uses the same Page Access Token as Messenger — single OAuth flow covers both.

---

## 8. Instagram Comments

> MVP Core Channel — monitor and reply to comments on Instagram posts/reels

### Capabilities

| Feature | Supported |
|---------|-----------|
| Receive comments on posts | Yes |
| Receive comments on reels | Yes |
| Reply to comments (public) | Yes |
| Reply via DM (Instagram DM) | Yes |
| Comment reactions | No (not via API) |
| Nested replies (threads) | Yes |
| Hide/delete comments | Yes (moderation) |

### How It Works

```
Customer comments on Instagram post/reel
  → Meta Webhook: comments event
  → Communication Gateway receives
  → Normalizes to UnifiedMessage:
    - channel: "instagram_comments"
    - content_type: "social_comment"
    - content: {
        media_id: "ig_media_12345",
        media_type: "IMAGE" | "VIDEO" | "CAROUSEL_ALBUM" | "REEL",
        media_url: "https://instagram.com/p/...",
        media_caption: "Check out our new spice range...",
        comment_id: "ig_comment_67890",
        comment_text: "Looks amazing! How do I order?",
        parent_comment_id: null,
        commenter_username: "rahul_verma",
        commenter_id: "IGSID_12345"
      }

CRM Inbox display:
  - Shows as conversation with the commenter
  - Thread shows: post image/thumbnail + caption (context) + comment chain
  - Agent can:
    a. Reply publicly (posts reply comment on Instagram)
    b. Reply via DM (switches to Instagram DM)
    c. Delete comment (moderation)
```

### Conversation Threading for Comments

```
Same model as Facebook Comments:
  - One conversation per commenter per post/reel
  - Cross-channel: if agent clicks "Reply via DM" → Instagram DM conversation
  - Both linked to same contact (via IGSID)

Important difference from Facebook:
  - Instagram IGSID ≠ Facebook PSID
  - Same person on Instagram comments and Facebook comments = different contacts
  - Must be manually linked (or matched by phone/email if provided)
```

### Handle Type

```
handle_type: "instagram_id"
handle_value: "IGSID_12345" (same as Instagram DMs — same user!)

Instagram comments + Instagram DMs share the same IGSID.
If someone comments AND DMs → same contact, merged conversations.
```

### Configuration Required

```json
{
  "provider": "meta_ig_comments",
  "instagram_account_id": "17841400123456",
  "page_id": "123456789",
  "page_access_token": "(encrypted)",
  "monitored_media_types": ["IMAGE", "VIDEO", "CAROUSEL_ALBUM", "REEL"],
  "auto_hide_spam": false
}
```

Note: Uses same token as Instagram DMs — single OAuth flow.

---

## 9. Meta Unified OAuth

Since WhatsApp, Messenger, Instagram DMs, Facebook Comments, and Instagram Comments all use Meta APIs, a single OAuth flow can authorize all channels:

```
Settings → Channels → Connect Meta Channels
  → OAuth: "Log in with Facebook"
  → Permissions requested:
      whatsapp_business_messaging    (WhatsApp)
      pages_messaging                (Messenger)
      instagram_manage_messages      (Instagram DMs)
      pages_manage_metadata          (Facebook Comments)
      instagram_basic                (Instagram Comments)
      pages_read_engagement          (Comments monitoring)
  → User selects Facebook Page + Instagram Account
  → System stores single page_access_token
  → Enables all 5 Meta channels simultaneously

Channel toggle (workspace can enable/disable each independently):
  ☑ WhatsApp Business
  ☑ Facebook Messenger
  ☑ Instagram DMs
  ☑ Facebook Comments
  ☑ Instagram Comments
```

### Cross-Channel Identity (Meta)

```
Meta provides different user IDs per channel:
  - Messenger: PSID (Page-Scoped ID)
  - Facebook Comments: PSID (same as Messenger!)
  - Instagram DMs: IGSID (Instagram-Scoped ID)
  - Instagram Comments: IGSID (same as DMs!)
  - WhatsApp: Phone number

Auto-linking:
  - Messenger PSID = Facebook Comments PSID → automatic same contact
  - Instagram DM IGSID = Instagram Comments IGSID → automatic same contact
  - WhatsApp phone ≠ PSID ≠ IGSID → separate contacts until manually linked
  - Agent can manually link contacts (or system links if customer provides phone/email)
```

---

## 10. Lead Capture Channels

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

## 11. Channel Priority & Fallback

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

## 12. Adding a New Channel

Steps to add a new channel (e.g., Telegram):

1. **Communication Gateway**: Implement `ChannelAdapter` interface
   - `validateWebhook()`: Verify webhook signature
   - `parseWebhook()`: Extract message data from provider payload
   - `normalizeInbound()`: Convert to UnifiedMessage
   - `sendMessage()`: Call provider API to send
   - `parseStatusUpdate()`: Handle delivery receipts

2. **Communication Gateway config**: Register adapter, set up webhook URL

3. **CRM Settings UI**: Add channel to configuration page
   - OAuth or API key flow for provider
   - Store credentials (encrypted)

4. **CRM changes needed**: **NONE**
   - Inbox already renders any channel's messages
   - Filters already have dynamic channel list
   - Reports already group by channel
   - Assignment rules already support channel conditions

5. **elsdk**: No changes (channel icons can be added to icon set if needed)

---

## 13. Channel Comparison Matrix

| Feature | WhatsApp | Messenger | IG DMs | FB Comments | IG Comments | Voice | Email | Lead Capture |
|---------|----------|-----------|--------|-------------|-------------|-------|-------|-------------|
| Real-time messaging | Yes | Yes | Yes | Yes | Yes | No (events) | Near-RT | One-time |
| Rich media | Yes | Yes | Yes (limited) | No | No | No | Yes | No |
| Templates/buttons | Yes | Yes | Yes | N/A | N/A | N/A | Optional | N/A |
| Two-way | Yes | Yes | Yes | Yes (public) | Yes (public) | Yes | Yes | No |
| Read receipts | Yes | Yes | Yes | N/A | N/A | N/A | No* | N/A |
| Delivery status | Full | Full | Full | Immediate | Immediate | Call status | Bounce/dlvd | Received |
| Session limits | 24h window | 24h (+7d agent) | 24h (+7d agent) | None | None | N/A | None | N/A |
| Private reply | N/A | N/A | N/A | Yes (→Messenger) | Yes (→IG DM) | N/A | N/A | N/A |
| Rate limits | Tier-based | 250/sec | 250/sec | API limits | API limits | Concurrent | SES limits | Provider |
| Recording | No | No | No | No | No | Yes | No | N/A |
| Cost | Per-conversation | Free | Free | Free | Free | Per-minute | Per-email | Free |
| Auth | Cloud API key | Page OAuth | Page OAuth | Page OAuth | Page OAuth | PBX | SES/SMTP | Webhook |
| Cross-channel ID | Phone | PSID | IGSID | PSID | IGSID | Phone | Email | Varies |

*Email read receipts possible via pixel tracking but not recommended due to privacy.

**Meta channel identity sharing:**
- Messenger PSID = Facebook Comments PSID (auto-linked)
- Instagram DM IGSID = Instagram Comments IGSID (auto-linked)
- WhatsApp phone is separate from PSID/IGSID (manual link needed)
