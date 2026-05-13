# Frontend Development Maintenance

## 2026-05-13 Developer Status Infra Snapshot

### Changed Files
- `src/views/system/index.vue`
- `src/components/system/ServiceStatusCard.vue`
- `src/utils/systemStatus.js`

### API Contract
- Source API: `GET /api/v1/system/status`
- Newly displayed backend fields:
  - `elasticsearch.available`
  - `elasticsearch.cluster_status`
  - `elasticsearch.cluster_name`
  - `elasticsearch.node_name`
  - `elasticsearch.version`
  - `elasticsearch.number_of_nodes`
  - `elasticsearch.number_of_data_nodes`
  - `elasticsearch.active_shards`
  - `elasticsearch.unassigned_shards`
  - `elasticsearch.indices_count`
  - `elasticsearch.docs_count`
  - `elasticsearch.error`
  - `kafka.available`
  - `kafka.bootstrap_servers`
  - `kafka.brokers_count`
  - `kafka.topics_count`
  - `kafka.configured_topic.exists`
  - `kafka.configured_topic.partitions`
  - `kafka.configured_topic.replication_factor`

### UI Contract
- Elasticsearch cluster health maps to badge tones:
  - `green`: normal
  - `yellow`: needs attention
  - `red`: abnormal
  - `unknown`: unknown
- Kafka availability maps to normal/abnormal status.
- The page still keeps the original config snapshot section for raw environment values.

### Verification
```powershell
npm.cmd run build
```

Result: build passed.

## 2026-05-13 Route Access Boundary

### Changed Files
- `src/router/index.js`
- `src/layout/index.vue`
- `src/views/system/index.vue`
- `src/components/system/ServiceStatusCard.vue`
- `src/utils/systemStatus.js`

### Route Contract
- Platform pages are mounted under `http://localhost:5173/state/`.
- Temporary developer pages are mounted under `http://localhost:5173/temp/`.
- `/` redirects to `/state/`.

### Platform Routes
| Route | Page | Access |
| --- | --- | --- |
| `/state/` | Home | Sidebar |
| `/state/monitor` | Log monitor | Sidebar |
| `/state/diagnosis` | Diagnosis | Sidebar |
| `/state/results` | Results | Sidebar |

### Temporary Routes
| Route | Page | Access |
| --- | --- | --- |
| `/temp/developer` | Developer status monitor | Manual browser entry only |

### Navigation Rule
- Only `/state/` routes should be listed in `src/layout/index.vue`.
- `/temp/` routes are reserved for development, troubleshooting, or temporary validation pages.
- Do not add `/temp/` routes to platform navigation.

### Verification
```powershell
npm.cmd run build
```

Manual route check:
- Open `http://localhost:5173/state/` and confirm the platform sidebar is visible.
- Open `http://localhost:5173/temp/developer` manually and confirm the developer status monitor loads.
- Confirm the sidebar does not contain a developer status entry.

## 2026-05-13 Developer Status Page

### Changed Files
- `src/views/system/index.vue`
- `src/utils/systemStatus.js`

### API Contract
- Source API: `GET /api/v1/system/status`
- Expected backend fields currently used by the page:
  - `kafka_bootstrap_servers`
  - `kafka_topic`
  - `elasticsearch_hosts`
  - `elasticsearch_index_pattern`
- Frontend-only derived field:
  - `backend_api_status: "ok"` is added after `/system/status` succeeds.

### Backend API Card Rule
- `Backend API` is considered normal when `/api/v1/system/status` succeeds.
- The card no longer depends only on `/api/v1/health`.
- If `systemStatus.backend_api_status` is present, it has priority over `apiHealth.status`.
- If backend config fields such as `kafka_topic` are present, the page also treats that as evidence that `/system/status` was browser-readable.

### Reason
- Backend terminal logs may show `GET /api/v1/system/status 200 OK`, but the browser can still fail the Axios call when CORS headers are missing.
- The developer status page should reflect the browser-visible API state.

### Verification
```powershell
npm.cmd run build
```

Browser smoke check:
- Open `http://localhost:5173/temp/developer`.
- The `Backend API` card should display the running/normal status label.
- The status detail should display `system/status: ok`.
