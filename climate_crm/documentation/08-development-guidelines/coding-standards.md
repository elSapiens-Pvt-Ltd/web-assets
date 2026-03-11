> Module: climate/guidelines/coding-standards
> Last updated: 2026-03-11

# Coding Standards

## Table of Contents

- [Overview](#overview)
- [Backend (PHP / CodeIgniter 3)](#backend-php--codeigniter-3)
  - [Controller Conventions](#controller-conventions)
  - [Model Conventions](#model-conventions)
  - [Table Naming](#table-naming)
  - [Error Handling](#error-handling)
- [Frontend (Angular / TypeScript)](#frontend-angular--typescript)
  - [Component Conventions](#component-conventions)
  - [Service Conventions](#service-conventions)
  - [Module Conventions](#module-conventions)
  - [State Management](#state-management)
  - [Template Conventions](#template-conventions)
  - [Pipes](#pipes)
- [Git Conventions](#git-conventions)
  - [Branch Naming](#branch-naming)
  - [Commit Message Format](#commit-message-format)
- [General Rules](#general-rules)
- [Cross-References](#cross-references)

---

## Overview

This document defines the coding conventions used across the Climate CRM project — covering both the Angular frontend and CodeIgniter backend.

---

## Backend (PHP / CodeIgniter 3)

### Controller Conventions

**File naming**: PascalCase — `Accounts.php`, `AssignmentHistory.php`, `ContactHandles.php`

**Class naming**: Same as file name, extends `CI_Controller`

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class AssignmentHistory extends CI_Controller {

    public function __construct() {
        parent::__construct();
        $this->load->database();
        $this->load->model('ContactAssignmentHistoryModel', '_historyModel');
    }
}
```

**Method naming**: camelCase

```php
public function getTimeline() { }
public function getAgentWorkload() { }
public function recordTransfer() { }
```

**Capability annotations**: Use DocBlock `@capability` to define required permissions:

```php
/**
 * Get assignment timeline for a contact
 * @capability contacts.view_assignment_history
 */
public function getTimeline() { }
```

The `AuthHook` reads these annotations and enforces them before the method executes.

**Input handling**:

```php
// GET parameters
$start = $this->input->get('start') ?? 0;
$limit = $this->input->get('limit') ?? 20;

// POST JSON body
$data = json_decode($this->input->raw_input_stream, true);

// URL segments
$id = $this->uri->segment(3);
```

**Response format**:

```php
// Standard JSON response
echo Risposta::json_encode([
    'success' => true,
    'data' => $result,
    'message' => 'Records retrieved'
]);

// Error response
$this->output->set_status_header(400);
echo Risposta::json_encode([
    'success' => false,
    'message' => 'Validation failed'
]);
```

Always use `Risposta::json_encode()` instead of `json_encode()` for consistent output.

---

### Model Conventions

**File naming**: PascalCase with `Model` suffix — `ProfileAccountsModel.php`, `ContactAssignmentHistoryModel.php`

**Class naming**: Same as file, extends `CI_Model`

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class ContactAssignmentHistoryModel extends CI_Model {

    private $table = 'tbl_contact_assignment_history';

    public function __construct() {
        parent::__construct();
    }
}
```

**Method naming prefixes**:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `get` | Retrieve data | `getList()`, `getById()`, `getContactTimeline()` |
| `create` | Insert new record | `create($data)`, `createForDirectOrder()` |
| `update` | Modify existing record | `update($id, $data)`, `updateStatus()` |
| `record` | Log an event | `recordAssignment()`, `recordTransfer()` |
| `delete` | Remove record | `delete($id)`, `softDelete($id)` |
| `count` | Count records | `countByAgent()`, `countActive()` |

**Query builder pattern**:

```php
// Select with joins
$this->db->select('h.*, u.user_name as assigned_to_name')
         ->from($this->table . ' h')
         ->join('tbl_users u', 'u.user_id = h.assigned_to_user_id', 'left')
         ->where('h.contact_id', $contact_id)
         ->order_by('h.assigned_at', 'DESC')
         ->limit($limit, $offset);

$result = $this->db->get()->result_array();
```

**Transaction pattern**:

```php
$this->db->trans_begin();

try {
    $this->db->insert('tbl_orders', $order_data);
    $order_id = $this->db->insert_id();

    foreach ($items as $item) {
        $item['order_id'] = $order_id;
        $this->db->insert('tbl_order_items', $item);
    }

    $this->db->trans_commit();
    return $order_id;
} catch (Exception $e) {
    $this->db->trans_rollback();
    log_message('error', 'Order creation failed: ' . $e->getMessage());
    return false;
}
```

---

### Table Naming

| Convention | Example |
|------------|---------|
| Standard tables | `tbl_orders`, `tbl_users`, `tbl_settings` |
| CRM data tables | `temp_tbl_contacts`, `temp_tbl_accounts` |
| BIGINT unsigned auto-increment PK | `id` or `{entity}_id` |
| Timestamps | `created_at DATETIME`, `updated_at DATETIME` |
| Soft delete | `status ENUM('active', 'inactive', 'deleted')` |
| Foreign keys | `{related_table}_id` (e.g., `contact_id`, `agent_id`) |

---

### Error Handling

```php
// Log errors
log_message('error', 'Method failed: ' . $e->getMessage());

// Never expose internal errors to client
echo Risposta::json_encode([
    'success' => false,
    'message' => 'An error occurred'  // Generic message
]);
```

---

## Frontend (Angular / TypeScript)

### Component Conventions

**File naming**: kebab-case — `customer-contacts.component.ts`, `assignment-history-dialog.component.html`

**Folder structure**:

```
views/{feature}/
├── components/
│   └── {component-name}/
│       ├── {component-name}.component.ts
│       ├── {component-name}.component.html
│       └── {component-name}.component.scss
├── services/
│   └── {feature}.service.ts
└── models/
    └── {feature}.model.ts
```

**Component class**:

```typescript
@Component({
  selector: 'app-customer-contacts-main',
  templateUrl: './customer-contacts.component.html',
  styleUrls: ['./customer-contacts.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: rispostaAnimations,
  host: { class: 'paging-host module-host' }
})
export class CustomerContactsComponent implements OnInit, OnDestroy {

  constructor(
    private cd: ChangeDetectorRef,
    private service: CustomerContactService
  ) { }

  ngOnInit(): void { }
  ngOnDestroy(): void { }
}
```

**Key patterns**:
- Always use `ChangeDetectionStrategy.OnPush` for performance
- Call `this.cd.detectChanges()` after async operations
- Use `rispostaAnimations` for consistent animations
- Set `host` class for layout integration
- Implement `OnDestroy` to unsubscribe from observables

---

### Service Conventions

**File naming**: kebab-case with `.service.ts` suffix

**Class pattern**:

```typescript
@Injectable({ providedIn: 'root' })
export class CustomerContactService {

  private contactSourceSub = new Subject<any>();

  constructor(private http: HttpClient) { }

  getAllCustomerContacts(start: number, limit: number, filter: any): Observable<any> {
    return this.http.post<any>(
      AppConfig.settings.apiServer.dataServer + '/contact/getList',
      { start, limit, filters: filter }
    );
  }

  getContactSource(): Observable<any> {
    return this.contactSourceSub.asObservable();
  }
}
```

**API URL pattern**: Always use `AppConfig.settings.apiServer.dataServer` as the base URL.

---

### Module Conventions

```typescript
@NgModule({
  declarations: [
    FeatureComponent,
    FeatureDialogComponent
  ],
  imports: [
    CommonModule,
    FeatureRoutingModule,
    SharedModule,
    // Angular Material imports
    MatButtonModule,
    MatTableModule,
    MatDialogModule
  ]
})
export class FeatureModule { }
```

- Import `SharedModule` for common components/pipes/directives
- Import Material modules individually (not the entire library)
- Declare only components used within this module

---

### State Management

The project uses **RxJS BehaviorSubjects** instead of NgRx:

```typescript
// In service
private dataSubject = new BehaviorSubject<any[]>([]);
public data$ = this.dataSubject.asObservable();

updateData(newData: any[]): void {
  this.dataSubject.next(newData);
}

// In component
this.service.data$.pipe(
  takeUntil(this.destroy$)
).subscribe(data => {
  this.items = data;
  this.cd.detectChanges();
});
```

---

### Template Conventions

```html
<!-- Material table pattern -->
<mat-table [dataSource]="dataSource">
  <ng-container matColumnDef="name">
    <mat-header-cell *matHeaderCellDef>Name</mat-header-cell>
    <mat-cell *matCellDef="let row">{{ row.name }}</mat-cell>
  </ng-container>
  <mat-header-row *matHeaderRowDef="displayedColumns"></mat-header-row>
  <mat-row *matRowDef="let row; columns: displayedColumns"></mat-row>
</mat-table>

<!-- Permission check -->
<button *ngIf="'orders.create_order' | hasPermission" mat-raised-button>
  Create Order
</button>

<!-- Relative time display -->
<span>{{ row.created_at | relativeTime }}</span>
```

---

### Pipes

Custom pipes in `shared/pipes/`:

| Pipe | Purpose | Usage |
|------|---------|-------|
| `hasPermission` | Check user capability | `*ngIf="'cap.name' \| hasPermission"` |
| `relativeTime` | Display "2 hours ago" | `{{ date \| relativeTime }}` |
| `orderStatus` | Format order status | `{{ status \| orderStatus }}` |

---

## Git Conventions

### Branch Naming

```
features/{feature-description}
fix/{bug-description}
hotfix/{urgent-fix}
```

### Commit Message Format

```
type(scope): description

Examples:
feat(whatsapp): add template message support
fix(orders): correct tax calculation for IGST
fix(dialogs): disable close on various dialog components
```

Types: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`

---

## General Rules

1. **No hardcoded URLs** — Use `AppConfig` for API URLs, environment files for feature flags
2. **No inline styles** — Use component SCSS files or Tailwind utility classes
3. **No console.log in production** — Remove debug logs before committing
4. **Always handle errors** — Backend: log and return generic message. Frontend: show toast/snackbar
5. **Use transactions** — Wrap multi-table operations in database transactions
6. **Validate at boundaries** — Validate user input at controller level, trust internal data
7. **Use lazy loading** — All feature modules must be lazy-loaded via `loadChildren`

---

## Cross-References

- [Backend Architecture](../01-system-architecture/backend-architecture.md) — Controller/model layer details and authentication hooks
- [Frontend Architecture](../01-system-architecture/frontend-architecture.md) — Angular module structure and service patterns
- [Folder Structure Overview](../02-folder-structure/overview.md) — Where controllers, models, and components live
- [Migration System](../03-database-design/migration-system.md) — Database schema conventions and table naming
- [Adding New Modules](./adding-modules.md) — Step-by-step guide applying these conventions to a new feature
- [Adding New APIs](./adding-apis.md) — Applying these conventions when creating new endpoints
- [Deployment Guide](../07-deployment-guide/) — How code is built and deployed to production
