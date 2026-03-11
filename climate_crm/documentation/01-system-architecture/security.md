# Security Architecture

> Module: `climate/crm`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [JWT Authentication](#jwt-authentication)
3. [Single-Session Enforcement](#single-session-enforcement)
4. [Inactivity Timeout](#inactivity-timeout)
5. [Capability-Based Authorization](#capability-based-authorization)
6. [CORS Configuration](#cors-configuration)
7. [Input Validation](#input-validation)
8. [File Storage Security](#file-storage-security)
9. [Webhook Security](#webhook-security)
10. [Audit Trail](#audit-trail)
11. [Cross-References](#cross-references)

---

## Overview

The Climate CRM implements a layered security architecture. Authentication and authorization are handled entirely by the `PermissionCheck` hook — a single class in `application/hooks/permission_check.php` that runs on every request via two CodeIgniter hook points:

- **`pre_system`** → `preflight()`: Sets CORS headers and handles OPTIONS preflight requests
- **`post_controller_constructor`** → `CheckAccess()`: Validates JWT, enforces capabilities, checks session validity, tracks inactivity

Every controller method must declare its access level via a `@capability` DocBlock annotation. Methods without this annotation are blocked with HTTP 501.

---

## JWT Authentication

### Token Configuration

| Property | Value |
|----------|-------|
| Algorithm | HS512 (HMAC-SHA512) |
| Key Source | `$_SERVER['JWT_KEY']` environment variable |
| Expiry | 48 hours (`config_item('token_timeout')` = 48 * 60 minutes) |
| Library | `firebase/php-jwt` |

### Token Lifecycle

```
1. POST /loginctrl/verifyLogin
   ├── LoginModel validates credentials against tbl_users
   ├── Generate unique login_hash
   ├── Store login_hash in tbl_login
   └── Sign JWT payload with HS512
       │
2. Frontend stores token in localStorage['token']
       │
3. Every API request:
   ├── JwtInterceptor adds Authorization: Bearer <token>
   ├── PermissionCheck::CheckAccess() decodes JWT
   ├── Validates user exists and is Active
   ├── Checks login_hash matches tbl_login
   ├── Updates inactivity timestamp
   └── Checks @capability annotation
```

### JWT Decode in Hook

```php
// hooks/permission_check.php — inside CheckAccess()

$jwtKey = config_item('jwt_key');
if (isset($headers['Authorization']) && $return['status'] === 200) {
    $token = $headers['Authorization'];
    try {
        $token = str_replace("Bearer ", "", $token);
        $decoded = JWT::decode($token, new Key($jwtKey, 'HS512'));
        $AuthData = json_decode(Risposta::json_encode($decoded), true);
        $AuthData['real'] = array('user_type' => $AuthData['user_type']);
        $CI->AuthData = $AuthData;
    } catch (Exception $e) {
        log_message('error', __FILE__ . ' ' . __LINE__ . ' ' . $e->getMessage());
        $return = array("status" => 400, 'error' => "Bad Request");
    }
}
```

### JWT Payload Structure

```json
{
  "user_id": 1,
  "user_name": "Admin User",
  "user_type": "admin",
  "login_as": "admin",
  "role_id": 9,
  "capabilities": {
    "customers": ["default", "view", "edit"],
    "orders": ["create", "edit", "view"],
    "contacts": ["view_assignment_history"]
  },
  "login_hash": "a1b2c3d4e5f6g7h8i9j0",
  "is_super": "No",
  "account_id": null,
  "exp": 1717123456
}
```

---

## Single-Session Enforcement

Each login generates a unique `login_hash` stored in both the JWT payload and `tbl_login` table. Every request validates the hash — if a user logs in on another device, the old session's hash no longer matches.

```php
// hooks/permission_check.php — single-session check

$login_hash = $AuthData['login_hash'];
$query = $db->select("login_id")->from("tbl_login")
    ->where("login_hash", $login_hash)
    ->where("user_id", $AuthData['user_id'])->get();

if (!$query->num_rows()) {
    $return = array("status" => 400, "error" => "Session Change");
}
```

The frontend `ErrorInterceptor` catches this and shows:

```typescript
if (err.statusText == 'Session Change') {
    this.snackBar.open(
        "Your session has been terminated as you have changed credentials in another device.",
        "Ok Noted", { duration: 30000 }
    );
}
localStorage.clear();
this.route.navigate(['/sessions/signin']);
```

---

## Inactivity Timeout

### Backend Tracking

The hook records the last API request time per user and compares against the configurable timeout:

```php
// hooks/permission_check.php — inactivity check

$last_request_time = $this->getLastRequestTime($db, $AuthData['user_id']);
$this->updateRequestTime($db, $AuthData['user_id']);

if ($last_request_time) {
    $current_time = date("Y-m-d H:i:s");
    $time_diff = strtotime($current_time) - strtotime($last_request_time);
    $inactive_time = $db->select("setting_val")->from("tbl_settings")
        ->where("setting_name", "inactivity_setting")->get()->row_array();

    if ($time_diff > ($inactive_time['setting_val'] * 60)) {
        $return = array(
            "status" => 400,
            "error" => "Session expired due to inactivity for more than {$inactive_time['setting_val']} minutes"
        );
    }
}
```

**Tables involved:**
- `tbl_user_last_request_log` — `user_id`, `request_time`
- `tbl_settings` — `setting_name = 'inactivity_setting'`, value in minutes

### Request Time Tracking Methods

```php
// hooks/permission_check.php

public function insertRequestTime($db, $userId) {
    $db->insert("tbl_user_last_request_log", [
        "user_id" => $userId,
        "request_time" => date("Y-m-d H:i:s")
    ]);
}

public function updateRequestTime($db, $userId) {
    $db->where("user_id", $userId)->update("tbl_user_last_request_log", [
        "request_time" => date("Y-m-d H:i:s")
    ]);
}

public function getLastRequestTime($db, $userId) {
    $db->select("request_time")->from("tbl_user_last_request_log")->where("user_id", $userId);
    $query = $db->get();
    if ($query->num_rows()) {
        return $query->row_array()['request_time'];
    }
    return false;
}
```

### Frontend Cross-Tab Sync

The `ErrorInterceptor` updates `localStorage['lastActivityTime']` on every successful API call, which syncs across all browser tabs:

```typescript
// climate-admin/src/app/shared/helpers/error.interceptor.ts

tap(() => {
    if (localStorage.getItem('currentUserDetails')) {
        localStorage.setItem(this.LAST_ACTIVITY_KEY, Date.now().toString());
    }
}),
```

---

## Capability-Based Authorization

### How It Works

Every controller method declares its required capability via a PHP DocBlock `@capability` annotation. The `PermissionCheck` hook uses PHP Reflection to extract and validate it.

### Annotation Extraction

```php
// hooks/permission_check.php — annotation parsing

$class = $CI->router->class;
$method = $CI->router->method;
$rc = new ReflectionClass($class);
$rc_method = $rc->getMethod($method);
$doc_comment = $rc_method->getDocComment();
$access_line = preg_match("/\*\s*@capability\s+([\w_\.\-\s]*)/", $doc_comment, $matches);

if ($access_line) {
    $access = trim(preg_replace("/\s+/", " ", $matches[1]));
    $access_array = explode(" ", $access);
}
```

### Resolution Order

```php
// hooks/permission_check.php — capability resolution

// 1. @capability public → skip all auth
if (in_array('public', $access_array)) {
    $return = array("status" => 200, 'error' => "");
}
// 2. @capability authenticated/user → any valid JWT
elseif (count(array_intersect(['authenticated', 'user'], $access_array))) {
    $return = array("status" => 200, 'error' => "");
}
// 3. Super admin → bypass all checks
elseif ($AuthData['is_super'] == "Yes") {
    $return = array("status" => 200, 'error' => "");
}
// 4. Check specific capability: "module.action"
elseif (!empty($access_array)) {
    foreach ($access_array as $access) {
        $parts = explode(".", $access);
        if (count($parts) == 2
            && isset($AuthData['capabilities'][$parts[0]])
            && in_array($parts[1], $AuthData['capabilities'][$parts[0]])) {
            $return = array("status" => 200, 'error' => "");
            break;
        }
        $return = array("status" => 403, 'error' => 'Forbidden');
    }
}
```

### Annotation Types

| Annotation | Meaning | Example |
|------------|---------|---------|
| `@capability public` | No auth required | Login, webhooks, password reset |
| `@capability authenticated` | Any valid JWT | Profile endpoints |
| `@capability user` | Same as authenticated | Legacy alias |
| `@capability module.action` | Specific permission | `orders.create`, `customers.edit` |
| Multiple capabilities | OR logic — any one matches | `@capability orders.view orders.create` |

### Frontend Permission Pipe

Angular templates use the `hasPermission` pipe to show/hide UI elements based on the user's JWT capabilities:

```html
<!-- Only visible if user has orders.create capability -->
<button *ngIf="'orders.create' | hasPermission" mat-raised-button>
  Create Order
</button>
```

### Role Hierarchy

| Role | ID | Capabilities | Dashboard |
|------|----|-------------|-----------|
| Super Admin | — | All (bypass via `is_super == "Yes"`) | `/dashboard` |
| Sales Admin | 9 | Team management, all reports, full CRM | `/admindashboard` |
| Sales Agent | 4 | Own conversations, orders, basic reports | `/agentdashboard` |
| Standard | varies | Per-role configuration via `tbl_role_capability` | `/dashboard` |
| Customer | — | Limited portal access (separate layout) | Customer portal |

### Database Tables

| Table | Purpose |
|-------|---------|
| `tbl_capability` | Permission definitions: `module_name`, `capability`, `capability_title` |
| `tbl_roles` | Role definitions: `role_name`, `role_description` |
| `tbl_role_capability` | Many-to-many: `role_id` → `capability_id` |
| `tbl_user_roles` | User role assignments: `user_id` → `role_id` |
| `tbl_menu` | Menu items linked to capabilities for sidebar visibility |

---

## CORS Configuration

The `preflight()` method fires as a `pre_system` hook before any controller loads:

```php
// hooks/permission_check.php — preflight()

public function preflight() {
    date_default_timezone_set("Asia/Kolkata");
    $http_origin = isset($_SERVER['HTTP_ORIGIN'])
        ? $_SERVER['HTTP_ORIGIN']
        : 'https://d1rymkbr2tz0j7.cloudfront.net';

    header("Access-Control-Allow-Origin: {$http_origin}");
    header("Access-Control-Allow-Credentials: true");
    header("Access-Control-Allow-Methods: GET,POST,OPTIONS");
    header("Access-Control-Allow-Headers: Authorization, Access-Control-Allow-Headers, "
         . "Origin, Accept, X-Requested-With, Content-Type, "
         . "Access-Control-Request-Method, Access-Control-Request-Headers, "
         . "User-Type, Referer, User-Agent, CompanyId, InAs, "
         . "companyid, inas, web-version, app-version");
    header('P3P: CP="CAO PSA OUR"');

    if ('OPTIONS' == ($_SERVER['REQUEST_METHOD'] ?? '')) {
        die();  // Return 200 with headers only for preflight
    }
}
```

**Key behavior:**
- Origin is set dynamically from `$_SERVER['HTTP_ORIGIN']`, falling back to the CloudFront CDN URL
- Credentials enabled (`true`) for cookie and header-based authentication
- OPTIONS requests terminate immediately after setting headers (preflight response)

---

## Input Validation

### Server-Side

| Validation | Implementation |
|------------|----------------|
| GST Number | Uniqueness check across `temp_tbl_accounts` before insert |
| Phone Numbers | Normalized to 10-digit via `PhoneNumberHelper` (strip +91, leading 0, spaces) |
| Email | Format validation via `handle_validation_helper.php` |
| Handle Uniqueness | Unique constraint on `(handle_type, handle_value)` in `temp_tbl_contact_handles` |
| Required Fields | Validated in controller methods before model operations |
| JSON Input | Parsed via `json_decode($this->input->raw_input_stream, true)` |

### Phone Number Normalization

```
Input              → Normalized
+919876543210      → 9876543210
919876543210       → 9876543210
09876543210        → 9876543210
9876543210         → 9876543210
+91 98765 43210    → 9876543210
```

All phone lookups in `temp_tbl_contact_handles` use the normalized 10-digit format, preventing duplicate contacts from format variations.

---

## File Storage Security

- **No local file storage** — all media, invoices, and documents stored on AWS S3
- **Pre-signed URLs** — private files accessed via time-limited pre-signed S3 URLs
- **CloudFront CDN** — public assets served via `https://d1r95e2xq05b34.cloudfront.net/{media_key}`
- **S3 credentials** — stored in environment variables (`$_SERVER['S3_KEY']`, `$_SERVER['S3_TOKEN']`, `$_SERVER['S3_BUCKET']`), never in code

---

## Webhook Security

### WhatsApp Cloud API

Verification via shared secret token:

```php
// Whatsapp::webhookCloudApi() — GET request verification
// hub.verify_token must match 'climate'
// Returns hub.challenge to confirm subscription
```

### JustDial

API key authentication via `tbl_api_auth`:

```php
// Justdial::receiveLead()
// API-KEY parameter validated against tbl_api_auth
// Credentials generated via Justdial::registerClient()
```

### Facebook Lead Ads

HMAC-SHA256 webhook signature verification.

### External API

`X-API-KEY` header validated against `tbl_justdial_credentials`:

```php
// ExternalApi endpoints
// X-API-KEY header → validate against tbl_justdial_credentials WHERE active = 1
```

---

## Audit Trail

### Assignment History

Every contact assignment event is recorded in `tbl_contact_assignment_history`:

| Field | Description |
|-------|-------------|
| `contact_id` | Target contact |
| `assigned_to_user_id` | New agent |
| `previous_user_id` | Previous agent (null for initial) |
| `assignment_type` | `initial`, `transfer`, `reassignment`, `round_robin`, `contact_merged` |
| `assignment_method` | `manual`, `automatic`, `round_robin`, `system` |
| `transfer_reason` | Agent-provided reason for transfers |
| `source_system` | `open_conversations`, `offline_sync`, etc. |
| `backfill_confidence` | `high`, `medium`, `low` (for historical backfills) |
| `assigned_at` | Timestamp |

### Account Merge Audit

Merge operations logged in `tbl_account_merge_requests_logs`:
- Merge request initiation and approval/rejection
- All data transfers (contacts, conversations, orders)
- Source and target account IDs

### Webhook Audit

All incoming webhook payloads stored raw before processing:
- `tbl_whatsapp_callback` — WhatsApp webhook JSON
- `tbl_justdial_leads` — JustDial lead data
- `tbl_facebook_leads` — Facebook lead data

### Order Status History

Every order status transition logged in `tbl_order_status_logs`:
- Old status, new status, changed by user, timestamp, notes

---

## Cross-References

| Document | Path |
|----------|------|
| Authentication API | `docs/05-api-documentation/authentication.md` |
| Backend Architecture | `docs/01-system-architecture/backend-architecture.md` |
| Frontend Architecture | `docs/01-system-architecture/frontend-architecture.md` |
| Configuration Tables | `docs/03-database-design/configuration-tables.md` |
| Assignment Management | `docs/04-core-modules/assignment-management.md` |
| Webhook Flow | `docs/06-data-flow/webhook-flow.md` |
