# Channel Configuration

> Role: Admin
> Trigger: Admin connects a new communication channel to the workspace
> Primary screen: Settings → Channels

---

## Flow Summary

Each workspace connects its own channel accounts (WhatsApp Business number, voice provider, email domain). The CRM stores channel configurations which the Communication Gateway uses to route messages.

---

## Channel Overview Page

```
Settings → Channels

┌─────────────────────────────────────────────────────────────────┐
│ Channels                                                        │
├─────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────┐                           │
│ │ WhatsApp Business API      ● Connected                       │
│ │ Phone: +91 98765 43210                                       │
│ │ WABA ID: 1234567890                                          │
│ │ Status: Active | Templates: 12 approved                      │
│ │ [Configure] [Test] [Disconnect]                              │
│ └───────────────────────────────────┘                           │
│                                                                 │
│ ┌───────────────────────────────────┐                           │
│ │ Voice (Smartflo)           ● Connected                       │
│ │ DID Numbers: +91 80 4567 8900, +91 80 4567 8901             │
│ │ Recording: Enabled                                           │
│ │ [Configure] [Test] [Disconnect]                              │
│ └───────────────────────────────────┘                           │
│                                                                 │
│ ┌───────────────────────────────────┐                           │
│ │ Email (SES)                ● Connected                       │
│ │ From: sales@clientdomain.com                                 │
│ │ Reply-To: sales@clientdomain.com                             │
│ │ [Configure] [Test] [Disconnect]                              │
│ └───────────────────────────────────┘                           │
│                                                                 │
│ ┌───────────────────────────────────┐                           │
│ │ JustDial Lead Capture      ● Active                          │
│ │ API Key: ••••••••1234                                        │
│ │ Leads this month: 47                                         │
│ │ [Configure] [Test] [Disconnect]                              │
│ └───────────────────────────────────┘                           │
│                                                                 │
│ ┌───────────────────────────────────┐                           │
│ │ Facebook Lead Ads          ○ Not Connected                   │
│ │ [Connect]                                                    │
│ └───────────────────────────────────┘                           │
│                                                                 │
│ ┌───────────────────────────────────┐                           │
│ │ IndiaMart Lead Capture     ○ Not Connected                   │
│ │ [Connect]                                                    │
│ └───────────────────────────────────┘                           │
│                                                                 │
│ ┌───────────────────────────────────┐                           │
│ │ Web Form / Live Chat       ○ Not Connected                   │
│ │ [Connect]                                                    │
│ └───────────────────────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## WhatsApp Configuration Flow

```
Admin clicks [Connect] on WhatsApp
  → Step 1: Meta Business Verification
      "Connect your Meta Business Manager account"
      → OAuth flow with Meta (Facebook Login for Business)
      → Admin grants permissions
      → System retrieves WABA ID and phone number IDs

  → Step 2: Phone Number Selection
      → Shows available phone numbers from WABA
      → Admin selects the number to use for this workspace
      → Webhook URL auto-configured: POST /webhooks/whatsapp/{workspace_id}

  → Step 3: Verify Webhook
      → System sends test message to verify webhook delivery
      → Green checkmark: "Webhook verified"

  → Step 4: Template Sync
      → System fetches approved message templates from Meta
      → Shows template list with status (approved/pending/rejected)
      → Templates available for use in conversations and workflows

  → Step 5: Test
      → Admin enters a test phone number
      → System sends a test template message
      → "Message delivered successfully" → channel connected

  → Channel card updates: ● Connected
```

### WhatsApp Settings (Post-Connection)

```
Settings → Channels → WhatsApp → Configure

  General:
    Display Name: "Climate Sales"
    Business Hours Auto-Reply: Enabled
      Message: "Thank you for contacting us. We'll get back to you shortly."
    Away Message (outside business hours): Enabled
      Message: "We're currently offline. We'll respond during business hours."

  Templates:
    [Sync Templates] — re-fetch from Meta
    List of templates with: name, category, status, body preview, last used
    Cannot edit here (templates managed in Meta Business Manager)

  Webhook:
    URL: https://api.example.com/webhooks/whatsapp/{workspace_id}
    Verify Token: ••••••••
    [Regenerate Token]

  Advanced:
    Quality Rating: Green (High)
    Messaging Limit: Tier 3 (100K/day)
    Auto-assign on first message: Yes/No
```

---

## Voice (Smartflo) Configuration Flow

```
Admin clicks [Connect] on Voice
  → Step 1: Provider Credentials
      API Key: [input]
      API Secret: [input]
      Account ID: [input]
      [Verify Credentials] → green check

  → Step 2: DID Number Assignment
      → Fetch available DID numbers from provider
      → Admin selects numbers for this workspace
      → Numbers mapped to workspace for inbound routing

  → Step 3: Call Settings
      Recording: Enable / Disable
      Max Ring Duration: 30 seconds (default)
      Voicemail: Enable / Disable
      IVR (future): Configure menu options

  → Step 4: Agent Mapping
      → Map agents to extensions or softphone endpoints
      → Ring strategy: All at once / Sequential / Round-robin

  → Step 5: Test Call
      → Admin initiates test inbound call
      → Verifies ring, answer, recording
```

---

## Email Configuration Flow

```
Admin clicks [Connect] on Email
  → Step 1: Email Provider
      ○ Amazon SES (recommended)
      ○ Custom SMTP
      ○ Gmail / Google Workspace
      ○ Microsoft 365

  → Step 2: Sending Configuration (SES example)
      AWS Region: ap-south-1
      Access Key: [input]
      Secret Key: [input]
      From Address: sales@clientdomain.com
      Reply-To: sales@clientdomain.com
      [Verify Domain] → DNS records to add (DKIM, SPF)

  → Step 3: Inbound Email
      Forward incoming emails to: crm-{workspace_id}@inbound.elcrm.com
      → Admin configures email forwarding on their domain
      → Or: direct MX record setup for a subdomain

  → Step 4: Test
      → Send test email → verify delivery
      → Receive test email → verify inbound processing
```

---

## Lead Capture Configuration

### JustDial
```
Settings → Channels → JustDial → Connect
  → API Key from JustDial CRM integration
  → Webhook URL: https://api.example.com/webhooks/justdial/{workspace_id}
  → Field mapping: JustDial fields → CRM contact fields
      name → contact_name
      mobile → phone_handle
      email → email_handle
      category → custom_field "product_interest"
      area → custom_field "location"
  → Auto-assign rule: Use workspace assignment rules (default) or specific agent
```

### Facebook Lead Ads
```
Settings → Channels → Facebook Lead Ads → Connect
  → OAuth with Facebook Business
  → Select Page and Lead Form
  → Field mapping: Facebook fields → CRM contact fields
  → Webhook auto-configured
```

### Web Form
```
Settings → Channels → Web Form → Connect
  → Generates embeddable form snippet (HTML/JS)
  → Or: webhook URL for custom forms
  → Field mapping configurable
  → Spam protection: reCAPTCHA, rate limiting
```

---

## Channel Health Monitoring

```
Each channel card shows health status:
  ● Green: Connected, last message < 5 min ago
  ● Yellow: Connected, no activity > 1 hour (check if normal)
  ● Red: Error — webhook failures, auth expired, quota exceeded
  ○ Grey: Disconnected

Admin receives alerts:
  - Channel disconnected (auth token expired)
  - Webhook delivery failures > 5 in 10 minutes
  - WhatsApp quality rating dropped
  - Voice provider connectivity issues
  - Email bounces exceeding threshold
```

---

## Data Storage

| Data | Storage Location |
|------|-----------------|
| Channel credentials (encrypted) | Communication Gateway config DB |
| Webhook URLs | Communication Gateway routing table |
| Channel status per workspace | CRM PostgreSQL: `workspace_channels` |
| WhatsApp templates | Communication Gateway (synced from Meta) |
| Email templates | CRM PostgreSQL: `message_templates` |
| Field mappings (lead capture) | CRM PostgreSQL: `crm_workspace_config` |
