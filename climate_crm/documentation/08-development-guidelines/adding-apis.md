> Module: climate/guidelines/adding-apis
> Last updated: 2026-03-11

# Adding New APIs

## Table of Contents

- [Overview](#overview)
- [API Architecture](#api-architecture)
- [Creating a New Endpoint](#creating-a-new-endpoint)
  - [Step 1: Add Controller Method](#step-1-add-controller-method)
  - [Step 2: Add Model Method](#step-2-add-model-method)
  - [Step 3: Register Capability](#step-3-register-capability)
- [Input Patterns](#input-patterns)
  - [POST with JSON Body](#post-with-json-body)
  - [GET with Query Parameters](#get-with-query-parameters)
  - [URL Segments](#url-segments)
- [Response Format](#response-format)
  - [Success Response](#success-response)
  - [Paginated Response](#paginated-response)
  - [Error Response](#error-response)
  - [HTTP Status Codes](#http-status-codes)
- [Frontend Integration](#frontend-integration)
  - [Add Service Method](#add-service-method)
  - [Call from Component](#call-from-component)
- [Authentication & Authorization](#authentication--authorization)
  - [Public Endpoints](#public-endpoints)
  - [Capability-Based Authorization](#capability-based-authorization)
  - [Capability Naming Convention](#capability-naming-convention)
- [External API Endpoints](#external-api-endpoints)
  - [X-API-KEY Authentication](#x-api-key-authentication)
  - [Webhook Endpoints](#webhook-endpoints)
- [Real-Time Notifications](#real-time-notifications)
- [Testing an Endpoint](#testing-an-endpoint)
- [Checklist](#checklist)
- [Cross-References](#cross-references)

---

## Overview

This guide covers how to add new API endpoints to the Climate CRM backend, including controller setup, model creation, authentication, and frontend integration.

---

## API Architecture

All API requests follow this pattern:

```
Frontend (Angular HttpClient)
    │
    ├── JWT token in Authorization header
    │   (added automatically by JwtInterceptor)
    │
    ▼
Backend (CodeIgniter)
    │
    ├── pre_system hook → CORS headers
    ├── post_controller_constructor hook → JWT validation + capability check
    │
    ▼
Controller::method()
    │
    ├── Parse input (GET params, POST JSON body)
    ├── Validate
    ├── Call Model method
    └── Return JSON response
```

---

## Creating a New Endpoint

### Step 1: Add Controller Method

In an existing controller or a new one:

```php
/**
 * Short description of what this endpoint does.
 * POST /mycontroller/myMethod
 *
 * @capability module_name.capability_name
 */
public function myMethod() {
    // 1. Parse input
    $data = json_decode($this->input->raw_input_stream, true);

    // 2. Validate
    if (empty($data['required_field'])) {
        $this->output->set_status_header(400);
        echo Risposta::json_encode([
            'success' => false,
            'message' => 'required_field is required'
        ]);
        return;
    }

    // 3. Process
    try {
        $result = $this->_model->doSomething($data);

        // 4. Return success
        echo Risposta::json_encode([
            'success' => true,
            'data' => $result
        ]);
    } catch (Exception $e) {
        log_message('error', 'myMethod failed: ' . $e->getMessage());

        $this->output->set_status_header(500);
        echo Risposta::json_encode([
            'success' => false,
            'message' => 'Operation failed'
        ]);
    }
}
```

### Step 2: Add Model Method

```php
public function doSomething($data) {
    $this->db->trans_begin();

    try {
        // Insert/update operations
        $this->db->insert($this->table, [
            'field' => $data['field'],
            'created_at' => date('Y-m-d H:i:s')
        ]);
        $id = $this->db->insert_id();

        $this->db->trans_commit();
        return ['id' => $id];
    } catch (Exception $e) {
        $this->db->trans_rollback();
        throw $e;
    }
}
```

### Step 3: Register Capability

If the endpoint requires a new permission, add it via migration:

```php
$this->db->insert('tbl_capability', [
    'module_name' => 'module_name',
    'capability' => 'module_name.capability_name',
    'capability_title' => 'Do Something',
    'capability_description' => 'Allow user to do something',
    'menu_id' => 0,
    'sort_order' => 100
]);
```

Then assign to roles:

```sql
INSERT INTO tbl_role_capability (role_id, capability_id)
SELECT role_id, capability_id
FROM tbl_roles, tbl_capability
WHERE role_name = 'Super Admin'
AND capability = 'module_name.capability_name';
```

---

## Input Patterns

### POST with JSON Body

```php
// Frontend
this.http.post(url, { field1: 'value', field2: 123 });

// Backend
$data = json_decode($this->input->raw_input_stream, true);
$field1 = $data['field1'];
$field2 = $data['field2'];
```

### GET with Query Parameters

```php
// Frontend
this.http.get(url, { params: { start: 0, limit: 20 } });

// Backend
$start = $this->input->get('start') ?? 0;
$limit = $this->input->get('limit') ?? 20;
```

### URL Segments

```php
// Frontend
this.http.get(`${url}/mymethod/${id}`);

// Backend
public function mymethod($id = null) {
    // $id from URL segment
}
// Or:
$id = $this->uri->segment(3);
```

---

## Response Format

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed"
}
```

### Paginated Response

```json
{
  "success": true,
  "data": {
    "total": 150,
    "start": 0,
    "limit": 20,
    "data": [ ... ]
  }
}
```

### Error Response

```json
{
  "success": false,
  "message": "Human-readable error message"
}
```

### HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Success (default) |
| 400 | Validation error, missing params |
| 401 | Authentication failed (JWT invalid) |
| 403 | Authorization failed (missing capability) |
| 404 | Resource not found |
| 500 | Internal server error |

---

## Frontend Integration

### Add Service Method

```typescript
// In the appropriate service file
doSomething(data: any): Observable<any> {
  return this.http.post<any>(
    AppConfig.settings.apiServer.dataServer + '/mycontroller/myMethod',
    data
  );
}
```

### Call from Component

```typescript
this.service.doSomething({ field1: 'value' }).pipe(
  takeUntil(this.destroy$)
).subscribe({
  next: (res) => {
    if (res.success) {
      // Handle success
      this.cd.detectChanges();
    } else {
      // Handle API-level error
      this.snackbar.open(res.message, 'Close', { duration: 3000 });
    }
  },
  error: (err) => {
    // Handle HTTP-level error (401, 500, etc.)
    console.error('API error:', err);
  }
});
```

---

## Authentication & Authorization

### Public Endpoints

Some endpoints bypass JWT authentication. These are typically:
- Login/registration endpoints
- Webhook receivers (use their own auth)
- Health check endpoints

Public endpoints are configured in the `AuthHook` exclude list.

### Capability-Based Authorization

The `@capability` DocBlock annotation controls access:

```php
/**
 * @capability orders.create_order
 */
public function create() { }
```

The `AuthHook` reads this annotation:
1. Extracts the capability string
2. Looks up the user's role capabilities
3. If the user's role has the capability → allow
4. If not → return 403

### Capability Naming Convention

```
{module_name}.{action}_{resource}

Examples:
orders.create_order
orders.view_order
orders.edit_order
contacts.view_assignment_history
reports.view_crm_reports
```

---

## External API Endpoints

For endpoints called by external systems (not the Angular frontend):

### X-API-KEY Authentication

```php
/**
 * External API endpoint
 * No JWT required — uses X-API-KEY header
 */
public function externalEndpoint() {
    // Validate API key
    $api_key = $this->input->get_request_header('X-API-KEY');

    if (!$api_key || !$this->apiAuth->validate($api_key)) {
        $this->output->set_status_header(401);
        echo Risposta::json_encode(['success' => false, 'message' => 'Invalid API key']);
        return;
    }

    // Process request...
}
```

### Webhook Endpoints

```php
/**
 * Webhook receiver — no auth required
 * Must respond quickly (HTTP 200)
 */
public function webhook() {
    // 1. Store raw payload for audit
    $raw = file_get_contents('php://input');
    $this->webhookLog->store($raw);

    // 2. Parse and validate
    $data = json_decode($raw, true);

    // 3. Queue for async processing
    $this->queue->push('webhook_channel', $data);

    // 4. Respond immediately
    echo 'OK';
}
```

---

## Real-Time Notifications

If your endpoint should trigger real-time UI updates:

```php
// After database operation
$this->load->library('queue');

$this->queue->push('channel_name', [
    'chatType' => 'event_type',
    'data' => $event_data,
    'agent_id' => $target_agent_id,
    'timestamp' => time()
]);
```

The WebSocket server picks up queue messages and delivers to connected clients.

---

## Testing an Endpoint

### Using curl

```bash
# POST with JSON body
curl -X POST http://climate.loc/index.php/mycontroller/myMethod \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{"field1": "value"}'

# GET with parameters
curl "http://climate.loc/index.php/mycontroller/list?start=0&limit=20" \
  -H "Authorization: Bearer <jwt_token>"
```

### Getting a JWT Token

```bash
# Login to get token
curl -X POST http://climate.loc/index.php/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password"}'

# Response includes access_token
```

---

## Checklist

- [ ] Controller method created with proper DocBlock
- [ ] `@capability` annotation added
- [ ] Model method created with transaction handling
- [ ] Input validation in controller
- [ ] Error handling with `log_message()`
- [ ] Consistent JSON response format
- [ ] Capability registered in migration (if new)
- [ ] Capability assigned to roles
- [ ] Frontend service method added
- [ ] Frontend component integrated
- [ ] Endpoint tested with curl

---

## Cross-References

- [Backend Architecture](../01-system-architecture/backend-architecture.md) — AuthHook, JWT flow, and CodeIgniter routing details
- [Frontend Architecture](../01-system-architecture/frontend-architecture.md) — JwtInterceptor, HttpClient patterns, and service layer
- [Folder Structure Overview](../02-folder-structure/overview.md) — Where to place new controllers and models in the API project
- [Migration System](../03-database-design/migration-system.md) — Creating the capability registration migration in Step 3
- [Coding Standards](./coding-standards.md) — Response format rules, error handling conventions, and naming
- [Adding New Modules](./adding-modules.md) — Full end-to-end module guide that uses these API patterns
- [Deployment Guide](../07-deployment-guide/) — Deploying new endpoints to staging and production environments
