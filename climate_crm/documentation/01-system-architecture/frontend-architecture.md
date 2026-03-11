# Frontend Architecture — Angular 17 SPA

> Module: `climate/admin`
> Last updated: 2026-03-11

---

## Table of Contents

1. [Overview](#overview)
2. [Module System](#module-system)
3. [App Initialization](#app-initialization)
4. [Routing Architecture](#routing-architecture)
5. [Layout System](#layout-system)
6. [State Management](#state-management)
7. [HTTP Pipeline](#http-pipeline)
8. [Authentication & Session Management](#authentication--session-management)
9. [Real-Time Communication](#real-time-communication)
10. [File Upload](#file-upload)
11. [Internationalization & PWA](#internationalization--pwa)
12. [Cross-References](#cross-references)

---

## Overview

The frontend is an Angular 17 Single Page Application serving as the admin panel for Climate CRM. It communicates with the CodeIgniter 3 backend exclusively via JSON REST APIs and WebSocket connections. The application uses Angular Material 17 for UI components, Tailwind CSS for utility styling, and RxJS BehaviorSubjects for state management — there is no centralized store like NgRx.

| Metric | Count |
|--------|-------|
| Feature Modules | 48 (all lazy-loaded) |
| Services | 72+ |
| Shared Pipes | 21+ |
| Shared Directives | 7 |

All components use `ChangeDetectionStrategy.OnPush` with manual `cd.detectChanges()` for optimal rendering performance. Animations are provided by the shared `rispostaAnimations` collection.

---

## Module System

### Root Module

The root `AppModule` bootstraps the application with core providers for authentication, localization, Firebase, and HTTP interceptors:

```typescript
// src/app/app.module.ts

@NgModule({
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    SharedModule,
    HttpClientModule,
    TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useFactory: HttpLoaderFactory,
        deps: [HttpClient]
      }
    }),
    AppRoutingModule,
    ServiceWorkerModule.register('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerWhenStable:30000'
    })
  ],
  declarations: [AppComponent],
  providers: [
    AppConfig,
    { provide: LOCALE_ID, useValue: 'en-IN' },
    { provide: DEFAULT_CURRENCY_CODE, useValue: 'INR' },
    { provide: APP_INITIALIZER, useFactory: initializeApp, deps: [AppConfig], multi: true },
    { provide: HTTP_INTERCEPTORS, useClass: JwtInterceptor, multi: true },
    { provide: HTTP_INTERCEPTORS, useClass: ErrorInterceptor, multi: true },
    { provide: MAT_DATE_LOCALE, useValue: 'en-IN' },
    { provide: DateAdapter, useClass: MomentDateAdapter },
    provideFirebaseApp(() => firebaseInitializeApp(firebaseEnvironment.firebase)),
    provideMessaging(() => getMessaging()),
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
```

### SharedModule

The SharedModule provides common components, pipes, directives, and services used across all feature modules:

- **Layout Components**: Header, Sidebar, Footer, Breadcrumb
- **Dialog Services**: Confirm, Prompt, Loader
- **Pipes**: `hasPermission`, `relativeTime`, `safeHtml`, `orderStatus`, `rDate` (21+ total)
- **Directives**: FontSize, ScrollTo, Dropdown (7 total)
- **Services**: Auth, Theme, Layout, Navigation, Topbar

---

## App Initialization

The `APP_INITIALIZER` token ensures configuration is loaded before the application renders. The `AppConfig` class fetches runtime configuration from a JSON file and backend settings:

```typescript
// src/app/app.config.ts

export class AppConfig {
  static settings: IAppConfig;

  load() {
    const jsonFile = `assets/config/config.${environment.name}.json`;
    return new Promise<void>((resolve, reject) => {
      this.http.get(jsonFile).toPromise().then((response: IAppConfig) => {
        AppConfig.settings = response;
        // Load user details from localStorage
        AppConfig.settings.currentUserDetails = JSON.parse(
          localStorage.getItem('currentUserDetails')
        );
        resolve();
      });
    });
  }
}
```

The static `AppConfig.settings` object is the single source for API base URLs, user details, and company configuration:

```typescript
AppConfig.settings = {
  apiServer: {
    dataServer: 'http://climate.loc/index.php',  // API base URL
    serverName: 'Local'
  },
  currentUserDetails: { ... },  // From localStorage
  currentSettings: { ... },     // App settings from backend
  currentStoreDetails: { ... }  // Company info
}
```

All HTTP services use `AppConfig.settings.apiServer.dataServer` as their base URL.

---

## Routing Architecture

The router defines three layout zones: `AuthLayout` for unauthenticated pages, `AdminLayout` for the main admin panel (protected by `AuthGuard`), and `CustomerLayout` for the customer portal.

```typescript
// src/app/app-routing.module.ts

const routes: Routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: '',
    component: AuthLayoutComponent,
    children: [
      {
        path: 'sessions',
        loadChildren: () => import('./views/sessions/sessions.module')
          .then(m => m.SessionsModule),
        data: { title: 'Session' }
      },
      {
        path: 'offline',
        loadChildren: () => import('./views/offline/offline.module')
          .then(m => m.OfflineModule),
        data: { title: 'Offline', breadcrumb: 'Offline' }
      }
    ]
  },
  {
    path: '',
    component: AdminLayoutComponent,
    canActivate: [AuthGuard],
    children: [
      {
        path: 'dashboard',
        loadChildren: () => import('./views/dashboard/dashboard.module')
          .then(m => m.DashboardModule),
        data: { title: 'Dashboard', breadcrumb: 'Dashboard' },
        canActivate: [AuthGuard]
      },
      {
        path: 'accounts',
        loadChildren: () => import('./views/customers/customers.module')
          .then(m => m.CustomersModule),
        data: { title: 'Accounts', breadcrumb: 'Accounts' },
        canActivate: [AuthGuard]
      },
      // ... 48 total lazy-loaded modules
    ]
  }
];
```

### Key Routes

| Path | Module | Description |
|------|--------|-------------|
| `/dashboard` | DashboardModule | Main KPI dashboard |
| `/admindashboard` | AdminDashboardModule | Team-wide admin metrics |
| `/agentdashboard` | AgentDashboardModule | Agent personal metrics |
| `/accounts` | CustomersModule | Account management |
| `/contacts` | CustomerContactsModule | Contact management |
| `/communications` | WhatsappModule | WhatsApp chat interface |
| `/leads` | LeadsModule | Lead management |
| `/orders` | OrdersModule | Order lifecycle |
| `/invoices` | InvoicesModule | Invoice management |
| `/payments` | PaymentsModule | Payment tracking |
| `/opportunities` | OpportunityContactsModule | Sales opportunities |
| `/crmreports` | CrmReportsModule | CRM analytics and reports |
| `/users` | UsersModule | User management |
| `/roles` | RolesModule | Role and capability management |
| `/settings` | SettingsModule | System settings |

Every route includes `data` with `title` (for the browser tab) and `breadcrumb` (for breadcrumb navigation).

---

## Layout System

### AdminLayout

The primary layout wraps all authenticated pages with a sidebar, header, breadcrumb, and footer:

```
┌──────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────┐ │
│  │              HeaderComponent                     │ │
│  │  [Menu Toggle] [Search] [Notifications] [User]  │ │
│  └─────────────────────────────────────────────────┘ │
│  ┌────────┐  ┌──────────────────────────────────┐    │
│  │Sidebar │  │  BreadcrumbComponent              │    │
│  │        │  ├──────────────────────────────────┤    │
│  │ - Full │  │                                  │    │
│  │ - Comp │  │    <router-outlet>               │    │
│  │ - Close│  │    (Feature Module Content)      │    │
│  │        │  │                                  │    │
│  │ Menu   │  ├──────────────────────────────────┤    │
│  │ Items  │  │  FooterComponent                 │    │
│  └────────┘  └──────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

The sidebar has three modes managed by `LayoutService`:

| Mode | Behavior | Trigger |
|------|----------|---------|
| `full` | Full-width sidebar with icons and labels | Default for most routes |
| `compact` | Icons-only narrow sidebar | Auto-activates on `/communications` and `/shop` routes |
| `closed` | Hidden sidebar (overlay on demand) | Default on mobile (below 959px width) |

### AuthLayout

Clean layout with no sidebar or header — used exclusively for login, signup, forgot-password, and OTP verification pages.

### CustomerLayout

Customer-facing portal layout with limited navigation for external customer access.

---

## State Management

The application uses service-based reactive state with RxJS. There is no centralized store.

### Pattern 1: BehaviorSubject Services

Services expose state via BehaviorSubjects that components subscribe to:

```typescript
// src/app/shared/services/topbar.service.ts

@Injectable({ providedIn: 'root' })
export class TopbarService {
  addTrigger = new Subject<any>();
  pageTrigger = new BehaviorSubject<number>(1);
  statusTrigger = new BehaviorSubject<string>('');

  public currentPage: number = 0;
  public currentSearch: string = "";
  public dateFilter: string = "";
  public inAs: any = {};
  hasAddButton: boolean = false;
  // ...
}
```

### Pattern 2: Static Singletons

Global state accessed via static properties without subscriptions:

```typescript
// API URLs, user details, company info
AppConfig.settings.apiServer.dataServer
AppConfig.settings.currentUserDetails

// User permissions
LoginService.capabilities
```

### Pattern 3: localStorage Persistence

Session-persistent state stored in localStorage:

| Key | Content |
|-----|---------|
| `token` | JWT authentication token |
| `currentUserDetails` | User info JSON (user_id, name, role, capabilities) |
| `companyDts` | Company details |
| `timeSettings` | Timezone and date format preferences |
| `lastActivityTime` | Inactivity tracking timestamp (cross-tab sync) |
| `multiTabLogoutFlag` | Cross-tab logout signal |
| `orderListFilters` | Order list filter state |

### Pattern 4: Request Deduplication

Services implement caching to prevent duplicate in-flight HTTP requests:

```typescript
if (this.cachedCustomerObservable[id]) {
  return this.cachedCustomerObservable[id];  // Return in-flight request
}
this.cachedCustomerObservable[id] = this.http.post(url, body).pipe(
  share(),
  finalize(() => delete this.cachedCustomerObservable[id])
);
```

---

## HTTP Pipeline

### JwtInterceptor

Adds authentication headers to all outgoing requests (except config/i18n JSON files):

```typescript
// src/app/shared/helpers/jwt.interceptor.ts

intercept(request: HttpRequest<any>, next: HttpHandler) {
  if (!request.url.includes('.json')) {
    const currentUser = JSON.parse(localStorage.getItem("currentUserDetails"));
    request = request.clone({
      setHeaders: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
        InAs: localStorage.getItem("InAs") || '',
        CompanyId: currentUser?.company_id || ''
      }
    });
  }
  return next.handle(request);
}
```

### ErrorInterceptor

Centralizes HTTP error handling with session management:

```typescript
// src/app/shared/helpers/error.interceptor.ts

intercept(request: HttpRequest<any>, next: HttpHandler) {
  return next.handle(request).pipe(
    tap((event) => {
      if (event instanceof HttpResponse && event.status === 200) {
        localStorage.setItem('lastActivityTime', Date.now().toString());
      }
    }),
    catchError(err => {
      switch (err.status) {
        case 400:
          this.snackBar.open(err.statusText, 'OK');
          if (err.statusText?.includes('Session expired')
              || err.statusText?.includes('Session Change')) {
            this.clearSessionAndRedirect();
          }
          break;
        case 401:
          this.snackBar.open('Logged in on another device', 'OK');
          this.clearSessionAndRedirect();
          break;
        case 403:
          this.snackBar.open('Permission denied', 'OK');
          break;
      }
      return throwError(err);
    })
  );
}
```

---

## Authentication & Session Management

### AuthGuard

Route protection using `@auth0/angular-jwt`:

```typescript
// src/app/shared/services/auth/auth.guard.ts

canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot) {
  const token = localStorage.getItem('token');
  if (token && !this.jwtHelper.isTokenExpired(token)) {
    return true;
  }
  this.router.navigate(['/sessions/signin'], {
    queryParams: { nextUrl: state.url }
  });
  return false;
}
```

### Permission Checking in Templates

The `HasPermissionPipe` controls UI element visibility based on capabilities from the JWT payload:

```html
<button *ngIf="'customers.edit' | hasPermission">Edit</button>
<mat-tab *ngIf="'orders.create' | hasPermission" label="Orders">...</mat-tab>
```

### IdleService (Inactivity Timeout)

The `IdleService` monitors user activity and enforces server-configurable inactivity timeouts with cross-tab synchronization:

```typescript
// src/app/shared/services/idle.service.ts

@Injectable({ providedIn: 'root' })
export class IdleService {
  private readonly UPDATE_THROTTLE_MS = 30000;
  private readonly LAST_ACTIVITY_KEY = 'lastActivityTime';
  private readonly LOGOUT_FLAG_KEY = 'multiTabLogoutFlag';
  public userInactive: Subject<void> = new Subject<void>();

  constructor(private dialog: MatDialog, private router: Router) {
    this.getIdleTimeAndReminderTime();
    this.initTimers();
    this.initListeners();       // mousemove, keydown, wheel, mousedown
    this.initStorageListener(); // cross-tab sync via localStorage events
  }

  private initTimers(): void {
    this.timer = setTimeout(() => this.logoutUser(), this.idleTime * 60000);
    this.reminderTimer = setTimeout(() => this.showReminderPopup(), this.reminderTime * 60000);
  }

  private resetTimers(): void {
    clearTimeout(this.timer);
    clearTimeout(this.reminderTimer);
    this.updateLastActivityTime();  // Throttled to max once per 30 seconds
    this.initTimers();
  }
}
```

**Cross-Tab Sync**: All tabs share `lastActivityTime` via localStorage. Activity in any tab resets the timer for all tabs. Setting `multiTabLogoutFlag` triggers logout across all open tabs.

### Login Flow

```
1. User enters credentials → SigninComponent
2. LoginService.verifyLogin(credentials)
3. Backend returns: { token, user, timeSettings, capabilities }
4. Store in localStorage: token, currentUserDetails, companyDts, timeSettings
5. Register FCM token for push notifications
6. Redirect based on role:
   ├── role_id 9 (Sales Admin) → /admindashboard
   ├── role_id 4 (Sales Agent) → /agentdashboard
   └── Others → /dashboard
```

---

## Real-Time Communication

### WebSocketService

A direct WebSocket connection to the backend's `WhatsappChat` controller for live chat delivery:

```typescript
// src/app/shared/services/web-socket.service.ts

@Injectable({ providedIn: 'root' })
export class WebSocketService {
  public connection: WebSocket;
  public communicationWss = new Subject<any>();

  wssConnect() {
    this.connection = new WebSocket(environment.wssUrl);

    this.connection.onopen = (event) => {
      const joinMessage = {
        current_time: Date.now(),
        chatType: 'chatjoin',
        token: this.token,
        user_id: this.user.user_id,
      };
      this.connection.send(JSON.stringify(joinMessage));
    };

    this.connection.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.communicationWss.next(data);
    };

    this.connection.onclose = (e) => {
      if (e.code != 3001) {
        setTimeout(() => this.wssConnect(), 1000);  // Auto-reconnect
      }
    };
  }

  wssDisconnect() {
    this.connection?.close(3001);  // Intentional close — no reconnect
  }
}
```

Components subscribe to `communicationWss` to receive real-time messages, call status updates, and conversation events.

### FcmService (Push Notifications)

Firebase Cloud Messaging handles background notifications:

```typescript
// src/app/shared/services/firebase/fcm.service.ts

@Injectable({ providedIn: 'root' })
export class FcmService {
  constructor(
    private messaging: Messaging,
    private _notification: NotificationService,
    private _topbarService: TopbarService
  ) {}

  listenForMessages() {
    onMessage(this.messaging, (payload) => {
      if (payload?.notification) {
        const audio = new Audio('assets/sounds/notification.wav');
        audio.play().catch(() => {});
        this._notification.triggerNotification(
          payload.notification.title,
          payload.notification.body,
          payload.data
        );
        this._topbarService.incrementNotificationCount();
      }
    });
  }

  async getToken(): Promise<string | null> {
    const token = await getToken(this.messaging, {
      vapidKey: firebaseEnvironment.firebase.vapidKey,
    });
    return token || null;
  }
}
```

---

## File Upload

The upload flow uses S3 pre-signed URLs for direct browser-to-S3 uploads with progress tracking:

```typescript
// src/app/shared/services/upload.service.ts

@Injectable({ providedIn: 'root' })
export class UploadService {

  getUploadUrl(fileItem: FileItem) {
    const formData = new FormData();
    formData.append('extension', fileItem.file.type.replace(/.*\//, ""));
    formData.append('id', fileItem.id);
    formData.append('file_type', fileItem.file_type);
    formData.append('type', fileItem.file.type);
    return this.http.post<any>(
      AppConfig.settings.apiServer.dataServer + "/images/getUploadUrl",
      formData,
      { observe: 'events' }
    );
  }

  uploadS3File(file: File, url: string) {
    return this.http.put(url, file, {
      headers: { "Content-Type": file.type },
      reportProgress: true,
      observe: 'events'
    });
  }
}
```

**Upload Flow**:
1. Frontend → `POST /images/getUploadUrl` (file type, extension)
2. Backend generates pre-signed S3 URL and returns it
3. Frontend → `PUT` to S3 URL directly (with progress tracking)
4. Frontend → `POST /images/postImage` (confirm upload, get CDN URL)

---

## Internationalization & PWA

### Translation

The application uses `@ngx-translate` with JSON translation files:

```
Loader:  TranslateHttpLoader → /assets/i18n/{lang}.json
Template: {{ 'KEY' | translate }}
Code:     this.translate.instant('KEY')
Locale:   en-IN (Indian English)
```

### Progressive Web App

- **Service Worker**: Registered via `@angular/service-worker` with `ngsw-config.json` configuration
- **Firebase Messaging SW**: `firebase-messaging-sw.js` handles background push notifications
- **App Updater**: `AppUpdateService` checks for new versions and prompts users to reload
- **Offline Page**: `/offline` route displayed when the app is offline

---

## Cross-References

| Document | Path |
|----------|------|
| System Architecture Overview | `01-system-architecture/overview.md` |
| Backend Architecture | `01-system-architecture/backend-architecture.md` |
| Security & Auth | `01-system-architecture/security.md` |
| Communication Patterns | `01-system-architecture/communication-patterns.md` |
| API Authentication | `05-api-documentation/authentication.md` |
| Folder Structure | `02-folder-structure/overview.md` |
| Coding Standards | `08-development-guidelines/coding-standards.md` |
| Adding Modules | `08-development-guidelines/adding-modules.md` |
