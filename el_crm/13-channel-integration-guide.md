# Channel Integration Guide

> Technical API reference for all Communication Gateway channel adapters.
> Covers authentication, webhooks, payloads, rate limits, and sending for every MVP channel.
> Last verified: March 2026 (Graph API v25.0)

---

## 1. Meta Platform (Shared Infrastructure)

All 5 Meta channels (WhatsApp, Messenger, Instagram DMs, Facebook Comments, Instagram Comments) share common infrastructure.

### 1.1 Graph API Version

**Current:** v25.0 (March 2026)

**Base URL:** `https://graph.facebook.com/v25.0/`

Meta deprecates API versions ~2 years after release. Always target the latest stable version.

### 1.2 Unified OAuth & Permissions

A single Facebook Login OAuth flow grants access to all 5 Meta channels. Request these permissions during app review:

| Permission | Channels | Purpose |
|---|---|---|
| `whatsapp_business_management` | WhatsApp | Manage phone numbers, templates, account settings |
| `whatsapp_business_messaging` | WhatsApp | Send/receive messages |
| `pages_messaging` | Messenger, FB Comments (private reply) | Send/receive Messenger messages |
| `pages_manage_metadata` | All Meta webhooks | Subscribe to webhook events |
| `pages_show_list` | All Page-related | List accessible Pages |
| `pages_read_engagement` | FB/IG Comments | Read Page/IG engagement data |
| `pages_manage_ads` | FB Lead Ads | Access lead ad forms |
| `leads_retrieval` | FB Lead Ads | Read lead form submission data |
| `instagram_business_basic` | IG DMs, IG Comments | Basic IG business account access |
| `instagram_business_manage_messages` | IG DMs | Send/receive IG direct messages |
| `instagram_manage_comments` | IG Comments + private replies | Read/reply/moderate IG comments |
| `business_management` | All | Access business assets |

### 1.3 Access Tokens

| Token Type | Use | Expiry |
|---|---|---|
| **System User Token** | Production server-to-server (recommended) | Never (until revoked) |
| **Long-lived Page Token** | Page-scoped operations | Never (if from long-lived user token) |
| **User Access Token** | OAuth login flow | Short-lived → exchange for long-lived (60 days) |
| **Temporary Token** | Development/testing only | 24 hours |

**Getting a System User Token (production):**
1. Meta Business Suite → Business Settings → System Users
2. Create Admin system user
3. Add WhatsApp app + Pages as assets
4. Generate token with required permissions
5. Use as `Authorization: Bearer {TOKEN}`

### 1.4 Webhook Verification (All Meta Channels)

When configuring any Meta webhook, Meta sends a GET verification challenge:

```
GET https://your-server.com/webhook?
  hub.mode=subscribe&
  hub.verify_token=YOUR_SECRET_TOKEN&
  hub.challenge=CHALLENGE_STRING
```

**Your server must:**
1. Verify `hub.mode === 'subscribe'`
2. Verify `hub.verify_token` matches your configured secret
3. Respond HTTP 200 with `hub.challenge` as plain text body

### 1.5 Webhook Security

All Meta webhook POST payloads are signed with `X-Hub-Signature-256` header:

```
X-Hub-Signature-256: sha256=<HMAC_SHA256_HEX>
```

**Validate:** HMAC-SHA256 of request body using your App Secret. Always verify before processing.

### 1.6 Webhook Requirements

- Respond with HTTP 200 within **5 seconds** (WhatsApp) or **20 seconds** (Messenger/IG)
- Process asynchronously — acknowledge immediately, process in background
- Handle deduplication (same event can be delivered more than once)
- Meta retries failed deliveries with exponential backoff for up to **7 days** (WhatsApp) or **24 hours** (Messenger/IG)
- No dead-letter queue — lost events cannot be replayed

### 1.7 2026 Changes

- **March 31, 2026:** mTLS Certificate Authority change for WhatsApp webhooks — servers must update trust store
- **February 10, 2026:** Messenger message tags `CONFIRMED_EVENT_UPDATE`, `ACCOUNT_UPDATE`, `POST_PURCHASE_UPDATE` deprecated

---

## 2. WhatsApp Business Cloud API

### 2.1 Overview

| Aspect | Details |
|---|---|
| **Direction** | Webhook (push) for inbound; REST API for outbound |
| **Send Endpoint** | `POST /{PHONE_NUMBER_ID}/messages` |
| **Webhook Object** | `whatsapp_business_account` |
| **Webhook Field** | `messages` |
| **Identity** | Phone number (with country code, e.g., `919876543210`) |
| **24-hour Window** | Free-form messages within 24h of customer's last message; template-only outside |

### 2.2 Webhook Subscription

```
POST /{WABA_ID}/subscribed_apps
Authorization: Bearer {ACCESS_TOKEN}
```

Or configure in Meta App Dashboard → WhatsApp → Configuration.

### 2.3 Inbound Webhook Payload

**Envelope structure (all WhatsApp webhooks):**

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "WABA_ID",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "919876543210",
          "phone_number_id": "PHONE_NUMBER_ID"
        },
        "contacts": [{
          "profile": { "name": "Customer Name" },
          "wa_id": "919876543210"
        }],
        "messages": [ ... ],
        "statuses": [ ... ]
      },
      "field": "messages"
    }]
  }]
}
```

**`messages` and `statuses` are mutually exclusive** — a webhook contains one or the other.

### 2.4 Inbound Message Types

**Text:**
```json
{
  "from": "919876543210",
  "id": "wamid.ABGGFlA5Fpaf...",
  "timestamp": "1677091890",
  "type": "text",
  "text": { "body": "Hello, I'd like to place an order" }
}
```

**Image / Video / Audio / Document / Sticker:**
```json
{
  "type": "image",
  "image": {
    "caption": "Product photo",
    "mime_type": "image/jpeg",
    "sha256": "base64_hash",
    "id": "MEDIA_ID"
  }
}
```

| Type | Object | Key Fields |
|---|---|---|
| `image` | `image` | `id`, `mime_type`, `sha256`, `caption` |
| `video` | `video` | `id`, `mime_type`, `sha256`, `caption` |
| `audio` | `audio` | `id`, `mime_type`, `sha256`, `voice` (true = voice note) |
| `document` | `document` | `id`, `mime_type`, `sha256`, `filename`, `caption` |
| `sticker` | `sticker` | `id`, `mime_type`, `sha256`, `animated` |

**Location:**
```json
{
  "type": "location",
  "location": {
    "latitude": 12.971599,
    "longitude": 77.594566,
    "name": "Office",
    "address": "123 Main St, Bangalore"
  }
}
```

**Contacts:**
```json
{
  "type": "contacts",
  "contacts": [{
    "name": { "formatted_name": "John Doe", "first_name": "John", "last_name": "Doe" },
    "phones": [{ "phone": "+911234567890", "type": "CELL", "wa_id": "911234567890" }],
    "emails": [{ "email": "john@example.com", "type": "WORK" }]
  }]
}
```

**Interactive (Button Reply):**
```json
{
  "type": "interactive",
  "interactive": {
    "type": "button_reply",
    "button_reply": { "id": "confirm_yes", "title": "Yes, Confirm" }
  }
}
```

**Interactive (List Reply):**
```json
{
  "type": "interactive",
  "interactive": {
    "type": "list_reply",
    "list_reply": { "id": "row-1", "title": "Premium Package", "description": "Top tier" }
  }
}
```

**Reaction:**
```json
{
  "type": "reaction",
  "reaction": {
    "message_id": "wamid.original_id",
    "emoji": "👍"
  }
}
```

**Order (from catalog):**
```json
{
  "type": "order",
  "order": {
    "catalog_id": "CATALOG_ID",
    "text": "Please deliver tomorrow",
    "product_items": [
      { "product_retailer_id": "SKU-001", "quantity": 2, "item_price": 150.00, "currency": "INR" }
    ]
  }
}
```

**Referral (from Click-to-WhatsApp ads):**
```json
{
  "referral": {
    "source_url": "https://ad_url",
    "source_type": "ad",
    "source_id": "AD_ID",
    "headline": "Ad headline",
    "body": "Ad body",
    "ctwa_clid": "click_tracking_id"
  }
}
```

**Context (reply to specific message):**
```json
{
  "context": {
    "from": "919876543210",
    "id": "wamid.original_message_id"
  }
}
```

**Flow Completion (WhatsApp Flows):**
```json
{
  "type": "interactive",
  "interactive": {
    "type": "nfm_reply",
    "nfm_reply": {
      "response_json": "{\"screen\":\"SUMMARY\",\"quantity\":5}",
      "body": "Sent",
      "name": "flow"
    }
  }
}
```

### 2.5 Status Webhooks

```json
{
  "statuses": [{
    "id": "wamid.HBgL...",
    "status": "delivered",
    "timestamp": "1677091890",
    "recipient_id": "919876543210",
    "conversation": {
      "id": "CONVERSATION_ID",
      "origin": { "type": "business_initiated" }
    },
    "pricing": {
      "billable": true,
      "pricing_model": "CBP",
      "category": "utility"
    }
  }]
}
```

| Status | Meaning |
|---|---|
| `sent` | Delivered to WhatsApp servers |
| `delivered` | Delivered to recipient's device |
| `read` | Recipient opened/read the message (blue ticks) |
| `failed` | Delivery failed (includes `errors[]` with code, title, details) |

**Common error codes:** 131021 (not a WhatsApp user), 131026 (undeliverable), 131047 (outside 24h window), 131048 (spam rate limit), 132001 (template not found), 132012 (template paused)

### 2.6 Sending Messages

**Endpoint:** `POST https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages`

**Headers:**
```
Authorization: Bearer {ACCESS_TOKEN}
Content-Type: application/json
```

**All send requests include:** `"messaging_product": "whatsapp"`

**Text:**
```json
{
  "messaging_product": "whatsapp",
  "to": "919876543210",
  "type": "text",
  "text": { "preview_url": true, "body": "Hello! Your order is confirmed." }
}
```

**Template:**
```json
{
  "messaging_product": "whatsapp",
  "to": "919876543210",
  "type": "template",
  "template": {
    "name": "order_confirmation",
    "language": { "code": "en_US" },
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
}
```

**Image/Video/Audio/Document/Sticker:** Use `link` (URL) or `id` (uploaded media ID):
```json
{
  "messaging_product": "whatsapp",
  "to": "919876543210",
  "type": "image",
  "image": { "link": "https://example.com/photo.jpg", "caption": "Product image" }
}
```

**Interactive — Reply Buttons (max 3):**
```json
{
  "messaging_product": "whatsapp",
  "to": "919876543210",
  "type": "interactive",
  "interactive": {
    "type": "button",
    "body": { "text": "Confirm your order?" },
    "action": {
      "buttons": [
        { "type": "reply", "reply": { "id": "yes", "title": "Yes" } },
        { "type": "reply", "reply": { "id": "no", "title": "No" } }
      ]
    }
  }
}
```

**Interactive — List (max 10 sections × 10 rows):**
```json
{
  "messaging_product": "whatsapp",
  "to": "919876543210",
  "type": "interactive",
  "interactive": {
    "type": "list",
    "body": { "text": "Select a product:" },
    "action": {
      "button": "View Options",
      "sections": [{
        "title": "Products",
        "rows": [
          { "id": "sku-1", "title": "Turmeric", "description": "Premium quality" },
          { "id": "sku-2", "title": "Red Chilli", "description": "Hot variety" }
        ]
      }]
    }
  }
}
```

**Location Request (v21+):**
```json
{
  "messaging_product": "whatsapp",
  "to": "919876543210",
  "type": "interactive",
  "interactive": {
    "type": "location_request_message",
    "body": { "text": "Share your delivery location" },
    "action": { "name": "send_location" }
  }
}
```

**Reaction:**
```json
{
  "messaging_product": "whatsapp",
  "to": "919876543210",
  "type": "reaction",
  "reaction": { "message_id": "wamid.xxx", "emoji": "👍" }
}
```

**Mark as Read:**
```json
{
  "messaging_product": "whatsapp",
  "status": "read",
  "message_id": "wamid.received_message_id"
}
```

**Send Response:**
```json
{
  "messaging_product": "whatsapp",
  "contacts": [{ "input": "919876543210", "wa_id": "919876543210" }],
  "messages": [{ "id": "wamid.HBgL..." }]
}
```

### 2.7 Media API

| Operation | Method | Endpoint |
|---|---|---|
| Upload | POST | `/{PHONE_NUMBER_ID}/media` (multipart/form-data) |
| Get URL | GET | `/{MEDIA_ID}` |
| Download | GET | `{media_url}` (from Get URL response, temp ~5min) |
| Delete | DELETE | `/{MEDIA_ID}` |

**Media size limits:**

| Type | Formats | Max Size |
|---|---|---|
| Image | JPEG, PNG | 5 MB |
| Video | MP4, 3GPP | 16 MB |
| Audio | AAC, MP4, MPEG, AMR, OGG (opus) | 16 MB |
| Document | PDF, DOC(X), XLS(X), PPT(X), TXT | 100 MB |
| Sticker | WebP | 100 KB (static), 500 KB (animated) |

**Media IDs expire after 30 days.** Download and store on your own infrastructure.

### 2.8 Template Management

| Operation | Method | Endpoint |
|---|---|---|
| Create | POST | `/{WABA_ID}/message_templates` |
| List | GET | `/{WABA_ID}/message_templates` |
| Get | GET | `/{TEMPLATE_ID}` |
| Edit | POST | `/{TEMPLATE_ID}` (triggers re-review) |
| Delete | DELETE | `/{WABA_ID}/message_templates?name={name}` |

**Template categories:** `UTILITY` (lower cost), `AUTHENTICATION` (lower cost), `MARKETING` (higher cost)

**Template statuses:** `APPROVED`, `PENDING`, `REJECTED`, `PAUSED` (low quality), `DISABLED`

### 2.9 Rate Limits & Throughput

| Metric | Limit |
|---|---|
| **Send throughput (default)** | 80 messages/second per phone number |
| **Send throughput (high volume)** | Up to 1,000 MPS (auto-upgrade if 100K+ unique users/day + Green/Yellow quality) |
| **Coexistence mode** | 20 MPS (Cloud API + Business App on same number) |
| **Media upload/download** | 500 requests/phone/minute |
| **Template API** | 60 requests/hour |
| **Tier upgrade evaluation** | Every 6 hours (was 24-48h) |

**Messaging tiers (business-initiated):**

| Tier | Max Unique Customers / 24h |
|---|---|
| Unverified | 250 |
| Tier 1 | 1,000 |
| Tier 2 | 10,000 |
| Tier 3 | 100,000 |
| Tier 4 (Unlimited) | Unlimited |

**Quality rating:** Green (high) → Yellow (medium) → Red (low). Red = tier downgrade + templates paused.

### 2.10 24-Hour Messaging Window

- **Customer-initiated:** Free-form messages within 24h of customer's last message
- **Business-initiated:** Template messages only outside 24h window (each template opens new 24h window)
- **Pricing (India, 2026):** Marketing ~₹0.78, Utility ~₹0.15, Auth ~₹0.14, Service: first 1,000/month free

---

## 3. Facebook Messenger Platform

### 3.1 Overview

| Aspect | Details |
|---|---|
| **Send Endpoint** | `POST /{PAGE_ID}/messages` |
| **Webhook Object** | `page` |
| **Webhook Fields** | `messages`, `messaging_postbacks`, `messaging_optins`, `messaging_referrals`, `message_deliveries`, `message_reads`, `messaging_handovers`, `messaging_policy_enforcement` |
| **Identity** | PSID (Page-Scoped ID) — unique per user per Page |
| **24-hour Window** | Yes — promotional content allowed within window |
| **Human Agent Tag** | Extends to 7 days for human agent responses |
| **Auth** | Page Access Token |

### 3.2 Webhook Subscription

```
POST /{PAGE_ID}/subscribed_apps
?subscribed_fields=messages,messaging_postbacks,messaging_optins,messaging_referrals,message_deliveries,message_reads
&access_token={PAGE_ACCESS_TOKEN}
```

### 3.3 Inbound Webhook Payload

**Envelope:**
```json
{
  "object": "page",
  "entry": [{
    "id": "PAGE_ID",
    "time": 1458692752478,
    "messaging": [{
      "sender": { "id": "PSID" },
      "recipient": { "id": "PAGE_ID" },
      "timestamp": 1458692752478,
      "message": {
        "mid": "mid.1457764197618:41d102a3e1ae206a38",
        "text": "Hello!"
      }
    }]
  }]
}
```

**Message with attachment:**
```json
{
  "message": {
    "mid": "mid.xxx",
    "attachments": [{
      "type": "image",
      "payload": { "url": "https://scontent.xx.fbcdn.net/..." }
    }]
  }
}
```

Attachment types: `image`, `audio`, `video`, `file`, `location`, `fallback`

**Postback (button tap, menu selection):**
```json
{
  "postback": {
    "title": "Get Started",
    "payload": "GET_STARTED_PAYLOAD",
    "referral": { "ref": "REF_DATA", "source": "SHORTLINK" }
  }
}
```

**Delivery receipt:**
```json
{ "delivery": { "mids": ["mid.xxx"], "watermark": 1458668856253 } }
```

**Read receipt:**
```json
{ "read": { "watermark": 1458668856253 } }
```

### 3.4 Sending Messages

**Endpoint:** `POST https://graph.facebook.com/v25.0/{PAGE_ID}/messages`

**Text:**
```json
{
  "recipient": { "id": "PSID" },
  "messaging_type": "RESPONSE",
  "message": { "text": "Hello!" }
}
```

**Image/Video/Audio/File:**
```json
{
  "recipient": { "id": "PSID" },
  "message": {
    "attachment": {
      "type": "image",
      "payload": { "url": "https://example.com/photo.jpg", "is_reusable": true }
    }
  }
}
```

**Quick Replies (max 13):**
```json
{
  "recipient": { "id": "PSID" },
  "message": {
    "text": "How can I help?",
    "quick_replies": [
      { "content_type": "text", "title": "Track Order", "payload": "TRACK" },
      { "content_type": "text", "title": "Returns", "payload": "RETURNS" },
      { "content_type": "user_phone_number" },
      { "content_type": "user_email" }
    ]
  }
}
```

**Button Template (max 3 buttons):**
```json
{
  "recipient": { "id": "PSID" },
  "message": {
    "attachment": {
      "type": "template",
      "payload": {
        "template_type": "button",
        "text": "What do you want to do?",
        "buttons": [
          { "type": "web_url", "url": "https://example.com", "title": "Visit Website" },
          { "type": "postback", "title": "Start Chat", "payload": "START" },
          { "type": "phone_number", "title": "Call Us", "payload": "+919876543210" }
        ]
      }
    }
  }
}
```

**Generic Template / Carousel (max 10 elements):**
```json
{
  "recipient": { "id": "PSID" },
  "message": {
    "attachment": {
      "type": "template",
      "payload": {
        "template_type": "generic",
        "elements": [{
          "title": "Product Name",
          "subtitle": "Description",
          "image_url": "https://example.com/img.jpg",
          "buttons": [
            { "type": "postback", "title": "Buy", "payload": "BUY_1" }
          ]
        }]
      }
    }
  }
}
```

**Sender Actions:**
```json
{ "recipient": { "id": "PSID" }, "sender_action": "typing_on" }
```
Values: `typing_on`, `typing_off`, `mark_seen`

**`messaging_type` values:**
- `RESPONSE` — reply within 24h window (default)
- `UPDATE` — proactive message within 24h window
- `MESSAGE_TAG` — message outside 24h using approved tag

**Response:**
```json
{ "recipient_id": "PSID", "message_id": "mid.xxx" }
```

### 3.5 24-Hour Window & Message Tags

Within 24h window: send any content (including promotional).

Outside 24h: only with `HUMAN_AGENT` tag (extends to 7 days, human replies only — no bots).

**Deprecated Feb 10, 2026:** `CONFIRMED_EVENT_UPDATE`, `ACCOUNT_UPDATE`, `POST_PURCHASE_UPDATE`

```json
{
  "recipient": { "id": "PSID" },
  "message": { "text": "Following up on your inquiry..." },
  "messaging_type": "MESSAGE_TAG",
  "tag": "HUMAN_AGENT"
}
```

### 3.6 Private Reply to Page Comment

Send a one-time Messenger DM to someone who commented on your Page post:

```json
POST /{PAGE_ID}/messages
{
  "recipient": { "comment_id": "COMMENT_ID" },
  "message": { "text": "Thanks for your comment! Let me help you privately." }
}
```

**Constraints:** 1 message per comment, within 7 days, opens standard 24h Messenger window.

### 3.7 Handover Protocol

Transfer conversations between apps (bot → live agent):

| Action | Endpoint |
|---|---|
| Pass thread | `POST /me/pass_thread_control` |
| Take thread | `POST /me/take_thread_control` |
| Request thread | `POST /me/request_thread_control` |

Pass to Page Inbox (Meta Business Suite) using target app ID `263902037430900`.

### 3.8 User Profile

```
GET /{PSID}?fields=first_name,last_name,profile_pic&access_token={PAGE_TOKEN}
```

### 3.9 Rate Limits

| Operation | Limit |
|---|---|
| Text/links/reactions/stickers | 300 calls/sec per Page |
| Audio/video | 10 calls/sec per Page |
| Overall daily | 200 × number of engaged users in 24h |
| Private replies | 750 calls/hour per Page |
| Conversations API | 2 calls/sec per Page |
| High-volume threshold (FB) | 40+ messages/sec blocks inbox display |
| High-volume threshold (IG) | 72,000+ messages triggers rate limiting |

---

## 4. Instagram Messaging API (DMs)

### 4.1 Overview

| Aspect | Details |
|---|---|
| **Base URL** | `graph.instagram.com` (IG Login) or `graph.facebook.com` (FB Login) |
| **Send Endpoint** | `POST /{IG_ID}/messages` or `POST /me/messages` |
| **Webhook Object** | `instagram` |
| **Webhook Fields** | `messages`, `messaging_optins`, `messaging_postbacks`, `messaging_reactions`, `messaging_referrals`, `messaging_seen` |
| **Identity** | IGSID (Instagram-Scoped ID) — unique per user per app |
| **24-hour Window** | Yes — 7 days for human agent responses |
| **Auth** | Instagram User access token or Page Access Token |
| **Permissions** | `instagram_business_basic`, `instagram_business_manage_messages` |

### 4.2 Inbound Webhook Payload

**Text message:**
```json
{
  "object": "instagram",
  "entry": [{
    "id": "IGPRO_USER_ID",
    "time": 1700000000,
    "messaging": [{
      "sender": { "id": "IGSID" },
      "recipient": { "id": "IGPRO_USER_ID" },
      "timestamp": 1700000000000,
      "message": {
        "mid": "MESSAGE_ID",
        "text": "Hello!"
      }
    }]
  }]
}
```

**Attachment (image/video/audio/file/share):**
```json
{
  "message": {
    "mid": "MESSAGE_ID",
    "attachments": [{
      "type": "image",
      "payload": { "url": "https://cdn.fbsbx.com/..." }
    }]
  }
}
```

**Story mention:**
```json
{
  "message": {
    "mid": "MESSAGE_ID",
    "attachments": [{
      "type": "story_mention",
      "payload": { "url": "STORY_CDN_URL" }
    }]
  }
}
```

**Story reply:**
```json
{
  "message": {
    "mid": "MESSAGE_ID",
    "text": "Nice post!",
    "reply_to": {
      "story": { "url": "STORY_CDN_URL", "id": "STORY_MEDIA_ID" }
    }
  }
}
```

**Reaction:**
```json
{
  "message": {
    "mid": "MESSAGE_ID",
    "reaction": {
      "mid": "ORIGINAL_MESSAGE_ID",
      "action": "react",
      "emoji": "❤️"
    }
  }
}
```

### 4.3 Sending Messages

**Text:**
```json
{
  "recipient": { "id": "IGSID" },
  "message": { "text": "Thanks for reaching out!" }
}
```

**Image/Video/Audio:**
```json
{
  "recipient": { "id": "IGSID" },
  "message": {
    "attachment": {
      "type": "image",
      "payload": { "url": "https://example.com/image.jpg" }
    }
  }
}
```

| Type | Formats | Max Size |
|---|---|---|
| Image | PNG, JPEG | 8 MB (up to 10 per request) |
| Audio | AAC, M4A, WAV, MP4 | 25 MB |
| Video | MP4, OGG, AVI, MOV, WebM | 25 MB |
| PDF | PDF | 25 MB |

**Quick Replies (max 13):**
```json
{
  "recipient": { "id": "IGSID" },
  "message": {
    "text": "How can I help?",
    "quick_replies": [
      { "content_type": "text", "title": "Track Order", "payload": "TRACK" },
      { "content_type": "text", "title": "Talk to Agent", "payload": "AGENT" }
    ]
  }
}
```

**Heart sticker and emoji reactions** are also supported.

### 4.4 Ice Breakers

Pre-set conversation starters shown on first DM open (max 4):

```
POST /me/messenger_profile
{
  "platform": "instagram",
  "ice_breakers": [{
    "call_to_actions": [
      { "question": "What products do you offer?", "payload": "PRODUCTS" },
      { "question": "Track my order", "payload": "TRACK" }
    ]
  }]
}
```

### 4.5 Rate Limits

- **Sending messages:** 250 API calls per hour per IG professional account
- **24-hour window:** Must respond within 24h of user's last message
- **Human agent window:** 7 days (for human, non-automated replies)
- **No message tags for IG** — unlike Messenger, no way to message outside the window

### 4.6 Limitations

- No group messaging
- Messages in Requests folder inactive for 30+ days are not returned
- Cannot look up IGSID by username — only received when user messages first
- IG account must be Professional (Business or Creator) connected to a Facebook Page

---

## 5. Instagram Comments

### 5.1 Overview

| Aspect | Details |
|---|---|
| **Webhook Object** | `instagram` |
| **Webhook Fields** | `comments`, `mentions`, `live_comments` |
| **Permissions** | `instagram_manage_comments`, `pages_manage_metadata` |
| **Public Reply** | `POST /{COMMENT_ID}/replies` |
| **Private DM Reply** | `POST /{IG_ID}/messages` with `recipient.comment_id` |

### 5.2 Comment Webhook Payload

```json
{
  "object": "instagram",
  "entry": [{
    "id": "IGPRO_USER_ID",
    "time": 1520622968,
    "changes": [{
      "field": "comments",
      "value": {
        "from": { "id": "COMMENTER_IGSID", "username": "johndoe" },
        "media": { "id": "MEDIA_ID", "media_product_type": "FEED" },
        "id": "COMMENT_ID",
        "text": "Great post!",
        "timestamp": "2026-03-15T10:30:00+0000"
      }
    }]
  }]
}
```

Reply comments include `"parent_id": "PARENT_COMMENT_ID"`.

**Mention webhook** (same structure, `field: "mentions"`):
```json
{
  "field": "mentions",
  "value": {
    "comment_id": "COMMENT_ID",
    "media_id": "MEDIA_ID"
  }
}
```

### 5.3 Public Reply

```
POST /{COMMENT_ID}/replies
{ "message": "Thanks for your comment!" }
```

### 5.4 Private DM Reply

```
POST /{IG_ID}/messages
{
  "recipient": { "comment_id": "COMMENT_ID" },
  "message": { "text": "Hi! Thanks for your comment. Let me help you privately." }
}
```

**Constraints:**
- 1 private message per comment
- Must be sent within 7 days of the comment
- For IG Live: only during broadcast
- After private reply, standard 24h DM window applies if recipient responds

### 5.5 Comment Moderation

| Action | Method | Endpoint |
|---|---|---|
| Hide comment | POST | `/{COMMENT_ID}` with `{ "hide": true }` |
| Unhide | POST | `/{COMMENT_ID}` with `{ "hide": false }` |
| Delete | DELETE | `/{COMMENT_ID}` |
| Disable comments on media | POST | `/{MEDIA_ID}` with `{ "comments_enabled": false }` |

---

## 6. Facebook Page Comments

### 6.1 Overview

| Aspect | Details |
|---|---|
| **Webhook Object** | `page` |
| **Webhook Field** | `feed` (filter by `item: "comment"`) |
| **Permissions** | `pages_manage_metadata`, `pages_read_engagement`, `pages_manage_engagement`, `pages_messaging` (for private reply) |
| **Public Reply** | `POST /{POST_ID}/comments` |
| **Private Reply** | `POST /{PAGE_ID}/messages` with `recipient.comment_id` |

### 6.2 Comment Webhook Payload

```json
{
  "object": "page",
  "entry": [{
    "id": "PAGE_ID",
    "time": 1520544816,
    "changes": [{
      "field": "feed",
      "value": {
        "from": { "id": "USER_PSID", "name": "John Doe" },
        "item": "comment",
        "verb": "add",
        "comment_id": "COMMENT_ID",
        "parent_id": "POST_ID",
        "post_id": "POST_ID",
        "message": "Great post!",
        "created_time": 1520544814
      }
    }]
  }]
}
```

`verb` values: `add`, `edited`, `remove`

**Note:** The `feed` webhook also fires for posts, reactions, shares — filter by `item === "comment"`.

### 6.3 Public Reply

```
POST /{POST_ID}/comments
?message=Thanks+for+your+feedback!
&access_token={PAGE_ACCESS_TOKEN}
```

### 6.4 Private Reply (via Messenger)

```
POST /{PAGE_ID}/messages
{
  "recipient": { "comment_id": "COMMENT_ID" },
  "message": { "text": "Thanks for your comment! Let me help privately." }
}
```

**Constraints:** 1 message per comment, 7-day window, opens Messenger thread with standard 24h rules.

---

## 7. Facebook Lead Ads

### 7.1 Overview

| Aspect | Details |
|---|---|
| **Type** | Webhook (notification) + API (data fetch) — two-step |
| **Webhook Object** | `page` |
| **Webhook Field** | `leadgen` |
| **Fetch Lead** | `GET /{LEADGEN_ID}` |
| **Fetch Form Leads** | `GET /{FORM_ID}/leads` |
| **Auth** | Page Access Token (long-lived) |
| **Permissions** | `pages_manage_ads`, `leads_retrieval`, `pages_show_list`, `pages_read_engagement` |
| **Data Retention** | Leads older than 90 days may not be retrievable |

### 7.2 Webhook Payload

**Important:** The webhook does NOT contain the actual lead data (name, email, phone). It only notifies you of a new lead — you must fetch the data separately.

```json
{
  "object": "page",
  "entry": [{
    "id": "PAGE_ID",
    "time": 1700000000,
    "changes": [{
      "field": "leadgen",
      "value": {
        "ad_id": "111111111111",
        "form_id": "222222222222",
        "leadgen_id": "333333333333",
        "created_time": 1700000000,
        "page_id": "444444444444",
        "adgroup_id": "555555555555"
      }
    }]
  }]
}
```

### 7.3 Fetch Lead Data

```
GET https://graph.facebook.com/v25.0/{LEADGEN_ID}
  ?access_token={PAGE_ACCESS_TOKEN}
```

**Response:**
```json
{
  "id": "333333333333",
  "created_time": "2026-03-15T12:00:00+0000",
  "ad_id": "111111111111",
  "form_id": "222222222222",
  "field_data": [
    { "name": "full_name", "values": ["Rahul Sharma"] },
    { "name": "email", "values": ["rahul@example.com"] },
    { "name": "phone_number", "values": ["+919876543210"] },
    { "name": "city", "values": ["Mumbai"] }
  ],
  "platform": "fb",
  "is_organic": false
}
```

### 7.4 Bulk Fetch (by Form)

```
GET https://graph.facebook.com/v25.0/{FORM_ID}/leads
  ?access_token={PAGE_ACCESS_TOKEN}
  &limit=50
  &fields=id,created_time,field_data,ad_id,campaign_id,platform,is_organic
```

Supports cursor-based pagination (`before`/`after` in `paging` object).

**Filter by time:**
```
&filtering=[{"field":"time_created","operator":"GREATER_THAN","value":1700000000}]
```

### 7.5 Available Lead Fields

**Standard (pre-fill):** `full_name`, `first_name`, `last_name`, `email`, `phone_number`, `city`, `state`, `zip_code`, `country`, `company_name`, `job_title`, `work_email`, `work_phone_number`, `street_address`, `date_of_birth`, `gender`

**Custom questions** appear with the question ID as the `name` field.

**Additional:** `platform` (fb/ig), `is_organic` (paid vs organic lead form)

### 7.6 Integration Flow

```
1. User submits Lead Ad form (Facebook/Instagram)
         ↓
2. Meta sends webhook POST (contains leadgen_id only)
         ↓
3. Communication Gateway extracts leadgen_id
         ↓
4. GET /v25.0/{leadgen_id}?access_token=...
         ↓
5. Response contains field_data[] with all form fields
         ↓
6. Normalize to UnifiedMessage → publish to CRM
```

### 7.7 Rate Limits

- ~200 calls/user/hour (standard)
- Higher with Business Use Case approval
- Bulk via `/{FORM_ID}/leads` is more efficient than individual lead fetches

---

## 8. IndiaMart Lead Manager API

### 8.1 Overview

| Aspect | Details |
|---|---|
| **Type** | Pull (polling) — NO webhooks available |
| **Endpoint** | `GET https://mapi.indiamart.com/wservce/crm/crmListing/v2/` |
| **Auth** | Single API key (`glusr_crm_key`) — no OAuth |
| **Polling Interval** | Every 5-10 minutes (recommended) |
| **Pagination** | None — returns all leads since last successful call |
| **Version** | v2 (current and only supported version) |

### 8.2 Authentication

The `glusr_crm_key` (also called MCAT key or CRM key) is:
- Generated from IndiaMart seller dashboard (Lead Manager → Settings → CRM Integration)
- Tied to a specific seller account
- Has an expiration — monitor and renew proactively
- Passed as a query parameter (not header)

### 8.3 API Request

```
GET https://mapi.indiamart.com/wservce/crm/crmListing/v2/?glusr_crm_key={API_KEY}
```

**Optional parameters:**
- `start_time` — Fetch from specific time (format: `DD-Mon-YYYY HH:MM:SS`)
- `end_time` — Fetch up to specific time
- If omitted, returns leads since last successful call (server-tracked)

### 8.4 Response Structure

```json
{
  "CODE": 200,
  "STATUS": "Success",
  "MESSAGE": "Leads fetched",
  "RESPONSE": [
    {
      "UNIQUE_QUERY_ID": "12345678",
      "QUERY_TYPE": "W",
      "QUERY_TIME": "2026-03-15 10:30:00",
      "SENDER_NAME": "Rahul Sharma",
      "SENDER_MOBILE": "+91-9876543210",
      "SENDER_EMAIL": "rahul@example.com",
      "SENDER_COMPANY": "ABC Traders",
      "SENDER_CITY": "Mumbai",
      "SENDER_STATE": "Maharashtra",
      "SENDER_PINCODE": "400001",
      "SENDER_ADDRESS": "123 Main St",
      "SENDER_MOBILE_ALT": "",
      "SENDER_EMAIL_ALT": "",
      "SUBJECT": "Bulk Turmeric Inquiry",
      "QUERY_MESSAGE": "Need 500kg turmeric powder...",
      "QUERY_PRODUCT_NAME": "Turmeric Powder",
      "QUERY_MCAT_NAME": "Spices",
      "CALL_DURATION": "45",
      "RECEIVER_MOBILE": "9876543210",
      "DIRECT_TYPE": "D"
    }
  ]
}
```

### 8.5 Lead Types

| Code | Type | Description |
|---|---|---|
| `W` | Direct | Direct & ASTBUY Enquiries |
| `BL` | Buy-Leads | Buyer requirement posts |
| `P` | PNS Calls | Phone calls via IndiaMart |
| `V / BIZ` | Catalog-view | Catalog/profile view leads |
| `WA` | WhatsApp | WhatsApp enquiries via IndiaMart |

### 8.6 Error Handling

Non-200 `CODE` response indicates API key expiry or other errors. Monitor and send notifications to admin when keys expire.

### 8.7 Integration Flow

```
1. Cron job triggers every 5-10 minutes
         ↓
2. GET /crmListing/v2/?glusr_crm_key=...
         ↓
3. Parse RESPONSE array
         ↓
4. For each lead:
   - Clean phone number (strip +/- chars)
   - Deduplicate by UNIQUE_QUERY_ID
   - Normalize to UnifiedMessage
   - Publish to CRM event bus
         ↓
5. Store raw JSON for audit
```

---

## 9. JustDial Lead Manager

### 9.1 Overview

| Aspect | Details |
|---|---|
| **Type** | Webhook (push) — JustDial POSTs to your endpoint |
| **Auth** | API key in `API-KEY` parameter |
| **Content Type** | `application/x-www-form-urlencoded` or JSON (supports both GET & POST) |
| **Response** | Plain text `RECEIVED` (HTTP 200) |
| **Deduplication** | By `leadid` field |

### 9.2 Authentication

- API key generated via `registerClient` endpoint (or provided by JustDial account manager)
- Validated against stored credentials on each webhook call
- Passed as `API-KEY` parameter in the request

### 9.3 Webhook Payload

JustDial sends these fields:

| Field | Description |
|---|---|
| `leadid` | Unique lead identifier (required) |
| `leadtype` | Lead type category |
| `prefix` | Name prefix (Mr/Mrs/etc.) |
| `name` | Customer name |
| `mobile` | Primary mobile number |
| `phone` | Landline/alternate phone |
| `email` | Email address |
| `date` | Lead date |
| `time` | Lead time |
| `category` | Business category |
| `city` | Customer city |
| `area` | Customer area |
| `brancharea` | JustDial branch area |
| `dncmobile` | DNC status for mobile |
| `dncphone` | DNC status for phone |
| `company` | Company name |
| `pincode` | Customer pincode |
| `branchpin` | Branch pincode |
| `parentid` | Parent lead ID |

### 9.4 Integration Flow

```
1. JustDial POSTs to /webhook/justdial
         ↓
2. Validate API-KEY
         ↓
3. Check leadid not empty
         ↓
4. Store raw lead in audit table
         ↓
5. Normalize to UnifiedMessage:
   - Clean phone (add country code if <10 digits)
   - Build HTML message from lead fields
   - Set source = "justdial"
         ↓
6. Publish to CRM event bus
         ↓
7. Respond "RECEIVED" (200)
```

---

## 10. Smartflo (Voice / Telephony)

### 10.1 Overview

| Aspect | Details |
|---|---|
| **Provider** | Tata Communications Smartflo |
| **Base URL** | `https://api-smartflo.tatateleservices.com/v1/` |
| **CloudPhone URL** | `https://api-cloudphone.tatateleservices.com/v1/` |
| **Auth** | Token-based (login → Bearer token, ~50min expiry) |
| **Webhooks** | Push-based, configured in Smartflo dashboard |
| **Webhook Retry** | 2 attempts (30s first, 10s second) |

### 10.2 Authentication

**Login:**
```
POST https://api-smartflo.tatateleservices.com/v1/auth/login
{ "email": "...", "password": "..." }
→ { "access_token": "..." }
```

**Refresh (before 50min expiry):**
```
POST /v1/auth/refresh
Authorization: {current_token}
→ { "access_token": "new_token" }
```

### 10.3 Click-to-Call

```
POST https://api-smartflo.tatateleservices.com/v1/click_to_call
Authorization: Bearer {TOKEN}

{
  "agent_number": "9876543210",
  "destination_number": "919876543210",
  "caller_id": "919876543210",
  "async": 1,
  "call_timeout": 60,
  "custom_identifier": "crm_call_ref_123"
}
```

**Flow:** Smartflo calls agent → agent picks up → Smartflo calls customer → connected.

**Response:** `{ "call_id": "abc123..." }`

### 10.4 Call Operations

| Operation | Method | Endpoint | Key Params |
|---|---|---|---|
| Hangup | POST | `/v1/call/hangup` | `call_id` |
| Monitor | POST | `/v1/call/options` | `type: 1`, `call_id`, `agent_id` |
| Whisper | POST | `/v1/call/options` | `type: 2`, `call_id`, `agent_id` |
| Barge | POST | `/v1/call/options` | `type: 3`, `call_id`, `agent_id` |
| Transfer | POST | `/v1/call/options` | `type: 4`, `call_id`, `agent_id`, `intercom` |
| Live Calls | GET | `/v1/live_calls` | — |
| Call Records (CDR) | GET | `/v1/call/records` | `from_date`, `to_date`, `page`, `limit` |
| Add Note | POST | `/v1/call/note/{id}` | note content |
| Get Notes | GET | `/v1/call/notes/{client_number}` | — |

### 10.5 Webhook Events

Configure webhook URLs in Smartflo dashboard for each event type.

**Webhook URL pattern:** `POST /webhooks/voice/{webhook_type}/{direction}`

**Inbound call events:**

| Webhook Type | Status | Description |
|---|---|---|
| `inbound_call_received_on_server` | Incoming | Call arrived at Smartflo |
| `inbound_dialed_on_agent` | Ringing | Agent phone ringing |
| `inbound_call_answered_by_agent` | On Call | Agent picked up |
| `inbound_call_missed_by_agent` | Missed | Agent didn't answer |
| `inbound_call_hangup_answered_updated` | Ended | Call ended (was answered) |
| `inbound_call_hangup_missed_updated` | Missed | Hangup confirmation (was missed) |

**Outbound call events:**

| Webhook Type | Status | Description |
|---|---|---|
| `outbound_call_answered_by_agent` | Ringing | Agent answered, calling customer |
| `outbound_call_answered_by_customer_click_to_call` | On Call | Customer answered |
| `outbound_call_missed_by_customer_click_to_call` | Missed | Customer didn't answer |
| `outbound_call_hangup_answered_updated` | Ended | Call ended (was answered) |
| `outbound_call_hangup_missed_updated` | Missed | Hangup confirmation (was missed) |

### 10.6 Webhook Payload Fields

| Field | Description |
|---|---|
| `call_id` | Smartflo call identifier |
| `uuid` | Unique call UUID |
| `caller_id_number` | Originator phone |
| `call_to_number` | Destination phone |
| `direction` | `inbound` or `outbound` |
| `start_stamp` | Call start timestamp |
| `end_stamp` | Call end timestamp |
| `duration` | Total duration (seconds) |
| `outbound_sec` | Talk time (seconds) — preferred for duration |
| `answered_agent_number` | Agent who answered |
| `answered_agent_name` | Agent name |
| `recording_url` | Direct recording URL |
| `aws_call_recording_identifier` | S3 recording ID (append `.mp3`) |
| `call_status` | `Answered` or `Missed` |
| `custom_identifier` | Your reference ID (from click-to-call) |
| `ref_id` | Webhook match reference |

**Phone number convention:**
- Inbound: `call_to_number` = agent, `caller_id_number` = customer
- Outbound: `caller_id_number` = agent, `call_to_number` = customer

### 10.7 Agent Management

```
GET https://api-cloudphone.tatateleservices.com/v1/users?limit=1000
Authorization: Bearer {TOKEN}
```

Returns agent list with `id`, `name`, `follow_me_number`, `user_status`, `user_role`.

### 10.8 DID Numbers & IVR

```
GET /v1/my_number          → DID numbers with routing config
GET /v1/auto_attendants    → IVR menus and destinations
```

---

## 11. Email (AWS SES / SMTP)

### 11.1 Overview

Email is handled via the Communication Gateway's Email Adapter, not directly by the CRM.

| Aspect | Details |
|---|---|
| **Inbound** | SES receives → SNS notification → Email Adapter webhook |
| **Outbound** | SES SendEmail API or SMTP |
| **Auth** | AWS IAM credentials (access key + secret) |
| **Region** | `ap-south-1` (India) for lowest latency |

### 11.2 Inbound Email Flow

```
1. Customer sends email to support@workspace.example.com
         ↓
2. SES receives (MX record points to SES)
         ↓
3. SES Receipt Rule → stores in S3 + publishes to SNS
         ↓
4. SNS → HTTPS notification to Email Adapter
         ↓
5. Email Adapter parses:
   - From, To, Cc, Bcc, Subject
   - HTML body + plain text body
   - Attachments (download from S3)
   - In-Reply-To / References headers (for threading)
         ↓
6. Normalize to UnifiedMessage (contentType: "email")
         ↓
7. Publish to CRM event bus
```

### 11.3 Outbound Email

```
POST SES SendEmail API
{
  "Source": "agent@workspace.example.com",
  "Destination": {
    "ToAddresses": ["customer@example.com"],
    "CcAddresses": ["manager@example.com"]
  },
  "Message": {
    "Subject": { "Data": "Re: Your Inquiry" },
    "Body": {
      "Html": { "Data": "<html>..." },
      "Text": { "Data": "Plain text fallback" }
    }
  }
}
```

### 11.4 Limits

| Metric | SES Limit |
|---|---|
| Sending rate | 14 emails/second (default, can request increase) |
| Daily sending | 50,000 emails/day (production, after sandbox exit) |
| Message size | 10 MB (including attachments) |
| Recipients per message | 50 (To + Cc + Bcc combined) |

---

## 12. Web Forms (Custom Lead Capture)

### 12.1 Overview

| Aspect | Details |
|---|---|
| **Type** | Webhook — your web form POSTs to Communication Gateway |
| **Endpoint** | `POST /webhooks/webform` |
| **Auth** | API key or workspace token in header |
| **Format** | JSON |

### 12.2 Payload

```json
{
  "source": "website_contact_form",
  "name": "Customer Name",
  "email": "customer@example.com",
  "phone": "+919876543210",
  "message": "I'm interested in...",
  "form_id": "contact_us",
  "page_url": "https://example.com/contact",
  "utm_source": "google",
  "utm_medium": "cpc",
  "utm_campaign": "spring_2026",
  "custom_fields": {
    "company": "ABC Corp",
    "budget": "50000-100000"
  }
}
```

### 12.3 Integration

The Communication Gateway's WebForm Adapter normalizes this to a `UnifiedMessage` with `contentType: "lead_capture"` and `channel: "webform"`.

---

## 13. Cross-Channel Identity Mapping

### 13.1 Meta Channel Identity

| Channel | ID Type | Cross-Link |
|---|---|---|
| WhatsApp | Phone number | Standalone — no PSID/IGSID link |
| Messenger | PSID | Same PSID = same person in FB Comments |
| FB Comments | PSID (of commenter) | Auto-linked to Messenger identity |
| Instagram DMs | IGSID | Same IGSID = same person in IG Comments |
| IG Comments | IGSID (of commenter) | Auto-linked to IG DM identity |

**Important:** PSID ≠ IGSID. Same person on Messenger vs Instagram DM has different IDs. No cross-platform ID resolution available to third-party apps.

### 13.2 CRM Handle Resolution

The CRM resolves identity via the `contact_handles` table:

```
1. Inbound message arrives with handle_value (phone/PSID/IGSID/email)
         ↓
2. Lookup: SELECT * FROM contact_handles
   WHERE workspace_id = ? AND handle_type = ? AND handle_value = ?
         ↓
3a. Found → link to existing contact → route to existing conversation
3b. Not found → create handle → create contact → create conversation → assign agent
```

### 13.3 Conversation Threading

A conversation belongs to a **contact**, not a channel. Same customer messaging on WhatsApp and later emailing → same conversation (if handles are linked to same contact). The conversation tracks `primary_channel` and `active_channels[]`.

---

## 14. Communication Gateway Unified Webhook

All external webhooks route through a single gateway:

```
POST /webhooks/{channel_id}

Channels:
  /webhooks/whatsapp        → WhatsApp Adapter
  /webhooks/messenger       → Messenger Adapter
  /webhooks/instagram-dm    → Instagram DM Adapter
  /webhooks/instagram-comment → Instagram Comments Adapter
  /webhooks/facebook-comment → Facebook Comments Adapter
  /webhooks/facebook-lead   → Facebook Lead Ads Adapter
  /webhooks/voice           → Voice/Smartflo Adapter
  /webhooks/email           → Email Adapter (via SNS)
  /webhooks/justdial        → JustDial Adapter
  /webhooks/webform         → WebForm Adapter
```

IndiaMart uses a **poller** (not webhook) — the adapter runs on a cron schedule.

Each adapter:
1. Validates the webhook (signature, API key, etc.)
2. Parses channel-specific payload
3. Normalizes to `UnifiedMessage`
4. Publishes `comm.message.received` event to the event bus
5. CRM subscribes to this event and processes channel-agnostically

**Adding a new channel = implement adapter + register webhook. Zero CRM changes.**
