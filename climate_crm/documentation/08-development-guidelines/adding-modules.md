> Module: climate/guidelines/adding-modules
> Last updated: 2026-03-11

# Adding New Modules

## Table of Contents

- [Overview](#overview)
- [Frontend Module](#frontend-module)
  - [Step 1: Create Folder Structure](#step-1-create-folder-structure)
  - [Step 2: Create the Module](#step-2-create-the-module)
  - [Step 3: Create Routing Module](#step-3-create-routing-module)
  - [Step 4: Create Main Component](#step-4-create-main-component)
  - [Step 5: Create Service](#step-5-create-service)
  - [Step 6: Register Route in App Router](#step-6-register-route-in-app-router)
  - [Step 7: Add Menu Entry (Optional)](#step-7-add-menu-entry-optional)
- [Backend Module](#backend-module)
  - [Step 1: Create Controller](#step-1-create-controller)
  - [Step 2: Create Model](#step-2-create-model)
  - [Step 3: Create Migration](#step-3-create-migration)
  - [Step 4: Assign Capabilities to Roles](#step-4-assign-capabilities-to-roles)
- [Checklist](#checklist)
- [Cross-References](#cross-references)

---

## Overview

This guide walks through adding a new feature module to the Climate CRM — both the Angular frontend module and the CodeIgniter backend endpoints.

---

## Frontend Module

### Step 1: Create Folder Structure

```
src/app/views/my-feature/
├── my-feature.module.ts
├── my-feature-routing.module.ts
├── components/
│   ├── my-feature-main/
│   │   ├── my-feature-main.component.ts
│   │   ├── my-feature-main.component.html
│   │   └── my-feature-main.component.scss
│   └── my-feature-dialog/
│       ├── my-feature-dialog.component.ts
│       ├── my-feature-dialog.component.html
│       └── my-feature-dialog.component.scss
└── services/
    └── my-feature.service.ts
```

### Step 2: Create the Module

`my-feature.module.ts`:

```typescript
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MyFeatureRoutingModule } from './my-feature-routing.module';
import { SharedModule } from 'src/app/shared/shared.module';

// Angular Material
import { MatButtonModule } from '@angular/material/button';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';

// Components
import { MyFeatureMainComponent } from './components/my-feature-main/my-feature-main.component';
import { MyFeatureDialogComponent } from './components/my-feature-dialog/my-feature-dialog.component';

@NgModule({
  declarations: [
    MyFeatureMainComponent,
    MyFeatureDialogComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MyFeatureRoutingModule,
    SharedModule,
    MatButtonModule,
    MatTableModule,
    MatPaginatorModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatIconModule
  ]
})
export class MyFeatureModule { }
```

### Step 3: Create Routing Module

`my-feature-routing.module.ts`:

```typescript
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { MyFeatureMainComponent } from './components/my-feature-main/my-feature-main.component';

const routes: Routes = [
  {
    path: '',
    component: MyFeatureMainComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class MyFeatureRoutingModule { }
```

### Step 4: Create Main Component

`my-feature-main.component.ts`:

```typescript
import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, ChangeDetectorRef, ViewChild } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { MatDialog } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { rispostaAnimations } from 'src/app/shared/animations/risposta-animations';
import { MyFeatureService } from '../../services/my-feature.service';

@Component({
  selector: 'app-my-feature-main',
  templateUrl: './my-feature-main.component.html',
  styleUrls: ['./my-feature-main.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: rispostaAnimations,
  host: { class: 'paging-host module-host' }
})
export class MyFeatureMainComponent implements OnInit, OnDestroy {
  @ViewChild(MatPaginator) paginator: MatPaginator;

  displayedColumns: string[] = ['id', 'name', 'status', 'created_at', 'actions'];
  dataSource: any[] = [];
  totalRecords = 0;
  pageSize = 20;

  private destroy$ = new Subject<void>();

  constructor(
    private cd: ChangeDetectorRef,
    private dialog: MatDialog,
    private service: MyFeatureService
  ) { }

  ngOnInit(): void {
    this.loadData(0, this.pageSize);
  }

  loadData(start: number, limit: number): void {
    this.service.getList(start, limit).pipe(
      takeUntil(this.destroy$)
    ).subscribe(res => {
      if (res.success) {
        this.dataSource = res.data.data;
        this.totalRecords = res.data.total;
        this.cd.detectChanges();
      }
    });
  }

  onPageChange(event: any): void {
    this.loadData(event.pageIndex * event.pageSize, event.pageSize);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
```

### Step 5: Create Service

`services/my-feature.service.ts`:

```typescript
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AppConfig } from 'src/app/app.config';

@Injectable({ providedIn: 'root' })
export class MyFeatureService {

  private baseUrl = AppConfig.settings.apiServer.dataServer;

  constructor(private http: HttpClient) { }

  getList(start: number, limit: number, filters: any = {}): Observable<any> {
    return this.http.post<any>(
      `${this.baseUrl}/myfeature/list`,
      { start, limit, filters }
    );
  }

  getById(id: number): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/myfeature/get/${id}`);
  }

  create(data: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/myfeature/create`, data);
  }

  update(id: number, data: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/myfeature/update/${id}`, data);
  }

  delete(id: number): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/myfeature/delete/${id}`, {});
  }
}
```

### Step 6: Register Route in App Router

In `src/app/app-routing.module.ts`, add to the routes array:

```typescript
{
  path: 'my-feature',
  loadChildren: () => import('./views/my-feature/my-feature.module').then(m => m.MyFeatureModule),
  data: { title: 'My Feature', breadcrumb: 'My Feature' },
  canActivate: [AuthGuard]
}
```

### Step 7: Add Menu Entry (Optional)

If the module needs a sidebar menu entry, insert into `tbl_menu`:

```sql
INSERT INTO tbl_menu (menu_title, menu_url, menu_icon, parent_id, sort_order, status)
VALUES ('My Feature', '/my-feature', 'extension', 0, 50, 'active');
```

---

## Backend Module

### Step 1: Create Controller

`application/controllers/MyFeature.php`:

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class MyFeature extends CI_Controller {

    public function __construct() {
        parent::__construct();
        $this->load->database();
        $this->load->model('MyFeatureModel', '_model');
    }

    /**
     * Get paginated list
     * @capability my_feature.view
     */
    public function list() {
        $data = json_decode($this->input->raw_input_stream, true);
        $start = $data['start'] ?? 0;
        $limit = $data['limit'] ?? 20;
        $filters = $data['filters'] ?? [];

        $result = $this->_model->getList($start, $limit, $filters);

        echo Risposta::json_encode([
            'success' => true,
            'data' => $result
        ]);
    }

    /**
     * Get single record by ID
     * @capability my_feature.view
     */
    public function get($id = null) {
        if (!$id) {
            $this->output->set_status_header(400);
            echo Risposta::json_encode(['success' => false, 'message' => 'ID required']);
            return;
        }

        $record = $this->_model->getById($id);
        echo Risposta::json_encode([
            'success' => true,
            'data' => $record
        ]);
    }

    /**
     * Create new record
     * @capability my_feature.create
     */
    public function create() {
        $data = json_decode($this->input->raw_input_stream, true);

        if (empty($data['name'])) {
            $this->output->set_status_header(400);
            echo Risposta::json_encode(['success' => false, 'message' => 'Name is required']);
            return;
        }

        $id = $this->_model->create($data);

        if ($id) {
            echo Risposta::json_encode([
                'success' => true,
                'id' => $id,
                'message' => 'Created successfully'
            ]);
        } else {
            $this->output->set_status_header(500);
            echo Risposta::json_encode(['success' => false, 'message' => 'Creation failed']);
        }
    }

    /**
     * Update existing record
     * @capability my_feature.edit
     */
    public function update($id = null) {
        if (!$id) {
            $this->output->set_status_header(400);
            echo Risposta::json_encode(['success' => false, 'message' => 'ID required']);
            return;
        }

        $data = json_decode($this->input->raw_input_stream, true);
        $result = $this->_model->update($id, $data);

        echo Risposta::json_encode([
            'success' => $result,
            'message' => $result ? 'Updated successfully' : 'Update failed'
        ]);
    }

    /**
     * Delete record (soft delete)
     * @capability my_feature.delete
     */
    public function delete($id = null) {
        if (!$id) {
            $this->output->set_status_header(400);
            echo Risposta::json_encode(['success' => false, 'message' => 'ID required']);
            return;
        }

        $result = $this->_model->softDelete($id);

        echo Risposta::json_encode([
            'success' => $result,
            'message' => $result ? 'Deleted successfully' : 'Delete failed'
        ]);
    }
}
```

### Step 2: Create Model

`application/models/MyFeatureModel.php`:

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class MyFeatureModel extends CI_Model {

    private $table = 'tbl_my_feature';

    public function __construct() {
        parent::__construct();
    }

    public function getList($start, $limit, $filters = []) {
        $this->db->select('*')
                 ->from($this->table)
                 ->where('status !=', 'deleted');

        if (!empty($filters['status'])) {
            $this->db->where('status', $filters['status']);
        }

        if (!empty($filters['search'])) {
            $this->db->like('name', $filters['search']);
        }

        // Count before limit
        $count_query = clone $this->db;
        $total = $this->db->count_all_results('', false);

        $this->db->order_by('created_at', 'DESC')
                 ->limit($limit, $start);

        return [
            'total' => $total,
            'start' => $start,
            'limit' => $limit,
            'data' => $this->db->get()->result_array()
        ];
    }

    public function getById($id) {
        return $this->db->where('id', $id)
                        ->where('status !=', 'deleted')
                        ->get($this->table)
                        ->row_array();
    }

    public function create($data) {
        $insert = [
            'name' => $data['name'],
            'description' => $data['description'] ?? null,
            'status' => 'active',
            'created_at' => date('Y-m-d H:i:s'),
            'created_by' => $data['user_id'] ?? null
        ];

        $this->db->insert($this->table, $insert);
        return $this->db->insert_id();
    }

    public function update($id, $data) {
        $update = [
            'name' => $data['name'],
            'description' => $data['description'] ?? null,
            'updated_at' => date('Y-m-d H:i:s')
        ];

        return $this->db->where('id', $id)->update($this->table, $update);
    }

    public function softDelete($id) {
        return $this->db->where('id', $id)->update($this->table, [
            'status' => 'deleted',
            'updated_at' => date('Y-m-d H:i:s')
        ]);
    }
}
```

### Step 3: Create Migration

`application/migrations/{timestamp}_create_my_feature_table.php`:

```php
<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Migration_Create_my_feature_table extends CI_Migration {

    public function up() {
        $this->dbforge->add_field([
            'id' => ['type' => 'BIGINT', 'unsigned' => TRUE, 'auto_increment' => TRUE],
            'name' => ['type' => 'VARCHAR', 'constraint' => 255],
            'description' => ['type' => 'TEXT', 'null' => TRUE],
            'status' => ['type' => 'ENUM', 'constraint' => ['active', 'inactive', 'deleted'], 'default' => 'active'],
            'created_by' => ['type' => 'BIGINT', 'unsigned' => TRUE, 'null' => TRUE],
            'created_at DATETIME DEFAULT CURRENT_TIMESTAMP',
            'updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
        ]);
        $this->dbforge->add_key('id', TRUE);
        $this->dbforge->create_table('tbl_my_feature', TRUE);

        // Register capabilities
        $capabilities = [
            ['my_feature', 'view', 'View My Feature', 'View my feature records'],
            ['my_feature', 'create', 'Create My Feature', 'Create new records'],
            ['my_feature', 'edit', 'Edit My Feature', 'Edit existing records'],
            ['my_feature', 'delete', 'Delete My Feature', 'Delete records'],
        ];

        foreach ($capabilities as $cap) {
            $this->db->insert('tbl_capability', [
                'module_name' => $cap[0],
                'capability' => $cap[0] . '.' . $cap[1],
                'capability_title' => $cap[2],
                'capability_description' => $cap[3],
                'menu_id' => 0,
                'sort_order' => 100
            ]);
        }
    }

    public function down() {
        $this->db->where('module_name', 'my_feature')->delete('tbl_capability');
        $this->dbforge->drop_table('tbl_my_feature', TRUE);
    }
}
```

### Step 4: Assign Capabilities to Roles

After running the migration, assign the new capabilities to appropriate roles:

```sql
-- Give Super Admin all new capabilities
INSERT INTO tbl_role_capability (role_id, capability_id)
SELECT 1, capability_id FROM tbl_capability WHERE module_name = 'my_feature';

-- Give Manager view-only
INSERT INTO tbl_role_capability (role_id, capability_id)
SELECT 3, capability_id FROM tbl_capability
WHERE module_name = 'my_feature' AND capability LIKE '%.view';
```

---

## Checklist

- [ ] Frontend module folder created with correct structure
- [ ] Module file with declarations and imports
- [ ] Routing module with lazy-loaded routes
- [ ] Main component with OnPush change detection
- [ ] Service with API methods
- [ ] Route added to `app-routing.module.ts`
- [ ] Backend controller with capability annotations
- [ ] Backend model with CRUD operations
- [ ] Database migration for new table
- [ ] Capabilities registered in migration
- [ ] Capabilities assigned to roles
- [ ] Menu entry added (if needed)

---

## Cross-References

- [Backend Architecture](../01-system-architecture/backend-architecture.md) — Controller routing, AuthHook, and capability enforcement
- [Frontend Architecture](../01-system-architecture/frontend-architecture.md) — Lazy loading, routing, and SharedModule usage
- [Folder Structure Overview](../02-folder-structure/overview.md) — Canonical locations for controllers, models, and Angular views
- [Migration System](../03-database-design/migration-system.md) — Writing and running the migration created in Step 3
- [Coding Standards](./coding-standards.md) — Naming conventions and patterns applied throughout this guide
- [Adding New APIs](./adding-apis.md) — Detailed API endpoint creation for the backend methods
- [Deployment Guide](../07-deployment-guide/) — Deploying the new module to staging and production
