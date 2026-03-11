# Technologies & Dependencies

## Frontend Stack

### Core Framework

| Package | Version | Purpose |
|---------|---------|---------|
| `@angular/core` | 17.0.5 | Core Angular framework |
| `@angular/cli` | 17.0.5 | Build tooling and CLI |
| `@angular/compiler` | 17.0.5 | Template compilation |
| `@angular/router` | 17.0.5 | Client-side routing |
| `@angular/forms` | 17.0.5 | Reactive and template-driven forms |
| `@angular/animations` | 17.0.5 | Animation framework |
| `@angular/platform-browser` | 17.0.5 | Browser rendering |
| `@angular/platform-server` | 17.0.5 | Server-side rendering support |
| `@angular/ssr` | 17.0.5 | Angular SSR utilities |
| `@angular/service-worker` | 17.0.5 | PWA service worker |
| `typescript` | 5.2.2 | Type-safe JavaScript |
| `rxjs` | 7.8.0 | Reactive programming with Observables |
| `zone.js` | 0.14.2 | Angular change detection |

### UI Framework

| Package | Version | Purpose |
|---------|---------|---------|
| `@angular/material` | 17.0.2 | Material Design components |
| `@angular/cdk` | 17.0.2 | Component Dev Kit (drag-drop, overlay, etc.) |
| `@angular/flex-layout` | 15.0.0-beta.42 | Responsive flex layout directives |
| `tailwindcss` | 3.4.17 | Utility-first CSS framework |
| `@angular/google-maps` | 17.0.2 | Google Maps components |

### Data Visualization

| Package | Version | Purpose |
|---------|---------|---------|
| `chart.js` | 4.2.1 | Canvas-based charting library |
| `ng2-charts` | 4.1.1 | Angular wrapper for Chart.js |
| `ngx-echarts` | 15.0.3 | Apache ECharts integration (advanced charts) |
| `echarts` | 5.4.1 | Apache ECharts library |

### Date & Time

| Package | Version | Purpose |
|---------|---------|---------|
| `moment` | 2.24.0 | Date manipulation and formatting |
| `date-fns` | 2.29.3 | Lightweight date utility functions |
| `@angular/material-moment-adapter` | 17.0.2 | Moment.js adapter for Material datepicker |
| `angular-calendar` | 0.31.0 | Calendar UI component |
| `ngx-mat-timepicker` | 17.1.0 | Material time picker |

### Authentication & Security

| Package | Version | Purpose |
|---------|---------|---------|
| `@auth0/angular-jwt` | 5.1.2 | JWT token decoding and validation |

### Firebase & Notifications

| Package | Version | Purpose |
|---------|---------|---------|
| `firebase` | 10.10.0 | Firebase SDK |
| `@angular/fire` | 17.0.0 | Angular Firebase bindings |

### Media & Content

| Package | Version | Purpose |
|---------|---------|---------|
| `@tinymce/tinymce-angular` | 7.0.0 | Rich text editor (WYSIWYG) |
| `croppie` | 2.6.5 | Image cropping component |
| `exif-js` | 2.3.0 | EXIF image metadata reading |
| `hls.js` | 1.3.3 | HLS video streaming |
| `@videogular/ngx-videogular` | 7.0.1 | Video player component |

### Form & Validation

| Package | Version | Purpose |
|---------|---------|---------|
| `ng2-validation` | 3.9.1 | Custom form validators |

### Internationalization

| Package | Version | Purpose |
|---------|---------|---------|
| `@ngx-translate/core` | 14.0.0 | i18n translation framework |
| `@ngx-translate/http-loader` | 8.0.0 | HTTP-based translation file loader |

### UI Components

| Package | Version | Purpose |
|---------|---------|---------|
| `ngx-mat-timeline` | 1.1.2 | Timeline component |
| `canvas-confetti` | 1.9.4 | Confetti animation effects |

---

## Backend Stack

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| PHP | >= 5.3.7 | Server-side language |
| CodeIgniter 3 | 3.x | MVC web framework |
| MySQL / MariaDB | - | Relational database |
| MySQLi Driver | - | Database connection driver |

### PHP Dependencies (Composer)

| Package | Purpose |
|---------|---------|
| `firebase/php-jwt` | JWT token generation and validation (HS512) |
| `predis/predis` | Redis client for queue operations |
| `knplabs/knp-snappy` | PDF generation (uses wkhtmltopdf) |
| `takielias/codeigniter-websocket` | WebSocket server for real-time chat |
| `aws/aws-sdk-php` | AWS S3, SES, CloudFront integration |
| `google/apiclient` | Google Sheets API integration |

### Custom Libraries

| Library | File | Purpose |
|---------|------|---------|
| Risposta | `Risposta.php` | JSON encoding with numeric precision preservation |
| Firebase | `Firebase.php` | FCM push notification sending |
| Chat WebSocket | `Chat_websocket.php` | WebSocket server for real-time chat |
| Redis Queue | `LibRedisQueue.php` | Redis-based message queue operations |
| Queue Helper | `Queue_helper.php` | Background job queue management |
| Crypto | `Crypto.php` | Data encryption/decryption utilities |
| IP | `Ip.php` | IP address handling and validation |
| XLSX Writer | `XlsxWriter.php` | Excel spreadsheet generation |
| Markdown | `Markdown.php` | Markdown to HTML parsing |
| Background Process | `BackgroundProcess.php` | Background task runner |
| Telnet Client | `TelnetClient.php` | Telnet protocol communication |

### Custom Helpers

| Helper | File | Purpose |
|--------|------|---------|
| JWT Helper | `jwt_helper.php` | JWT encode/decode utility functions |
| Phone Number | `phone_number_helper.php` | Phone number parsing, country code extraction |
| Agent Assignment | `agent_assignment_helper.php` | Agent workload distribution logic |
| Handle Validation | `handle_validation_helper.php` | Contact handle (phone/email) validation |
| Filters | `filters_helper.php` | Report query filter construction |
| WebSocket | `codeigniter_websocket_helper.php` | WebSocket utility functions |

---

## Infrastructure & Services

### AWS Services

| Service | Purpose |
|---------|---------|
| **S3** | File and media storage (product images, WhatsApp media, documents) |
| **CloudFront** | Content delivery network for static assets and media |
| **SES** | Simple Email Service for transactional emails |

**CloudFront CDN URLs**:
- Production: `https://d1r95e2xq05b34.cloudfront.net`
- Media: `https://dxibg8kpmxm0e.cloudfront.net`

### Redis

| Usage | Purpose |
|-------|---------|
| Message Queue | Real-time notification delivery |
| Background Jobs | Async task processing |
| Chat Broadcasting | WebSocket message distribution |

### Firebase

| Service | Purpose |
|---------|---------|
| Cloud Messaging (FCM) | Push notifications to web/mobile |
| Service Account | Server-to-server authentication |

**Firebase Project**: `climate-naturals-india-b2b`

### WebSocket

| Environment | URL |
|-------------|-----|
| Development | `ws://localhost:8988` |
| Production | `wss://api.climatenaturals.com/chat` |

---

## External Service Integrations

### WhatsApp Business Cloud API
- **Provider**: Meta (Facebook)
- **Webhook**: `POST /whatsapp/webhookCloudApi`
- **Verification Token**: Configured in settings
- **Message Types**: Text, template, image, video, audio, document, contact, reaction

### JustDial
- **Integration Type**: API-based lead capture
- **Authentication**: API key + secret per client
- **Storage**: `tbl_justdial_credentials`, `tbl_justdial_leads`

### Facebook Leads
- **Integration Type**: Webhook-based lead form capture
- **Controller**: `FbLeads`

### Google Sheets
- **Integration Type**: Service account API
- **Purpose**: Data export and import
- **Queue**: Background processing via `SheetsQueueRunner`

### Vtransact/AWLME Payment Gateway
- **Location**: `/pg/` directory
- **Transaction Types**: Payment, Refund, Card Status Check
- **Security**: Request/response encryption via `VtransactSecurity`

---

## Build & Development Tools

### Frontend

| Tool | Purpose |
|------|---------|
| Angular CLI (`ng`) | Build, serve, test, lint |
| Webpack (via Angular CLI) | Module bundling |
| Karma | Test runner |
| Jasmine | Test framework |

**Build Commands**:
```bash
ng serve --port 4302          # Development server
ng build                      # Development build
ng build --configuration production   # Production build
ng build --configuration beta        # Beta build
```

**Build Configuration**:
- Production: Optimized, no source maps, output hashing, vendor chunks
- Budget limits: 2MB warning / 5MB error (initial), 40KB warning / 50KB error (component styles)

### Backend

| Tool | Purpose |
|------|---------|
| Composer | PHP dependency management |
| CodeIgniter Migrations | Database schema versioning |

**Migration Command**:
```bash
cd climate-api && php index.php migrate
```

---

## Environment Configuration

### Frontend Environments

| Environment | API URL Config | WebSocket | CDN |
|-------------|---------------|-----------|-----|
| Development | `config.dev.json` | `ws://localhost:8988` | CloudFront |
| Beta | `config.beta.json` | Configured per env | CloudFront |
| Production | `config.prod.json` | `wss://api.climatenaturals.com/chat` | CloudFront |

### Backend Environment Variables (`.env`)

| Variable | Purpose |
|----------|---------|
| `CI_ENV` | Environment (development/production) |
| `DBHOST` | Database host |
| `DBUSER` | Database username |
| `DBPASSWORD` | Database password |
| `DBNAME` | Database name |
| `JWT_KEY` | JWT signing key (HS512) |
| `CHAT_PORT` | WebSocket server port |
| `JUST_DIAL_NUMBER` | JustDial integration phone number |

---

## Supported Browsers

The Angular application targets modern browsers:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

PWA support enables offline capability via Service Worker.

---

## Locale & Currency

| Setting | Value |
|---------|-------|
| Locale | `en-IN` (Indian English) |
| Currency | `INR` (Indian Rupee) |
| Timezone | `Asia/Kolkata` (UTC +5:30) |
| Date Format | Moment.js format strings |
| Character Set | `utf8mb4_unicode_ci` |
