# Configuration & System Tables

> Module: `climate/database/config`
> Last updated: 2026-03-11

---

## Table of Contents

1. [User Management](#user-management)
2. [Access Control](#access-control)
3. [Session & Authentication](#session--authentication)
4. [Notifications](#notifications)
5. [Reference Data](#reference-data)
6. [Company & Organization](#company--organization)
7. [Workforce Management](#workforce-management)
8. [Integration Tables](#integration-tables)
9. [Cross-References](#cross-references)

---

## User Management

### tbl_users

System users including sales agents, admins, and managers. The `user_status` field controls access — inactive users are blocked by the PermissionCheck hook.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `user_id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `first_name` | VARCHAR(100) | Yes | NULL | First name |
| `last_name` | VARCHAR(100) | Yes | NULL | Last name |
| `user_name` | VARCHAR(100) | No | — | Login username (unique) |
| `user_email` | VARCHAR(100) | Yes | NULL | Email address |
| `user_phone` | VARCHAR(20) | Yes | NULL | Phone number |
| `password` | VARCHAR(255) | No | — | Hashed password |
| `user_type` | VARCHAR(50) | Yes | NULL | User classification |
| `user_status` | ENUM('Active','Inactive') | No | `'Active'` | Account status |
| `role_id` | INT UNSIGNED | No | — | FK to `tbl_roles` |
| `company_id` | INT UNSIGNED | Yes | NULL | FK to `tbl_companies` |
| `godown_id` | INT UNSIGNED | Yes | NULL | FK to `tbl_godowns` — assigned warehouse |
| `agent_id` | INT UNSIGNED | Yes | NULL | FK to `tbl_telecommunication_agents` |
| `employee_id` | VARCHAR(50) | Yes | NULL | Employee ID (added by migration) |
| `is_super` | ENUM('Yes','No') | No | `'No'` | Super admin flag — bypasses all capability checks |
| `is_deleted` | ENUM('Yes','No') | No | `'No'` | Soft delete flag |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Record creation time |
| `updated_on` | DATETIME | No | CURRENT_TIMESTAMP ON UPDATE | Last update time |

**Business Rules**:
- Super admins (`is_super = 'Yes'`) bypass all capability checks in the PermissionCheck hook
- `user_status = 'Inactive'` users are rejected during JWT validation
- `is_deleted = 'Yes'` users are excluded from round-robin assignment
- `agent_id` links to `tbl_telecommunication_agents` for CRM-specific agent settings

### tbl_roles

Role definitions. Capabilities are assigned to roles via the `tbl_role_capability` junction table.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `role_id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `role_name` | VARCHAR(100) | No | — | Role display name |
| `user_type` | VARCHAR(50) | Yes | NULL | Role classification |
| `description` | TEXT | Yes | NULL | Role description |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Record creation time |

**Default Roles**:

| Role | role_id | Description |
|------|---------|-------------|
| Super Admin | 1 | Full system access |
| Sales Admin | 9 | Sales team management, all reports |
| Sales Agent | 4 | Conversation handling, order creation |

---

## Access Control

### tbl_capability

Individual permission definitions. Each capability represents a specific action within a module.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `module_name` | VARCHAR(100) | No | — | Module identifier (e.g., `customers`, `orders`) |
| `capability` | VARCHAR(100) | No | — | Action identifier (e.g., `default`, `create`, `edit`) |
| `description` | VARCHAR(255) | Yes | NULL | Human-readable description |

Capabilities are referenced in controller DocBlock annotations as `@capability module_name.capability` (e.g., `@capability customers.default`).

### tbl_role_capability

Many-to-many junction table linking roles to capabilities.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `role_id` | INT UNSIGNED | No | — | FK to `tbl_roles` |
| `capability_id` | INT UNSIGNED | No | — | FK to `tbl_capability` |

The PermissionCheck hook resolves capabilities by reading `@capability` from the controller method's DocBlock, splitting on `.`, and checking if `capabilities[module_name]` contains the action in the JWT payload.

---

## Session & Authentication

### tbl_login

Tracks active login sessions. Each login generates a unique `login_hash` stored both here and in the JWT payload. When a user logs in on another device, the old session's hash no longer matches, terminating it.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `login_id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `user_id` | INT UNSIGNED | No | — | FK to `tbl_users` |
| `login_hash` | VARCHAR(255) | No | — | Unique session identifier |
| `ip_address` | VARCHAR(45) | Yes | NULL | Client IP address |
| `user_agent` | TEXT | Yes | NULL | Browser user agent string |
| `logged_in_at` | DATETIME | No | CURRENT_TIMESTAMP | Login timestamp |
| `expires_at` | DATETIME | Yes | NULL | Token expiration time |

**Business Rules**:
- On each authenticated request, the hook queries `tbl_login` for a matching `(login_hash, user_id)` — if not found, the response is `400 Session Change`
- On new login, previous login records for the user may have their `login_hash` cleared

### tbl_user_last_request_log

Tracks the timestamp of each user's last API request. The PermissionCheck hook compares this against `tbl_settings.inactivity_setting` (in minutes) to enforce inactivity timeouts.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `user_id` | INT UNSIGNED | No | — | FK to `tbl_users` |
| `request_time` | DATETIME | No | — | Timestamp of last request |

**Hook Logic**:
```php
$time_diff = strtotime($current_time) - strtotime($last_request_time);
$inactive_time = $db->select("setting_val")->from("tbl_settings")
    ->where("setting_name", "inactivity_setting")->get()->row_array();
if ($time_diff > ($inactive_time['setting_val'] * 60)) {
    // Session expired due to inactivity
}
```

---

## Notifications

### tbl_firebase_tokens

Stores Firebase Cloud Messaging device tokens for push notification delivery.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `user_id` | INT UNSIGNED | No | — | FK to `tbl_users` |
| `token` | TEXT | No | — | FCM device token |
| `device_type` | VARCHAR(20) | Yes | NULL | `web`, `android`, `ios` |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Token registration time |

### tbl_notifications

System notification records for in-app notification history.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INT UNSIGNED | No | AUTO_INCREMENT | Primary key |
| `user_id` | INT UNSIGNED | No | — | Target user |
| `type` | VARCHAR(50) | Yes | NULL | Notification type |
| `title` | VARCHAR(255) | Yes | NULL | Notification title |
| `body` | TEXT | Yes | NULL | Notification body |
| `data` | JSON / TEXT | Yes | NULL | Additional payload data |
| `is_read` | TINYINT(1) | No | `0` | Read status |
| `created_on` | DATETIME | No | CURRENT_TIMESTAMP | Notification time |

---

## Reference Data

### tbl_countries

| Column | Type | Description |
|--------|------|-------------|
| `country_id` | INT UNSIGNED (PK) | Primary key |
| `country_name` | VARCHAR(100) | Country name |
| `country_code` | VARCHAR(10) | ISO country code |
| `phone_code` | VARCHAR(10) | Dialing code (e.g., `+91`) |

### tbl_states

| Column | Type | Description |
|--------|------|-------------|
| `state_id` | INT UNSIGNED (PK) | Primary key |
| `state_name` | VARCHAR(100) | State name |
| `state_code` | VARCHAR(10) | GST state code |
| `country_id` | INT UNSIGNED (FK) | FK to `tbl_countries` |

### tbl_couriers

| Column | Type | Description |
|--------|------|-------------|
| `courier_id` | INT UNSIGNED (PK) | Primary key |
| `courier_name` | VARCHAR(100) | Courier company name |
| `tracking_url` | VARCHAR(255) | URL template for tracking |

### tbl_godowns

| Column | Type | Description |
|--------|------|-------------|
| `godown_id` | INT UNSIGNED (PK) | Primary key |
| `godown_name` | VARCHAR(100) | Warehouse name |
| `location` | VARCHAR(255) | Physical location |
| `state_id` | INT UNSIGNED (FK) | FK to `tbl_states` |

---

## Company & Organization

### tbl_companies

Multi-company support for the platform.

| Column | Type | Description |
|--------|------|-------------|
| `company_id` | INT UNSIGNED (PK) | Primary key |
| `company_name` | VARCHAR(100) | Company name |
| `gst_number` | VARCHAR(25) | Company GST registration |
| `state_id` | INT UNSIGNED (FK) | Company's registered state (for tax calculation) |

### tbl_settings

Key-value store for system-wide configuration. Used by the PermissionCheck hook, cron jobs, and various business logic.

| Column | Type | Description |
|--------|------|-------------|
| `setting_id` | INT UNSIGNED (PK) | Primary key |
| `setting_name` | VARCHAR(100) | Setting key |
| `setting_val` | TEXT | Setting value |

**Important Settings**:

| Setting Name | Example Value | Used By |
|-------------|---------------|---------|
| `inactivity_setting` | `30` (minutes) | PermissionCheck hook — session timeout |
| `agent_allocation` | JSON array of agent IDs | Round-robin assignment |
| `token_timeout` | `48` (hours) | JWT token expiry |
| `indiamart_last_sync` | Timestamp | IndiaMart cron sync |

---

## Workforce Management

### tbl_company_holidays

Holiday calendar for agent availability checking during round-robin assignment.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT UNSIGNED (PK) | Primary key |
| `company_id` | INT UNSIGNED (FK) | FK to `tbl_companies` |
| `holiday_date` | DATE | Holiday date |
| `holiday_name` | VARCHAR(100) | Holiday description |

### tbl_user_leaves

Employee leave records. The round-robin assignment system checks leave status to skip unavailable agents.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT UNSIGNED (PK) | Primary key |
| `user_id` | INT UNSIGNED (FK) | FK to `tbl_users` |
| `leave_date` | DATE | Leave date |
| `leave_type` | ENUM('full_day','first_half','second_half') | Leave duration |
| `status` | ENUM('pending','approved','rejected') | Approval status |

### tbl_company_work_hours

Working hours per day-of-week. Used by the round-robin system to respect shift timing (and half-day leaves).

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT UNSIGNED (PK) | Primary key |
| `company_id` | INT UNSIGNED (FK) | FK to `tbl_companies` |
| `day_of_week` | TINYINT | 0=Sunday through 6=Saturday |
| `start_time` | TIME | Shift start |
| `end_time` | TIME | Shift end |
| `is_working_day` | TINYINT(1) | Whether the day is a working day |

---

## Integration Tables

### tbl_justdial_credentials

API key storage for external integrations (JustDial, partner APIs).

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT UNSIGNED (PK) | Primary key |
| `api_key` | VARCHAR(255) | API key value |
| `partner_name` | VARCHAR(100) | Integration partner name |
| `is_active` | TINYINT(1) | Whether the key is active |

### tbl_justdial_leads

Raw lead data from JustDial webhooks, stored before processing into contacts and conversations.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT UNSIGNED (PK) | Primary key |
| `lead_name` | VARCHAR(100) | Lead contact name |
| `phone` | VARCHAR(20) | Phone number |
| `email` | VARCHAR(100) | Email address |
| `query` | TEXT | Lead inquiry text |
| `raw_data` | JSON / TEXT | Full webhook payload |
| `is_processed` | TINYINT(1) | Whether lead has been converted to a conversation |
| `created_on` | DATETIME | Webhook received time |

### tbl_account_merge_requests

Tracks account merge operations — when duplicate accounts are identified, one is designated as primary and the other's data is transferred.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT UNSIGNED (PK) | Primary key |
| `primary_account_id` | BIGINT UNSIGNED | Account that will survive |
| `merged_account_id` | BIGINT UNSIGNED | Account being merged (will be marked inactive) |
| `requested_by` | INT | FK to `tbl_users` |
| `status` | ENUM('pending','completed','failed') | Merge status |
| `created_on` | DATETIME | Request time |

---

## Cross-References

| Document | Path |
|----------|------|
| Schema Overview | `03-database-design/schema-overview.md` |
| Security & Auth | `01-system-architecture/security.md` |
| API Authentication | `05-api-documentation/authentication.md` |
| Backend Architecture (Hook System) | `01-system-architecture/backend-architecture.md` |
| Assignment Flow | `06-data-flow/assignment-flow.md` |
