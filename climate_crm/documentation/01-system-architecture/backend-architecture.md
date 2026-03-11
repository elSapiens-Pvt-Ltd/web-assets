# Backend Architecture — CodeIgniter 3 REST API

> Module: `climate/api`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [Request Lifecycle](#request-lifecycle)
3. [Hook System](#hook-system)
4. [Controller Patterns](#controller-patterns)
5. [Model Layer](#model-layer)
6. [Library Layer](#library-layer)
7. [WebSocket Server](#websocket-server)
8. [Cron Jobs](#cron-jobs)
9. [Database Configuration](#database-configuration)
10. [File Structure Conventions](#file-structure-conventions)
11. [Cross-References](#cross-references)

---

## Overview

The backend is a JSON REST API built on **CodeIgniter 3** (CI3), a lightweight PHP MVC framework. It handles all business logic, data persistence, authentication, authorization, webhook processing, and real-time communication for the Climate CRM platform. The API serves the Angular 17 SPA frontend exclusively — there are no server-rendered views.

| Metric | Count |
|--------|-------|
| Controllers | 61 |
| Models | 79+ |
| Database Migrations | 326 |
| API Endpoints | 150+ |
| Database Tables | 300+ |

The API uses no custom route definitions — all routing follows CodeIgniter's default convention of `/{controller}/{method}/{param1}/{param2}/...`. Two hooks handle cross-cutting concerns: `pre_system` for CORS and `post_controller_constructor` for JWT authentication and capability-based authorization.

---

## Request Lifecycle

Every HTTP request follows this path through the framework:

```
HTTP Request
    │
    ▼
index.php (Front Controller)
    │
    ▼
┌─────────────────────────────┐
│  pre_system Hook            │
│  PermissionCheck::preflight │
│  ├── Set CORS headers       │
│  └── Return 200 for OPTIONS │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  CI Router                  │
│  /{controller}/{method}/... │
│  No custom routes defined   │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Controller Constructor     │
│  Load models, libraries     │
└─────────────┬───────────────┘
              │
              ▼
┌────────────────────────────────────┐
│  post_controller_constructor Hook  │
│  PermissionCheck::CheckAccess      │
│                                    │
│  1. Read @capability from DocBlock │
│  2. If "public" → skip auth       │
│  3. Decode JWT (HS512)             │
│  4. Verify user exists & active    │
│  5. Verify login_hash (session)    │
│  6. Check inactivity timeout       │
│  7. Check capability permission    │
│  8. Store AuthData in $CI          │
└─────────────┬──────────────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Controller::method()       │
│  ├── Parse JSON input       │
│  ├── Validate parameters    │
│  ├── Call Model methods     │
│  └── Return JSON response   │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  JSON Response              │
│  Risposta::json_encode()    │
│  ├── Numeric precision      │
│  ├── UTF-8 unescaped        │
│  └── Content-Type: json     │
└─────────────────────────────┘
```

---

## Hook System

Both hooks are registered in `application/config/hooks.php` and handled by a single class:

```php
// application/config/hooks.php

$hook['post_controller_constructor'] = array(
    'class'    => 'PermissionCheck',
    'function' => 'CheckAccess',
    'filename' => 'permission_check.php',
    'filepath' => 'hooks',
);

$hook['pre_system'] = array(
    'class'    => 'PermissionCheck',
    'function' => 'preflight',
    'filename' => 'permission_check.php',
    'filepath' => 'hooks',
);
```

### CORS Preflight (`pre_system`)

The `preflight()` method fires before any controller loads. It sets CORS headers using the requesting origin dynamically and terminates OPTIONS requests immediately:

```php
// application/hooks/permission_check.php — preflight()

public function preflight()
{
    date_default_timezone_set("Asia/Kolkata");
    $http_origin = isset($_SERVER['HTTP_ORIGIN'])
        ? $_SERVER['HTTP_ORIGIN']
        : 'https://d1rymkbr2tz0j7.cloudfront.net';
    header("Access-Control-Allow-Origin: {$http_origin}");
    header("Access-Control-Allow-Credentials: true");
    header("Access-Control-Allow-Methods: GET,POST,OPTIONS");
    header("Access-Control-Allow-Headers: Authorization, ... User-Type, CompanyId, InAs, web-version, app-version");
    header('P3P: CP="CAO PSA OUR"');
    if ('OPTIONS' == ($_SERVER['REQUEST_METHOD'] ?? '')) {
        die();
    }
}
```

### Authentication & Authorization (`post_controller_constructor`)

The `CheckAccess()` method runs after the controller is constructed but before the requested method executes. It performs the full auth pipeline:

**Step 1 — Capability Resolution via Reflection**

The hook reads the `@capability` annotation from the target method's DocBlock using PHP Reflection:

```php
// application/hooks/permission_check.php — CheckAccess()

$class = $CI->router->class;
$method = $CI->router->method;
$rc = new ReflectionClass($class);
$rc_method = $rc->getMethod($method);
$doc_comment = $rc_method->getDocComment();
$access_line = preg_match("/\*\s*@capability\s+([\w_\.\-\s]*)/", $doc_comment, $matches);
```

**Step 2 — JWT Decode**

```php
$jwtKey = config_item('jwt_key');
$token = str_replace("Bearer ", "", $headers['Authorization']);
$decoded = JWT::decode($token, new Key($jwtKey, 'HS512'));
$AuthData = json_decode(Risposta::json_encode($decoded), true);
$CI->AuthData = $AuthData;
```

**Step 3 — User Verification and Session Checks**

The hook verifies user status, login hash (single-device enforcement), and inactivity timeout:

```php
// Verify user is active
$db->select("user_status")->from("tbl_users")->where("user_name", $AuthData['user_name']);
$result = $query->row_array();
if ($result['user_status'] !== 'Active') {
    $return = array("status" => 400, 'error' => "User Inactive");
}

// Single-session enforcement via login_hash
$query = $db->select("login_id")->from("tbl_login")
    ->where("login_hash", $AuthData['login_hash'])
    ->where("user_id", $AuthData['user_id'])->get();
if (!$query->num_rows()) {
    $return = array("status" => 400, 'error' => "Session Change");
}

// Inactivity timeout check
$last_request_time = $this->getLastRequestTime($db, $AuthData['user_id']);
$this->updateRequestTime($db, $AuthData['user_id']);
if ($last_request_time) {
    $time_diff = strtotime(date("Y-m-d H:i:s")) - strtotime($last_request_time);
    $inactive_time = $db->select("setting_val")->from("tbl_settings")
        ->where("setting_name", "inactivity_setting")->get()->row_array();
    if ($time_diff > ($inactive_time['setting_val'] * 60)) {
        $return = array("status" => 400,
            'error' => "Session expired due to inactivity for more than {$inactive_time['setting_val']} minutes");
    }
}
```

**Step 4 — Capability Permission Check**

After JWT validation, the hook checks the resolved capability against the user's JWT payload:

```php
if (in_array('public', $access_array)) {
    $return = array("status" => 200, 'error' => "");
} elseif (count(array_intersect(['authenticated', 'user'], $access_array))) {
    $return = array("status" => 200, 'error' => "");     // any valid JWT
} elseif ($AuthData['is_super'] == "Yes") {
    $return = array("status" => 200, 'error' => "");     // super admin bypass
} elseif (!empty($access_array)) {
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

### Capability Annotation Types

| Annotation | Behavior |
|------------|----------|
| `@capability public` | No authentication required — webhooks, login, cron jobs |
| `@capability user` or `@capability authenticated` | Requires valid JWT, no specific capability |
| `@capability module.action` | Requires the specific capability in the JWT payload (e.g., `customers.default`) |

---

## Controller Patterns

### Constructor — Model Loading

Controllers load their required models in the constructor with aliases for convenient access:

```php
// application/controllers/Accounts.php

class Accounts extends CI_Controller {

    public function __construct()
    {
        parent::__construct();
        $this->load->database();
        $this->load->model('ProfileAccountsModel', "_accounts");
        $this->load->model('ProfileContactsModel', "_contacts");
        $this->load->model('ProfileContactHandlesModel', "_handles");
        $this->load->model('ProfileAddressModel', "_addresses");
        $this->load->model('AccountMergeRequestModel', "_merge_requests");
        $this->load->model('WhatsappModel', "_whatsapp");
        $this->load->model('SchedulingHelper', "_scheduling");
    }
```

### Input Handling

Controllers parse JSON request bodies via `php://input` and access auth data from the hook:

```php
// JSON body parsing
$json_input = $this->input->raw_input_stream;
$data = json_decode($json_input, true);

// Query parameters
$id = $this->input->get('id');

// AuthData (set by the PermissionCheck hook)
$user_id = $this->AuthData['user_id'];
$company_id = $this->AuthData['company_id'];
```

### Validation Pattern

```php
// application/controllers/Accounts.php — createAccount()

private function _parseAndValidateInput()
{
    $json_input = $this->input->raw_input_stream;
    if (empty($json_input)) {
        return $this->_sendError(400, 'No input data provided');
    }

    $data = json_decode($json_input, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        return $this->_sendError(400, 'Invalid JSON: ' . json_last_error_msg());
    }

    $validation_errors = $this->validateCreateAccountData($data);
    if (!empty($validation_errors)) {
        $this->output->set_status_header(422);
        $this->output->set_output(json_encode([
            'success' => false,
            'message' => 'Validation failed',
            'errors' => $validation_errors
        ]));
        return false;
    }
    // ...
}
```

### Transaction Pattern

Multi-step operations use database transactions with explicit rollback:

```php
// application/controllers/Accounts.php — createAccount()

/**
 * @capability user
 */
public function createAccount()
{
    $this->output->set_content_type('application/json');

    $data = $this->_parseAndValidateInput();
    if ($data === false) return;

    $is_edit_mode = !empty($data['account']['account_id']);
    $account_id = $is_edit_mode ? $data['account']['account_id'] : null;

    if ($this->_hasDuplicateGst($data['addresses'] ?? [], $account_id)) return;

    // Transaction wraps account + contacts + addresses
    $result = $this->_processAccountTransaction($data, $is_edit_mode, $account_id);
    if ($result === false) return;

    if (!empty($data['conversation_id']) && !empty($result['contacts'])) {
        $this->_handlePostCreation($data, $account_id, $result['contacts']);
    }

    $this->_sendSuccessResponse($is_edit_mode, $account_id, $result);
}
```

### Response Patterns

**Success Response**:
```php
echo Risposta::json_encode([
    'success' => true,
    'data' => $result,
    'message' => 'Operation completed'
]);
```

**Error Response**:
```php
http_response_code(400);
echo Risposta::json_encode([
    'success' => false,
    'message' => 'Validation error',
    'errors' => ['field' => 'Error description']
]);
```

### HTTP Status Codes

| Code | Usage |
|------|-------|
| `200` | Success |
| `400` | Bad request / invalid input / session errors |
| `401` | Unauthorized — missing or expired JWT |
| `403` | Forbidden — insufficient capability |
| `409` | Conflict (e.g., duplicate GST number) |
| `422` | Validation error with field-level details |

---

## Model Layer

Models encapsulate all database operations using CI3's Active Record (Query Builder). Complex queries use raw SQL. All models extend `CI_Model` and follow the PascalCase + `Model` suffix naming convention:

```php
class ProfileAccountsModel extends CI_Model {

    public function create($data) {
        $this->db->insert('temp_tbl_accounts', $data);
        return $this->db->insert_id();
    }

    public function getById($id) {
        return $this->db->get_where('temp_tbl_accounts', ['account_id' => $id])
                        ->row_array();
    }

    public function update($id, $data) {
        $this->db->where('account_id', $id);
        $this->db->update('temp_tbl_accounts', $data);
    }
}
```

### Key Models

| Model | Table(s) | Responsibility |
|-------|----------|----------------|
| `ContactMessageModel` | `tbl_whatsapp_messages`, `tbl_open_conversations` | Incoming message pipeline — handle lookup, conversation management, message insertion |
| `ProfileAccountsModel` | `temp_tbl_accounts` | Account CRUD, merge logic, duplicate detection |
| `ProfileContactsModel` | `temp_tbl_contacts` | Contact CRUD, account association |
| `ProfileContactHandlesModel` | `temp_tbl_contact_handles` | Phone/email handle management, uniqueness enforcement |
| `OrdersModel` | `tbl_orders`, `tbl_order_items` | Order lifecycle, status transitions, tax calculations |
| `WhatsappModel` | `tbl_whatsapp_messages` | Message storage, template sending, media handling |
| `AgentFRTReportModel` | `tbl_agent_frt_summary` | First Response Time analytics and daily snapshots |
| `ConversationAgingModel` | `tbl_conversation_aging` | Conversation aging snapshots for stale lead detection |
| `CronModel` | Various | Delegated cron job logic (email sending, lead sync, etc.) |

---

## Library Layer

### Risposta (JSON Output)

Custom JSON encoder that preserves PHP numeric types through JSON serialization. Standard `json_encode` converts MySQL numeric columns to strings; `Risposta::json_encode()` walks the data structure and casts numeric strings back to their proper types:

```php
echo Risposta::json_encode($data);
// Output: {"price": 99.50, "quantity": 10}
// Instead of: {"price": "99.50", "quantity": "10"}
```

### LibRedisQueue (Message Broker)

The Redis queue library acts as a bridge between the short-lived PHP request lifecycle and the persistent WebSocket server. When a message is sent or received, the controller pushes it to a Redis channel, and the WebSocket server's timer callback reads from the same channel to deliver it to connected agents:

```php
$this->load->library('LibRedisQueue', null, 'redis');

// Push to real-time delivery queue
$this->redis->push('message_queue', [
    'type' => 'new_message',
    'conversation_id' => $conv_id,
    'message' => $message_data
]);
```

### AgentAssignmentHelper

The agent assignment helper implements the 4-level priority system for routing new conversations to agents. It checks account ownership, existing open conversations, previous conversation history, and falls back to round-robin with leave and work-hours awareness. See [Assignment Flow](../06-data-flow/assignment-flow.md) for the complete algorithm.

---

## WebSocket Server

The WebSocket server is a persistent PHP process managed by the `WhatsappChat` controller. It uses the Ratchet library via the `Chat_websocket` library to maintain real-time connections with agents:

```php
// application/controllers/WhatsappChat.php

class WhatsappChat extends CI_Controller
{
    public function __construct()
    {
        parent::__construct();
        $this->load->database();
        $this->db->query("SET time_zone='+5:30'");
        $this->load->library('LibRedisQueue', null, 'redis');
        $this->load->model('ContactMessageModel', 'contactService');
        $this->key = config_item('jwt_key');
    }

    /**
     * @capability public
     */
    public function index()
    {
        try {
            $this->load->library('chat_websocket');
            $this->chat_websocket->set_callback('chatauth', array($this, 'AuthChat'));
            $this->chat_websocket->set_callback('chatjoin', array($this, 'JoinChat'));
            $this->chat_websocket->set_callback('chatoutgoing', array($this, 'OutgoingChat'));
            $this->chat_websocket->set_callback('chattimer', array($this, 'TimerChat'));
            $this->chat_websocket->run();
        } catch (\Throwable $th) {
            log_message('error', __FILE__ . ' ' . __LINE__ . ' ' . $th->getMessage());
        }
    }
}
```

### WebSocket Callbacks

| Callback | Event | Purpose |
|----------|-------|---------|
| `chatauth` | Client connects | Validates the agent's `customer_id` for authentication |
| `chatjoin` | Client joins | Sends welcome message, registers the agent's connection |
| `chatoutgoing` | Client sends message | Routes outgoing messages to the WhatsApp API |
| `chattimer` | Periodic tick | Reads from Redis queue and delivers pending messages to connected agents |

The `chattimer` callback is the key mechanism for real-time delivery. It runs on a periodic interval, reads messages from the Redis `message_queue`, and pushes them to the appropriate agent's WebSocket connection. The server also handles database reconnection for long-running processes:

```php
private function checkDatabaseConnection()
{
    try {
        if (!$this->db->conn_id || !mysqli_ping($this->db->conn_id)) {
            $this->db->reconnect();
        }
    } catch (Exception $e) {
        $this->db->reconnect();
    }
}
```

### Running the WebSocket Server

```bash
# Development
php /path/to/climate-api/index.php whatsappchat/index

# Production (via supervisor or systemd)
# Listens on port 8988
# ws://localhost:8988 (dev) or wss://api.climatenaturals.com/chat (prod)
```

---

## Cron Jobs

The `Cron` controller handles all scheduled background tasks. Each method is annotated with `@capability public` since cron jobs are invoked via CLI, not through authenticated HTTP requests:

```php
// application/controllers/Cron.php

class Cron extends CI_Controller
{
    public function __construct()
    {
        parent::__construct();
        $this->load->model('CronModel', "_cron");
        $this->load->model('reports/AgentFRTReportModel');
        $this->load->model('reports/ConversationAgingModel');
    }

    /** @capability public */
    public function sendOrderConfirmedMail() {
        $this->_cron->sendOrderConfirmedMail();
    }

    /** @capability public */
    public function indiaMartLeads() {
        $this->_cron->indiaMartLeads();
    }
}
```

### Cron Schedule

| Job | Controller Method | Frequency | Purpose |
|-----|-------------------|-----------|---------|
| Follow-up Processing | `processScheduledFollowups` | Every 5 minutes | Process due follow-ups, send push notifications |
| Order Confirmation Emails | `sendOrderConfirmedMail` | Every 10 minutes | Send email when order status changes to confirmed |
| IndiaMart Lead Sync | `indiaMartLeads` | Every 15 minutes | Pull new leads from IndiaMart API |
| Exchange Rate Update | `getExchangeRates` | Daily | Update currency exchange rates for international orders |
| Agent FRT Summary | `calculateAgentFRTSummary` | Daily at 00:30 | Calculate daily First Response Time metrics per agent |
| Conversation Aging | `generateAgingSnapshot` | Daily at 06:00 | Snapshot stale conversations for aging reports |

All cron jobs are invoked via system crontab:

```bash
# /etc/crontab entries
*/5  * * * * php /var/www/climate-api/index.php cron/processScheduledFollowups
*/10 * * * * php /var/www/climate-api/index.php cron/sendOrderConfirmedMail
*/15 * * * * php /var/www/climate-api/index.php cron/indiaMartLeads
0    0 * * * php /var/www/climate-api/index.php cron/getExchangeRates
30   0 * * * php /var/www/climate-api/index.php cron/calculateAgentFRTSummary
0    6 * * * php /var/www/climate-api/index.php cron/generateAgingSnapshot
```

---

## Database Configuration

The database connection is configured in `application/config/database.php` with environment-variable overrides for deployment flexibility:

```php
// application/config/database.php

$active_group = 'default';
$query_builder = TRUE;

$db['default'] = array(
    'dsn'      => '',
    'hostname' => $_SERVER['DBHOST'] ?? '127.0.0.1',
    'username' => $_SERVER['DBUSER'] ?? 'root',
    'password' => $_SERVER['DBPASSWORD'] ?? '',
    'database' => $_SERVER['DBNAME'] ?? 'climate',
    'dbdriver' => 'mysqli',
    'dbprefix' => '',
    'pconnect' => FALSE,
    'db_debug' => (ENVIRONMENT !== 'production'),
    'cache_on' => FALSE,
    'cachedir' => '',
    'char_set' => 'utf8mb4',
    'dbcollat' => 'utf8mb4_unicode_ci',
    'swap_pre' => '',
    'encrypt'  => FALSE,
    'compress' => FALSE,
    'stricton' => FALSE,
    'failover' => array(),
    'save_queries' => TRUE
);
```

Key configuration choices:

- **`utf8mb4` charset** — required for WhatsApp messages which frequently contain emojis
- **`pconnect: FALSE`** — persistent connections disabled to avoid stale connection issues
- **`db_debug`** — enabled only in non-production environments
- **Timezone** — set to `+5:30` (IST) on every authenticated request via the PermissionCheck hook: `$db->query("SET time_zone='+5:30'")`

### Migration System

Migrations use CI3's timestamp-based system (`YYYYMMDDHHMMSS` prefix). Auto-migration is enabled — the application migrates to latest on startup.

| Setting | Value |
|---------|-------|
| Migration Type | Timestamp |
| Total Migrations | 326 |
| Latest Migration | `20260311160036` |
| Table Prefix | `tbl_` (primary), `temp_tbl_` (profile/account) |

---

## File Structure Conventions

### Naming Conventions

| Component | File Name | Class Name | Method Case |
|-----------|-----------|------------|-------------|
| Controller | `PascalCase.php` (e.g., `OpenConversations.php`) | Matches filename, extends `CI_Controller` | camelCase |
| Model | `PascalCaseModel.php` (e.g., `OrdersModel.php`) | Matches filename, extends `CI_Model` | camelCase |
| Library | `PascalCase.php` (e.g., `Chat_websocket.php`) | Matches filename | camelCase |
| Migration | `YYYYMMDDHHMMSS_description.php` | `Migration_Description` | `up()`, `down()` |
| Helper | `snake_case_helper.php` | N/A (procedural functions) | snake_case |

### Directory Structure

```
application/
├── config/
│   ├── database.php          # Database connection
│   ├── hooks.php             # Hook registration
│   ├── config.php            # App settings (jwt_key, etc.)
│   └── migration.php         # Migration settings
├── controllers/              # 61 controllers
│   ├── Accounts.php
│   ├── Cron.php
│   ├── LoginCtrl.php
│   ├── OpenConversations.php
│   ├── Orders.php
│   ├── Whatsapp.php
│   ├── WhatsappChat.php
│   └── reports/              # Report sub-controllers
├── hooks/
│   └── permission_check.php  # Auth + CORS hook
├── libraries/
│   ├── Chat_websocket.php    # Ratchet WebSocket server
│   ├── LibRedisQueue.php     # Redis queue wrapper
│   ├── Risposta.php          # JSON encoder + utilities
│   └── AgentAssignmentHelper.php
├── models/                   # 79+ models
│   ├── ContactMessageModel.php
│   ├── OrdersModel.php
│   ├── WhatsappModel.php
│   └── reports/              # Report-specific models
├── migrations/               # 326 timestamp-based migrations
└── helpers/
    └── agent_assignment_helper.php
```

---

## Cross-References

| Document | Path |
|----------|------|
| Frontend Architecture | `01-system-architecture/frontend-architecture.md` |
| Security & Auth (detailed) | `01-system-architecture/security.md` |
| Communication Patterns | `01-system-architecture/communication-patterns.md` |
| Database Schema | `03-database-design/schema-overview.md` |
| API Authentication | `05-api-documentation/authentication.md` |
| Message Flow | `06-data-flow/message-flow.md` |
| Assignment Flow | `06-data-flow/assignment-flow.md` |
| Backend Deployment | `07-deployment-guide/backend-setup.md` |
| Coding Standards | `08-development-guidelines/coding-standards.md` |
| Adding APIs | `08-development-guidelines/adding-apis.md` |
