# Contacts & Accounts Module

> Module: `climate/modules/contacts`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [Data Model](#data-model)
3. [Account Management](#account-management)
4. [Contact Management](#contact-management)
5. [Contact Handles](#contact-handles)
6. [Address Management](#address-management)
7. [Account Merge Workflow](#account-merge-workflow)
8. [Frontend Components](#frontend-components)
9. [Backend Controllers](#backend-controllers)
10. [Cross-References](#cross-references)

---

## Overview

The Contacts & Accounts module is the foundation of the CRM, managing customer data through a hierarchical model: **Account → Contacts → Handles**. An account represents a business or individual customer, contacts are the people within that account, and handles are the communication channels (phone, email, WhatsApp) for each contact.

---

## Data Model

```
temp_tbl_accounts (Business or Individual)
│
├── temp_tbl_contacts (People within the account)
│   │
│   ├── temp_tbl_contact_handles (Phone, Email, WhatsApp, etc.)
│   │   └── Unique constraint: (handle_type, handle_value)
│   │
│   └── tbl_authentications (Login credentials for customer portal)
│
├── temp_tbl_accounts_address (Billing & Shipping addresses)
│   └── GST number per address
│
├── tbl_orders (Linked orders)
│
└── tbl_opportunities (Sales pipeline)
```

---

## Account Management

### Account Creation

Account creation is a transactional operation handled by `Accounts::createAccount()`. It creates or updates an account along with its contacts and addresses in a single request:

```php
class Accounts extends CI_Controller
{
    public function __construct()
    {
        parent::__construct();
        $this->load->model('AccountsModel', '_accounts');
        $this->load->model('ContactModel', '_contacts');
        $this->load->model('ContactHandlesModel', '_handles');
        $this->load->model('AccountsAddressModel', '_addresses');
    }

    /**
     * @capability customers.default
     */
    public function createAccount()
    {
        $request = json_decode(file_get_contents('php://input'), true);
        $this->db->trans_begin();
        // 1. Create/update account
        // 2. Create/update contacts
        // 3. Create/update handles
        // 4. Create/update addresses
        // 5. Link to conversation (if originated from WhatsApp)
        if ($this->db->trans_status() === FALSE) {
            $this->db->trans_rollback();
        } else {
            $this->db->trans_commit();
        }
    }
}
```

**Key Validations**:
- GST number uniqueness check across all accounts
- Phone number normalization (Indian `0` prefix → `91`)
- Required fields: `account_name`, at least one contact

### Account Types

| Type | Description | Use Case |
|------|-------------|----------|
| `Business` | Company/firm with GST, FSSAI | B2B customers |
| `Individual` | Personal account | B2C or small buyers |

### Account Status Lifecycle

```
active ──► inactive ──► closed
  │                       │
  └───────────────────────┘
         reactivate
```

- **active**: Normal operating state
- **inactive**: Temporarily disabled
- **closed**: Permanently closed (can be reactivated via `Customers::reactivateAccount`)

### Account Fields

**Business Details**: `gst_number` (validated for uniqueness), `account_fssai_number` (food safety license), `business_type` (Proprietory, Partnership, Private Limited, etc.), `business_category` (trading classification), `distribution_type` (Retailer, Wholesaler, review_pending).

**Financial Summary** (auto-calculated): `total_orders`, `order_count`, `total_revenue`, `order_value`, `total_paid`, `first_order_date`, `last_order_date`.

**Classification**: `account_score` (numeric value score), `region` (geographic), `is_export` (export customer flag).

---

## Contact Management

### Contact-Account Relationship

- Each contact belongs to exactly one account (`account_id` FK)
- An account can have multiple contacts
- One contact per account can be marked as `is_primary_contact`
- Deleting an account cascades to all its contacts

### Contact Fields

| Field | Type | Description |
|-------|------|-------------|
| `contact_name` | VARCHAR(100) | Full name |
| `designation` | VARCHAR(50) | Job title/role |
| `is_primary_contact` | TINYINT | Primary contact flag |
| `status` | ENUM | active / inactive / deleted |
| `email_verified` | TINYINT | Email verification status |
| `mobile_verified` | TINYINT | Mobile verification status |

### Communication Preferences

| Field | Description |
|-------|-------------|
| `daily_rate_whatsapp` | Opted in for daily commodity rate updates via WhatsApp |
| `enable_email` | Email communications enabled |
| `enable_whatsapp` | WhatsApp communications enabled |
| `unsubscribed_notifications` | List of unsubscribed notification types |

---

## Contact Handles

### Multi-Channel Handles

Each contact can have multiple handles (communication channels):

| Handle Type | Example | Usage |
|-------------|---------|-------|
| `phone` | +91 9876543210 | Phone calls |
| `email` | user@example.com | Email communication |
| `whatsapp` | 919876543210 | WhatsApp messaging |
| `facebook` | fb_handle | Facebook messaging |
| `instagram` | ig_handle | Instagram messaging |

### Handle Uniqueness

The combination `(handle_type, handle_value)` is globally unique. This prevents the same phone number or email from being registered to multiple contacts.

### Phone Number Normalization

Indian phone numbers are automatically normalized in `phone_number_helper.php`:

```
Input:  09876543210  (0 prefix)
Output: 919876543210 (91 prefix)
```

### Handle Validation

| Purpose | Method | Rules |
|---------|--------|-------|
| For Calls | `ContactHandles::validateForCall()` | Country code present, valid phone format |
| For Messages | `ContactHandles::validateForMessage()` | Handle active, WhatsApp handle preferred |

---

## Address Management

### Address Types

| Type | Description |
|------|-------------|
| `billing` | Tax invoice address |
| `shipping` | Delivery address |
| `billing & shipping` | Combined address |

### Address Fields

- **Address Lines**: `line_1`, `line_2`
- **Location**: `city`, `state`, `country` (text) + `state_id`, `country_id` (FK references)
- **Postal**: `pincode`
- **Tax**: `gst_number` (address-specific GST, can differ from account GST)
- **Geolocation**: `latitude`, `longitude` (for mapping/distance calculations)
- **Contact Info**: `contact_name`, `contact_number` (delivery contact)

### Address Usage in Orders

When an order is created, the selected billing and shipping addresses are **snapshotted** into `tbl_order_data` as JSON. This preserves the address at the time of order, even if the account address is later updated.

---

## Account Merge Workflow

When duplicate accounts are identified, they can be merged:

```
Initiate Merge (source → target account)
    │
    ├── merge_type: 'direct' (admin) or 'request' (needs approval)
    │
    ▼
tbl_account_merge_requests (status: 'pending')
    │
    ├── Approve → Execute merge:
    │   ├── Transfer contacts
    │   ├── Transfer addresses
    │   ├── Transfer orders
    │   ├── Transfer conversations
    │   ├── Log in assignment history (type: 'contact_merged')
    │   └── Close source account
    │
    └── Reject → Record rejection_reason
```

All merge operations are logged in `tbl_account_merge_requests_logs` with full details of what was transferred and when.

---

## Frontend Components

### Customers Module (`views/customers/`)

| Component | Route | Purpose |
|-----------|-------|---------|
| Account List | `/accounts` | Paginated list with search, filters by status/region |
| Edit Account | `/accounts/edit/:id` | Full account editing with tabs for details, contacts, addresses |
| Merge Account | (dialog) | Account merge workflow |

### Customer Contacts Module (`views/customer-contacts/`)

| Component | Purpose |
|-----------|---------|
| Contact List | View all contacts with assignment info |
| Assignment History Dialog | Full assignment timeline for a contact |
| Assignment Timeline | Visual timeline of all assignments and transfers |

### Leads Module (`views/leads/`)

| Component | Purpose |
|-----------|---------|
| All Contacts | Contact management with personal/demographic details |
| Create Profile | New contact/account creation flow |

---

## Backend Controllers

| Controller | Key Methods | Capability | Description |
|------------|-------------|------------|-------------|
| `Accounts` | `createAccount()` | `customers.default` | Creates/edits account with contacts and addresses in a transaction |
| `Customers` | `index()`, `getDetail()`, `save()`, `delete()`, `reactivateAccount()`, `addresses()`, `updateCustomerAddress()` | Various | Customer CRUD with pagination |
| `Contact` | `getList()`, `getDetail()`, `save()`, `status()`, `delete()` | Various | Contact CRUD |
| `ContactHandles` | `create()`, `update()`, `get()`, `validateForCall()`, `validateForMessage()` | Various | Handle management with validation |

---

## Cross-References

| Document | Path |
|----------|------|
| Core Tables (Account/Contact schema) | `03-database-design/core-tables.md` |
| Accounts API | `05-api-documentation/accounts-api.md` |
| Assignment Management | `04-core-modules/assignment-management.md` |
| Order Management | `04-core-modules/order-management.md` |
| Assignment Flow | `06-data-flow/assignment-flow.md` |
