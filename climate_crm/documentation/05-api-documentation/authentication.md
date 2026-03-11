# Authentication — API Endpoints

> Module: `climate/crm`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication Flow](#authentication-flow)
3. [POST /loginctrl/verifyLogin](#post-loginctrlverifylogin)
4. [POST /loginctrl/verifyOTP](#post-loginctrlverifyotp)
5. [POST /loginctrl/signup](#post-loginctrlsignup)
6. [POST /loginctrl/registerCustomer](#post-loginctrlregistercustomer)
7. [POST /loginctrl/forgotPassword](#post-loginctrlforgotpassword)
8. [POST /loginctrl/checkResetPassword](#post-loginctrlcheckresetpassword)
9. [POST /loginctrl/resetPassword](#post-loginctrlresetpassword)
10. [POST /loginctrl/resetNewPassword](#post-loginctrlresetnewpassword)
11. [Session Management](#session-management)
12. [Permission Hook](#permission-hook)
13. [Error Codes](#error-codes)
14. [Cross-References](#cross-references)

---

## Overview

The CRM uses **JWT (JSON Web Token)** authentication with the **HS512** algorithm. All authentication endpoints (login, registration, password reset) are public — they are tagged with `@capability public` in the controller, which causes the `PermissionCheck` hook to skip authorization.

All other endpoints require a valid JWT in the `Authorization` header. The hook validates the token, enforces capability-based access, checks for single-session violations, and tracks inactivity.

### Base URL

```
Production:  https://api.climatenaturals.com/index.php
Development: http://climate.loc/index.php
```

### Required Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes (except `@capability public`) | `Bearer <JWT_TOKEN>` |
| `Content-Type` | Yes | `application/json` |
| `User-Type` | Yes | `admin` or `customer` |
| `CompanyId` | Yes | Company ID for multi-company support |
| `InAs` | No | Impersonation — admin acting as another user |
| `web-version` | No | Frontend app version string |

### JWT Interceptor (Frontend)

The Angular `JwtInterceptor` automatically attaches the token and headers to every API request:

```typescript
// climate-admin/src/app/shared/helpers/jwt.interceptor.ts

@Injectable()
export class JwtInterceptor implements HttpInterceptor {
    intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        if (request.url.includes('.json')) {
            return next.handle(request);
        }
        let currentUser: any = localStorage.getItem('currentUserDetails') ?? '{}';
        currentUser = currentUser && currentUser != "undefined" ? JSON.parse(currentUser) : false;
        let company: any = localStorage.getItem('companyDts') ?? '{}';
        company = company && company != "undefined" ? JSON.parse(company) : false;
        if (currentUser && localStorage['token']) {
            const headers: any = { Authorization: `Bearer ${localStorage['token']}` };
            if (localStorage['inas'] != undefined) {
                headers.InAs = `${localStorage['inas']}`;
            }
            if (company?.company_id) {
                headers.CompanyId = `${company.company_id}`;
            }
            request = request.clone({ setHeaders: headers });
        }
        return next.handle(request);
    }
}
```

---

## Authentication Flow

```
1. User submits email + password
       │
2. POST /loginctrl/verifyLogin
   ├── LoginModel::verifyLogin() validates credentials
   ├── Generate login_hash (unique per login session)
   ├── Store login_hash in tbl_login
   └── Sign JWT with HS512 using JWT_KEY env var
       │
3. Frontend stores in localStorage:
   ├── token → JWT string
   ├── currentUserDetails → user JSON
   ├── companyDts → company details
   └── timeSettings → date/time preferences
       │
4. Every subsequent API call:
   ├── JwtInterceptor adds Authorization header
   ├── PermissionCheck hook validates JWT
   ├── Hook checks login_hash against tbl_login
   ├── Hook checks inactivity timeout
   └── Hook checks @capability annotation → allow or 403
       │
5. On error (401/400):
   └── ErrorInterceptor clears localStorage → redirect to /sessions/signin
```

---

## POST /loginctrl/verifyLogin

Authenticates a user and returns a JWT token with user context.

### Controller

```php
// climate-api/application/controllers/LoginCtrl.php

class LoginCtrl extends CI_Controller {

    function __construct() {
        parent::__construct();
        $this->load->model('LoginModel', "_login");
        $this->load->model('SettingsModel', "_settings");
    }

    /**
     * @capability public
     */
    public function verifyLogin() {
        $request = json_decode(file_get_contents('php://input'), TRUE);
        echo json_encode($this->_login->verifyLogin($request), JSON_NUMERIC_CHECK);
    }
}
```

### Request

```http
POST /loginctrl/verifyLogin HTTP/1.1
Host: api.climatenaturals.com
Content-Type: application/json

{
  "username": "agent@climatespices.com",
  "password": "securepassword123"
}
```

### Success Response — 200 OK

```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VyX25hbWUiOiJBZG1pbiBVc2VyIi...",
    "user": {
      "user_id": 1,
      "user_name": "Admin User",
      "email": "agent@climatespices.com",
      "role_id": 9,
      "is_super": "No",
      "status": "Active",
      "agent_id": 101,
      "company_id": 1
    },
    "capabilities": [
      "customers.default",
      "orders.create",
      "contacts.view_assignment_history",
      "communications.whatsapp"
    ],
    "timeSettings": {
      "timezone": "Asia/Kolkata",
      "dateFormat": "DD/MM/YYYY",
      "timeFormat": "hh:mm A"
    }
  },
  "message": "Login successful"
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

**Key fields:**
- `login_hash` — unique per login session; stored in `tbl_login`; mismatch = logged in elsewhere
- `capabilities` — nested object: `module_name` → array of capability suffixes
- `is_super` — `"Yes"` bypasses all capability checks
- `login_as` — `"admin"` or `"customer"` determines which validation path the hook takes
- `exp` — token expiration (48 hours from issue)

### Error Response — 400

```json
{
  "success": false,
  "message": "Invalid credentials"
}
```

---

## POST /loginctrl/verifyOTP

Verifies OTP for two-factor authentication.

```php
/**
 * @capability public
 */
public function verifyOTP() {
    $request = json_decode(file_get_contents('php://input'), TRUE);
    echo json_encode($this->_login->verifyOTP($request), JSON_NUMERIC_CHECK);
}
```

### Request

```json
{
  "user_id": 1,
  "otp": "123456"
}
```

### Success Response — 200 OK

```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzUxMiIs...",
    "user": { "user_id": 1, "user_name": "Admin User", "..." : "..." }
  },
  "message": "OTP verified"
}
```

---

## POST /loginctrl/signup

Registers a new admin/agent user account.

```php
/**
 * @capability public
 */
public function signup() {
    $request = json_decode(file_get_contents('php://input'), TRUE);
    echo json_encode($this->_login->signup($request['data']), JSON_NUMERIC_CHECK);
}
```

### Request

```json
{
  "data": {
    "name": "New Agent",
    "email": "newagent@climatespices.com",
    "password": "securepassword123",
    "phone": "9876543210"
  }
}
```

---

## POST /loginctrl/registerCustomer

Registers a new customer account for the external customer portal.

```php
/**
 * @capability public
 */
public function registerCustomer() {
    $request = json_decode(file_get_contents('php://input'), TRUE);
    $response = $this->_login->registerCustomer($request);
    echo json_encode($response);
}
```

### Request

```json
{
  "contact_name": "Customer Name",
  "email": "customer@example.com",
  "password": "password123",
  "phone": "9876543210"
}
```

---

## POST /loginctrl/forgotPassword

Initiates password reset flow. Sends a reset link/OTP to the registered email via AWS SES.

```php
/**
 * @capability public
 */
public function forgotPassword() {
    $request = json_decode(file_get_contents('php://input'), TRUE);
    if ($request["from"] == "admin") {
        $response = $this->_login->adminForgotPassword($request);
    } else {
        $response = $this->_login->forgotPassword($request);
    }
    echo json_encode($response);
}
```

### Request

```json
{
  "email": "user@example.com",
  "from": "admin"
}
```

### Response — 200 OK

```json
{
  "success": true,
  "message": "Password reset instructions sent to your email"
}
```

---

## POST /loginctrl/checkResetPassword

Validates a password reset token before showing the reset form.

### Request

```json
{
  "reset_password": "reset-token-uuid-string"
}
```

### Response — 200 OK

```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "email": "user@example.com"
  }
}
```

---

## POST /loginctrl/resetPassword

Completes password reset using the validated token.

### Request

```json
{
  "unique_id": "reset-token-uuid-string",
  "new_password": "newSecurePassword123"
}
```

### Response — 200 OK

```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

---

## POST /loginctrl/resetNewPassword

Changes password for an authenticated user (old password required).

```php
/**
 * @capability public
 */
public function resetNewPassword() {
    $request = json_decode(file_get_contents('php://input'), TRUE);
    $response = $this->_login->resetNewPassword($request);
    echo json_encode($response);
}
```

### Request

```json
{
  "user_id": 1,
  "old_password": "currentPassword",
  "new_password": "newPassword123"
}
```

---

## Session Management

### Inactivity Timeout

The `PermissionCheck` hook tracks the last API request time per user:

```php
// hooks/permission_check.php — inside CheckAccess()

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

Tables involved:
- `tbl_user_last_request_log` — stores `user_id` and `request_time`
- `tbl_settings` — `setting_name = 'inactivity_setting'` stores the timeout in minutes

### Single-Session Enforcement

Each login generates a unique `login_hash` stored in both the JWT payload and `tbl_login`. On every request, the hook validates the hash:

```php
// hooks/permission_check.php — inside CheckAccess()

$login_hash = $AuthData['login_hash'];
$query = $db->select("login_id")->from("tbl_login")
    ->where("login_hash", $login_hash)
    ->where("user_id", $AuthData['user_id'])->get();

if (!$query->num_rows()) {
    $return = array("status" => 400, "error" => "Session Change");
}
```

If the hash doesn't match (user logged in on another device, which generated a new hash), the request fails with `400 Session Change`.

### Frontend Session Handling

The `ErrorInterceptor` handles auth failures and maintains cross-tab activity sync:

```typescript
// climate-admin/src/app/shared/helpers/error.interceptor.ts

@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
    private readonly LAST_ACTIVITY_KEY = 'lastActivityTime';

    intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        return next.handle(request).pipe(
            tap(() => {
                if (localStorage.getItem('currentUserDetails')) {
                    localStorage.setItem(this.LAST_ACTIVITY_KEY, Date.now().toString());
                }
            }),
            catchError(err => {
                let status = `${err.status}`;
                if (["400", "402"].indexOf(status) > -1) {
                    if (err.statusText == 'Session Change') {
                        this.snackBar.open(
                            "Your session has been terminated as you have changed credentials in another device.",
                            "Ok Noted", { duration: 30000 }
                        );
                    } else if (err.statusText.startsWith('Session expired due to inactivity for')) {
                        this.snackBar.open(err.statusText, "Ok Noted", { duration: 30000 });
                    }
                    localStorage.clear();
                    this.route.navigate(['/sessions/signin']);
                } else if (status == "401") {
                    this.snackBar.open(
                        "Your session has been terminated as you have logged in on another device",
                        "Ok Noted", { duration: 30000 }
                    );
                    localStorage.clear();
                    this.route.navigate(['/sessions/signin']);
                } else if (status == "403") {
                    this.snackBar.open("Permission Denied", "Ok Noted", { duration: 30000 });
                }
                return next.handle(request);
            })
        );
    }
}
```

### localStorage Keys

| Key | Content | Purpose |
|-----|---------|---------|
| `token` | JWT token string | Authorization header |
| `currentUserDetails` | User JSON object | User context, role, agent_id |
| `companyDts` | Company JSON object | Multi-company context |
| `timeSettings` | Date/time preferences | UI formatting |
| `lastActivityTime` | Unix timestamp | Cross-tab inactivity sync |
| `inas` | User ID (optional) | Admin impersonation |

---

## Permission Hook

The `PermissionCheck` class handles the full auth pipeline. Here is the capability resolution logic:

```php
// hooks/permission_check.php — capability resolution

// 1. Extract @capability annotation from controller method
$rc = new ReflectionClass($class);
$rc_method = $rc->getMethod($method);
$doc_comment = $rc_method->getDocComment();
$access_line = preg_match("/\*\s*@capability\s+([\w_\.\-\s]*)/", $doc_comment, $matches);

// 2. Parse capability string into array
$access = trim(preg_replace("/\s+/", " ", $matches[1]));
$access_array = explode(" ", $access);

// 3. Resolution order:
if (in_array('public', $access_array)) {
    // @capability public → skip all auth
} elseif (count(array_intersect(['authenticated', 'user'], $access_array))) {
    // @capability authenticated → any valid JWT
} elseif ($AuthData['is_super'] == "Yes") {
    // Super admin → bypass all capability checks
} elseif (!empty($access_array)) {
    // Check specific capability: "module.action"
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

### Capability Annotation Examples

```php
/** @capability public */
public function verifyLogin() { }           // No auth required

/** @capability authenticated */
public function getProfile() { }            // Any valid JWT

/** @capability customers.default */
public function getAccounts() { }           // Requires customers.default

/** @capability orders.create */
public function save() { }                  // Requires orders.create

/** @capability contacts.view_assignment_history */
public function getTimeline() { }           // Requires specific capability
```

### CORS Configuration

The `preflight()` method runs as a `pre_system` hook, before any controller loads:

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
        die();
    }
}
```

---

## Error Codes

| HTTP Status | Error String | Description | Frontend Action |
|-------------|-------------|-------------|-----------------|
| 200 | — | Success | Process response |
| 400 | `Session Change` | login_hash mismatch — logged in on another device | Clear localStorage, redirect to signin |
| 400 | `Session expired due to inactivity for more than N minutes` | Inactivity timeout exceeded | Clear localStorage, redirect to signin |
| 400 | `User Inactive` | User account status is not `Active` | Clear localStorage, redirect to signin |
| 400 | `User not found` | User deleted or missing from tbl_users | Clear localStorage, redirect to signin |
| 400 | `Bad Request` | JWT decode failed (expired, malformed, wrong key) | Clear localStorage, redirect to signin |
| 400 | `invalid user type` | User-Type header doesn't match JWT login_as | Clear localStorage, redirect to signin |
| 401 | `Unauthorized Access` | No Authorization header or token missing | Clear localStorage, redirect to signin |
| 403 | `Forbidden` | Valid JWT but user lacks the required capability | Show "Permission Denied" snackbar |
| 404 | — | Controller method not found | Show "Function Not Implemented" snackbar |
| 501 | `No capability defined` | Controller method missing `@capability` annotation | Block request (developer error) |

---

## Cross-References

| Document | Path |
|----------|------|
| Security Architecture | `docs/01-system-architecture/security.md` |
| Backend Architecture | `docs/01-system-architecture/backend-architecture.md` |
| Frontend Architecture | `docs/01-system-architecture/frontend-architecture.md` |
| RBAC & Capabilities | `docs/03-database-design/configuration-tables.md` |
| User & Role Tables | `docs/03-database-design/configuration-tables.md` |
| Accounts API | `docs/05-api-documentation/accounts-api.md` |
| Conversations API | `docs/05-api-documentation/conversations-api.md` |
| WhatsApp API | `docs/05-api-documentation/whatsapp-api.md` |
| Orders API | `docs/05-api-documentation/orders-api.md` |
