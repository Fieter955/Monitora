# Graph Report - Monitora  (2026-11-08)

## Corpus Check
- 201 files · ~151,988 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 23 file(s) not represented in the graph (top: (none) 15, .conf 3, .example 1)

## Summary
- 2458 nodes · 4235 edges · 184 communities (159 shown, 25 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 328 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9021f91c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- validate-coverage-ledger.cjs
- DeviceKind
- User
- main.py
- services/network.py
- sqlalchemy
- locations.py
- audit_docstrings.py
- Device
- deps.py
- Analysis Resource Bounds
- package.json
- scrape_configs
- Device
- test_network_visibility.py
- Template & Pola Kode Standar per Layer
- LLM Analyzer Base — Developer Guide
- perangkat/page.tsx
- peta/page.tsx
- Contoh Docstring Google Style (Bahasa Indonesia)
- Contoh TSDoc Indonesia — SI-KONSELING PRO
- validate-findings.cjs
- dns
- config.py
- environment
- 📍 Panduan Peta Lokasi & Denah Ruangan
- scrape_configs
- Icon
- collectUnitErrors
- telegram_configs
- telegram_configs
- validate-findings.test.cjs
- Kuesioner Audit Jaringan untuk Monitoring Perangkat dan Port
- api
- compilerOptions
- Vulnerability Patterns
- confirmed
- SkillSpector
- Dokumen Asesmen Keamanan Siber & Hardening Sistem Monitora
- services
- environment
- device-health-drawer.tsx
- Panduan Instalasi & Penambahan Perangkat Monitora
- route
- Pantau Infrastruktur
- Security Audit
- B.3.1: MCP Least-Privilege Analysis (LP1 -- LP4)
- B.3.2: MCP Tool-Poisoning Detection (TP1 -- TP4)
- SkillSpector v2.12.0
- 3. Implementation
- topologi/page.tsx
- rules
- Simplifying Method Calls
- Organizing Data
- Quick Start
- SkillSpector v2.10.0
- SkillSpector v2.11.0
- SkillSpector v2.11.1
- SkillSpector v2.11.2
- SkillSpector v2.5.0
- SkillSpector v2.5.1
- SkillSpector v2.5.2
- SkillSpector v2.5.3
- SkillSpector v2.6.0
- SkillSpector v2.7.0
- SkillSpector v2.7.2
- SkillSpector v2.8.0
- SkillSpector v2.8.1
- SkillSpector v2.8.2
- SkillSpector v2.9.0
- SkillSpector v2.9.1
- SkillSpector v2.9.2
- SkillSpector v2.9.3
- SkillSpector v2.9.4
- SkillSpector v2.9.5
- SkillSpector v2.9.6
- librenms
- validate-coverage-ledger.test.cjs
- environment
- providers
- Added a GitHub Pages landing page and made the repo public
- Clean Code Principles
- services/device.py
- interval
- telegraf-vsphere
- volumes
- Deployment Linux dan cPanel
- CONCISE
- Client-Side and Browser Hunting
- Cloud and Deployment Hunting
- Desktop, Mobile, and Local IPC Hunting
- Memory Safety, Binary, and Kernel Hunting
- HTTP-Protocol and Authentication Hunting
- Required content, reconstruction, and scan completeness
- services/auth.py
- gateway
- LibreNMSClient
- preflightJsonText
- Dealing with Generalization
- Composing Methods
- AI, LLM, and Agent Hunting
- ATTACK-CLASSES.md
- Data Isolation and Lifecycle Hunting
- Vulnerability Hunting
- Protocols, RPC, and Messaging Hunting
- security-audit
- Resource Exhaustion and Availability Hunting
- Skillspector Development Guide
- frontend
- Uji LibreNMS dengan perangkat fisik dari laptop Windows
- datasources
- networks
- Simplifying Conditional Expressions
- Moving Features Between Objects
- Supply Chain and Release Hunting
- Baseline / False-Positive Suppression
- bootstrap.py
- db
- librenms-rrdcached
- FakeLibreNMS
- ui-smoke.mjs
- snmp-exporter
- alertmanager
- alertmanager
- app/page.tsx
- Inference usage telemetry
- SkillSpector OpenCode Extension
- Skill Inspector
- routes/system.py
- grafana
- network-worker
- blackbox-exporter
- librenms-dispatcher
- validateDocument
- environment
- node-exporter
- 5. Skenario Pengujian Siber pada Monitora (Cyber Test Scenarios)
- next
- clean-code skill
- Code Smells — the diagnostic catalog
- Clean Code
- SkillSpector Pi Extension
- alertmanager
- prometheus
- README.md
- Refactoring Techniques — the fix catalog
- environment
- librenms-db
- librenms-redis
- Dependency Source Redirection
- 4. Architecture and graph structure
- 9. Adding or modifying analyzer nodes
- Catatan Penting & Panduan Debugging
- office_v2
- Uji perangkat fisik saat ini
- Phase 6: Produce target-neutral reports from final records
- Integrating SkillSpector
- 10. Environment and configuration
- 6. Running the workflow
- Detail perangkat uji
- Configuration
- How It Works
- Risk Scoring
- services/operations.py
- AS3_SELF_REFERENCES.md
- EVAL_DATASETS.md
- backup.sh
- pantau-infrastruktur-api

## God Nodes (most connected - your core abstractions)
1. `Device` - 72 edges
2. `User` - 53 edges
3. `DeviceKind` - 37 edges
4. `confirmed()` - 29 edges
5. `api()` - 27 edges
6. `device_health()` - 25 edges
7. `ProblemLocatorPage()` - 25 edges
8. `environment` - 24 edges
9. `PrometheusClient` - 23 edges
10. `DomainException` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Skenario 1: Broken Object Level Authorization (BOLA) & Privilege Escalation` --references--> `require_admin()`  [INFERRED]
  docs/panduan-keamanan-dan-uji-cyber.md → backend/api/deps.py
- `7. Entry Point `main.py`` --references--> `DomainException`  [INFERRED]
  .agents/skills/fastapi-backend-structure/references/layer-templates.md → backend/core/exceptions.py
- ``core/exceptions.py` (atau `core/exception.py`)` --references--> `DomainException`  [INFERRED]
  .agents/skills/fastapi-backend-structure/references/layer-templates.md → backend/core/exceptions.py
- ``services/user.py`` --references--> `DomainException`  [INFERRED]
  .agents/skills/fastapi-backend-structure/references/layer-templates.md → backend/core/exceptions.py
- ``db/base.py`` --references--> `Base`  [INFERRED]
  .agents/skills/fastapi-backend-structure/references/layer-templates.md → backend/db/base.py

## Import Cycles
- None detected.

## Communities (184 total, 25 thin omitted)

### Community 0 - "validate-coverage-ledger.cjs"
Cohesion: 0.13
Nodes (20): ATTEMPT_FIELDS, ATTEMPT_STATUSES, escapeUnsafeDiagnosticCharacters(), fs, hasValidUnicodeScalarValues(), hasVisibleProse(), path, PRIOR_STATUSES (+12 more)

### Community 1 - "DeviceKind"
Cohesion: 0.05
Nodes (48): alerts(), blackbox_discovery(), gateway_discovery(), icmp_discovery(), node_discovery(), snmp_discovery(), summary(), windows_discovery() (+40 more)

### Community 2 - "User"
Cohesion: 0.17
Nodes (15): `api/deps.py`, 4. Alur Kerja Migrasi & Refactoring (Step-by-Step), get_current_user(), get_db(), require_admin(), me(), bulk_place_devices_api(), create_device() (+7 more)

### Community 3 - "main.py"
Cohesion: 0.09
Nodes (27): 3. Standar `DomainException` & Exception Handler, Definisi di `core/exceptions.py`, Registrasi Handler di `main.py`, ConflictError, DomainException, ForbiddenError, InvalidArgumentError, NotFoundError (+19 more)

### Community 4 - "services/network.py"
Cohesion: 0.11
Nodes (48): create_manual_link(), discover_device(), discovery_state(), get_device_health(), internal_metrics(), snmp_interfaces(), sync_network(), test_connection() (+40 more)

### Community 5 - "sqlalchemy"
Cohesion: 0.21
Nodes (4): upgrade(), upgrade(), upgrade(), upgrade()

### Community 6 - "locations.py"
Cohesion: 0.14
Nodes (28): create_location(), delete_location(), floorplan_image(), list_floorplans(), list_locations(), location_devices(), update_location(), upload_floorplan() (+20 more)

### Community 7 - "audit_docstrings.py"
Cohesion: 0.07
Nodes (16): audit_backend(), collect_used_names(), get_layer(), main(), audit_file(), check_function(), function_params(), main() (+8 more)

### Community 8 - "Device"
Cohesion: 0.15
Nodes (10): hash_password(), reset_login_limits(), get_internal_metrics(), admin_client(), client(), reset_database(), viewer_client(), test_bootstrap_production_enforces_grafana_password() (+2 more)

### Community 9 - "deps.py"
Cohesion: 0.16
Nodes (9): authorize_admin(), authorize_session(), login(), logout(), ApiMessage, LoginRequest, Token, TokenPayload (+1 more)

### Community 10 - "Analysis Resource Bounds"
Cohesion: 0.06
Nodes (29): Analysis Resource Bounds, Bundle discovery and materialization, Configuring the aggregate workflow deadline, Configuring the dependency-source deadline, Configuring the static analysis deadline, Configuring the TP4 batch limit, Diagnosing incomplete referenced artifacts, Fail-closed partial behavior (+21 more)

### Community 11 - "package.json"
Cohesion: 0.07
Nodes (34): dependencies, next@16.4.1, qrcode@^1.5.4, react@19.2.8, react-dom@19.2.8, devDependencies, eslint@9.39.5, eslint-config-next@16.4.1 (+26 more)

### Community 12 - "scrape_configs"
Cohesion: 0.07
Nodes (29): alerting, alertmanagers, static_configs, environment, files, refresh_interval, global, evaluation_interval (+21 more)

### Community 13 - "Device"
Cohesion: 0.14
Nodes (26): Base, Device, DeviceObservation, NetworkPort, PortExpectation, utcnow(), DeviceIssue, add_device_to_librenms() (+18 more)

### Community 14 - "test_network_visibility.py"
Cohesion: 0.20
Nodes (6): create_access_token(), _credential_key(), decode_access_token(), decrypt_credentials(), encrypt_credentials(), test_credentials_are_encrypted_and_authenticated()

### Community 15 - "Template & Pola Kode Standar per Layer"
Cohesion: 0.07
Nodes (26): 1. Layer `core/`, 2. Layer `db/`, 3. Layer `models/`, 4. Layer `schemas/`, 5. Layer `services/`, 6. Layer `api/`, 7. Entry Point `main.py`, `api/routes/auth.py` (Contoh Router Publik & Sub-Router Internal) (+18 more)

### Community 16 - "LLM Analyzer Base — Developer Guide"
Cohesion: 0.07
Nodes (26): 1. Layered Resolution Approach, 2.1 Swappable Inference Endpoint, 2.2 Manual Specification of model_registry.yaml, 2. Open-Sourcing Plan, Appendix A: Class Hierarchy, Appendix B: Discovery-Mode Data Flow, Appendix C: Token Budget and Chunking, Appendix D: Meta-Analyzer vs Discovery Mode (+18 more)

### Community 17 - "perangkat/page.tsx"
Cohesion: 0.10
Nodes (24): AccessStep(), IdentityStep(), initialInput, kindLabels, locationPath(), PortConfig(), PortConfirmation(), SecretField() (+16 more)

### Community 18 - "peta/page.tsx"
Cohesion: 0.11
Nodes (22): buildMarkers(), descendantsOf(), DeviceGlyph(), findAncestorSite(), findFloorplanLocation(), healthLabel(), locationDepth(), locationLabels (+14 more)

### Community 19 - "Contoh Docstring Google Style (Bahasa Indonesia)"
Cohesion: 0.08
Nodes (24): 1. Docstring Modul, 2. Endpoint FastAPI (Route), 3. Fungsi Logika / Service, 4. Generator / Streaming, 5. Fungsi Tanpa Parameter / Tanpa Nilai Balik, 6. Class (Model SQLAlchemy / Schema Pydantic / Service), 7. Method di Dalam Class, Contoh Docstring Google Style (Bahasa Indonesia) (+16 more)

### Community 20 - "Contoh TSDoc Indonesia — SI-KONSELING PRO"
Cohesion: 0.08
Nodes (24): 1. Custom hook, 2. Utilitas `lib/`, 3. Tipe domain (`lib/types.ts`), 4. Komponen bersama + props, 5. Context, Anti-pola, Contoh TSDoc Indonesia — SI-KONSELING PRO, Komentar inline: sebelum → sesudah (+16 more)

### Community 21 - "validate-findings.cjs"
Cohesion: 0.06
Nodes (59): canonicalKey(), append(), encode(), codePointLength(), collect(), collectDataLimitErrors(), collectFindingSemanticErrors(), collectSchemaErrors() (+51 more)

### Community 22 - "dns"
Cohesion: 0.08
Nodes (25): preferred_ip_protocol, query_name, query_type, dns, prober, timeout, valid_rcodes, http (+17 more)

### Community 23 - "config.py"
Cohesion: 0.20
Nodes (7): run(), icmp_probe(), ProbeResult, rtsp_probe(), test_icmp_connection_test_uses_blackbox_probe(), test_rtsp_stream_url_crlf_and_scheme_rejection(), Skenario 3: Server-Side Request Forgery (SSRF) & Port Scanning Abuse

### Community 24 - "environment"
Cohesion: 0.11
Nodes (25): environment, ACCESS_TOKEN_EXPIRE_MINUTES, ADMIN_FULL_NAME, ADMIN_PASSWORD, ADMIN_USERNAME, ALLOWED_HOSTS, APP_ENV, APP_NAME (+17 more)

### Community 25 - "📍 Panduan Peta Lokasi & Denah Ruangan"
Cohesion: 0.08
Nodes (23): 1.1 Hierarki Lokasi, 1. Konsep Dasar, 1a. Buat Site, 1b. Buat Gedung, 1c. Buat Lantai, 1d. Buat Ruang-ruang, 2. Alur Kerja Lengkap, 3. Tampilan Akhir (+15 more)

### Community 26 - "scrape_configs"
Cohesion: 0.08
Nodes (26): alerting, alertmanagers, static_configs, files, global, evaluation_interval, scrape_interval, refresh_interval (+18 more)

### Community 27 - "Icon"
Cohesion: 0.24
Nodes (12): ReportsPage(), DeviceLabelPage(), locationPath(), AppShell(), navigation, PageHeader(), Icon(), IconName (+4 more)

### Community 28 - "collectUnitErrors"
Cohesion: 0.27
Nodes (18): canonicalCoverageId(), collectUnitErrors(), encodeCanonicalRef(), hasOwn(), hasValidSemanticFields(), isCanonicalRef(), isObject(), isOwnedArtifactPath() (+10 more)

### Community 29 - "telegram_configs"
Cohesion: 0.10
Nodes (20): global, resolve_timeout, inhibit_rules, equal, source_matchers, target_matchers, receivers, name (+12 more)

### Community 30 - "telegram_configs"
Cohesion: 0.10
Nodes (20): global, resolve_timeout, inhibit_rules, equal, source_matchers, target_matchers, receivers, name (+12 more)

### Community 31 - "validate-findings.test.cjs"
Cohesion: 0.11
Nodes (11): LIMITS, assert, errorsFor(), fs, os, path, rejectMutation(), { spawnSync } (+3 more)

### Community 32 - "Kuesioner Audit Jaringan untuk Monitoring Perangkat dan Port"
Cohesion: 0.10
Nodes (19): A. Identitas instalasi, B. Gambaran jalur jaringan, C. DHCP, IP, dan segmentasi jaringan, Cabang di belakang hub/unmanaged switch, D. Inventaris perangkat jaringan, E. Pemetaan switch, hub, dan kabel, F. Access point dan Wi-Fi, G. Lokasi dan denah dua lantai (+11 more)

### Community 33 - "api"
Cohesion: 0.22
Nodes (11): DevicesPage(), remove(), DeviceWizard(), finish(), saveAndDiscover(), secret(), testConnection(), locationName() (+3 more)

### Community 34 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 35 - "Vulnerability Patterns"
Cohesion: 0.11
Nodes (18): Anti-Refusal (3 patterns), Behavioral AST (9 patterns), Data Exfiltration (4 patterns), Excessive Agency (5 patterns), MCP Least Privilege (4 patterns), MCP Tool Poisoning (4 patterns), Memory Poisoning (3 patterns), Output Handling (3 patterns) (+10 more)

### Community 36 - "confirmed"
Cohesion: 0.24
Nodes (16): Structured hunter result, Cost budget, Coverage and prior runs, Full audit planning, Run profiles and scope, confirmed(), evidence(), needsValidation() (+8 more)

### Community 37 - "SkillSpector"
Cohesion: 0.12
Nodes (17): Contributing, Development, Documentation, Example Output, Features, License, Limitations, Live Vulnerability Lookups (SC4) (+9 more)

### Community 38 - "Dokumen Asesmen Keamanan Siber & Hardening Sistem Monitora"
Cohesion: 0.12
Nodes (17): 1.1 Jaminan Keamanan untuk Klien & Manajemen, 1. Ringkasan Eksekutif (Executive Summary), 2. Metodologi Pengujian Siber Internasional & Nasional, 3. Dekomposisi Arsitektur & Batas Keamanan (*Perimeter Isolation*), 4.1 Fitur & Mekanisme yang Terbukti AMAN (Built-in Defenses), 4.2 Kondisi BAHAYA & Titik Rawan (Threat Hazards & Misconfigurations), 4. Matriks Evaluasi: Apa Saja yang AMAN vs BAHAYA, 6. Prosedur & Alat Bantu Pengujian Siber (Tooling & Execution) (+9 more)

### Community 39 - "services"
Cohesion: 0.22
Nodes (8): command, image, network_mode, restart, volumes, name, services, librenms-rrd-init

### Community 40 - "environment"
Cohesion: 0.21
Nodes (16): CACHE_DRIVER, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_TIMEOUT, DB_USER, DISPATCHER_NODE_ID (+8 more)

### Community 41 - "device-health-drawer.tsx"
Cohesion: 0.29
Nodes (10): DeviceHealthDrawer(), expectationLabel(), formatDate(), getGrafanaDeviceUrl(), healthLabels, PortRow(), summaryFor(), formatBits() (+2 more)

### Community 42 - "Panduan Instalasi & Penambahan Perangkat Monitora"
Cohesion: 0.13
Nodes (14): BAGIAN 1: Instalasi Server Utama (Linux Monitoring), BAGIAN 2: Pasang Agen di Linux Client (Target Linux), BAGIAN 3: Pasang Agen di Windows Client (Target Windows), BAGIAN 4: Menambahkan Perangkat ke Aplikasi Monitora (UI Walkthrough), BAGIAN 5: Melihat Grafik & Hasil Monitoring, Langkah-langkah:, Langkah-langkah:, Langkah-langkah: (+6 more)

### Community 43 - "route"
Cohesion: 0.13
Nodes (14): global, resolve_timeout, inhibit_rules, equal, source_matchers, target_matchers, receivers, name (+6 more)

### Community 44 - "Pantau Infrastruktur"
Cohesion: 0.13
Nodes (15): Agen pada VM Windows, Alur penggunaan, Arsitektur, Cara perangkat saat ini terhubung, Development tanpa Docker, Keamanan dan UI, Menjalankan secara lokal, Model instalasi terpusat (+7 more)

### Community 45 - "Security Audit"
Cohesion: 0.14
Nodes (14): Anti-patterns, Core principles, Full audit setup, Full audit workflow, Operating modes, Platform terminology, Recommend the smallest effective source fix, Require a boundary and result (+6 more)

### Community 46 - "B.3.1: MCP Least-Privilege Analysis (LP1 -- LP4)"
Cohesion: 0.14
Nodes (13): 1. Background, 2. Architecture, 3. Capability Detection, 4. Permission Mapping, 5. Rules, 6. Interaction Between Rules, 7. Test Fixtures, 8. Limitations (+5 more)

### Community 47 - "B.3.2: MCP Tool-Poisoning Detection (TP1 -- TP4)"
Cohesion: 0.14
Nodes (13): 1. Background, 2. Architecture, 3. Rules, 4. Detection Coverage Matrix, 5. Test Fixtures, 6. Framework Alignment, 7. Limitations, B.3.2: MCP Tool-Poisoning Detection (TP1 -- TP4) (+5 more)

### Community 48 - "SkillSpector v2.12.0"
Cohesion: 0.14
Nodes (13): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+5 more)

### Community 49 - "3. Implementation"
Cohesion: 0.14
Nodes (13): 1. Background, 2. Solution — OSV.dev API, 3.1 Architecture, 3.2 Key files, 3.3 Design decisions, 3.4 What stays static, 3.5 What was removed, 3. Implementation (+5 more)

### Community 50 - "topologi/page.tsx"
Cohesion: 0.17
Nodes (10): DeviceSelect(), layoutNodes(), ManualLinkDrawer(), nodeAbbreviation(), Point, PortSelect(), TopologyPage(), formatPercent() (+2 more)

### Community 51 - "rules"
Cohesion: 0.14
Nodes (13): description, summary, groups, name, rules, dependency, scope, severity (+5 more)

### Community 52 - "Simplifying Method Calls"
Cohesion: 0.15
Nodes (13): Add Parameter / Remove Parameter, Introduce Parameter Object ★, Parameterize Method, Preserve Whole Object, Remove Setting Method / Hide Method, Rename Method ★, Replace Constructor with Factory Method, Replace Error Code with Exception ★ (+5 more)

### Community 53 - "Organizing Data"
Cohesion: 0.15
Nodes (13): Change Uni- ↔ Bidirectional Association, Change Value to Reference / Reference to Value, Duplicate Observed Data, Encapsulate Collection, Encapsulate Field, Organizing Data, Replace Array with Object, Replace Data Value with Object (+5 more)

### Community 54 - "Quick Start"
Cohesion: 0.15
Nodes (13): Basic Usage, Batch Scanning, Comparing MCP Registry snapshots, Docker (no Python required), Explicit scan scope, Installation, LLM Analysis, MCP Server (+5 more)

### Community 55 - "SkillSpector v2.10.0"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 56 - "SkillSpector v2.11.0"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 57 - "SkillSpector v2.11.1"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 58 - "SkillSpector v2.11.2"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 59 - "SkillSpector v2.5.0"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 60 - "SkillSpector v2.5.1"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 61 - "SkillSpector v2.5.2"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 62 - "SkillSpector v2.5.3"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 63 - "SkillSpector v2.6.0"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 64 - "SkillSpector v2.7.0"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 65 - "SkillSpector v2.7.2"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 66 - "SkillSpector v2.8.0"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 67 - "SkillSpector v2.8.1"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 68 - "SkillSpector v2.8.2"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 69 - "SkillSpector v2.9.0"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 70 - "SkillSpector v2.9.1"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 71 - "SkillSpector v2.9.2"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 72 - "SkillSpector v2.9.3"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 73 - "SkillSpector v2.9.4"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 74 - "SkillSpector v2.9.5"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 75 - "SkillSpector v2.9.6"
Cohesion: 0.15
Nodes (12): Added, Breaking Changes and Migration, Changed, Deprecations, Fixed, Highlights, Known Limitations, References (+4 more)

### Community 76 - "librenms"
Cohesion: 0.15
Nodes (13): librenms-db, librenms-redis, librenms-rrdcached, condition, depends_on, image, networks, ports (+5 more)

### Community 77 - "validate-coverage-ledger.test.cjs"
Cohesion: 0.13
Nodes (12): LIMITS, archivedAttempt(), assert, fs, localCheck(), os, path, sourceCheck() (+4 more)

### Community 78 - "environment"
Cohesion: 0.15
Nodes (13): GF_ANALYTICS_CHECK_FOR_PLUGIN_UPDATES, GF_ANALYTICS_CHECK_FOR_UPDATES, GF_ANALYTICS_REPORTING_ENABLED, GF_AUTH_ANONYMOUS_ENABLED, GF_AUTH_ANONYMOUS_HIDE_VERSION, GF_AUTH_ANONYMOUS_ORG_ROLE, GF_PLUGINS_PREINSTALL_DISABLED, GF_SECURITY_ADMIN_PASSWORD (+5 more)

### Community 79 - "providers"
Cohesion: 0.15
Nodes (12): apiVersion, foldersFromFilesStructure, path, providers, allowUiUpdates, disableDeletion, folder, name (+4 more)

### Community 80 - "Added a GitHub Pages landing page and made the repo public"
Cohesion: 0.17
Nodes (11): Added a GitHub Pages landing page and made the repo public, Changelog — 2026-06-09, Created the `clean-code` agent skill, Note, Sources, Verification, Verification (real, via headless Chrome screenshots), What (+3 more)

### Community 81 - "Clean Code Principles"
Cohesion: 0.17
Nodes (12): 10. Fail loudly, not silently, 1. Intention-revealing names, 2. Functions do one thing, at one level of abstraction, 3. Flatten with guard clauses; avoid arrow-shaped code, 4. Replace magic numbers and strings with named constants, 5. DRY — every piece of knowledge has one home, 6. Use explaining variables and queries instead of dense expressions, 7. Comments: explain *why*, never *what* (+4 more)

### Community 82 - "services/device.py"
Cohesion: 0.27
Nodes (12): DuplicateDataError, UnprocessableEntityError, CredentialProfile, bulk_place_devices(), create_device(), delete_device(), list_credential_profiles(), list_devices() (+4 more)

### Community 83 - "interval"
Cohesion: 0.49
Nodes (11): healthcheck, healthcheck, healthcheck, healthcheck, interval, retries, start_period, test (+3 more)

### Community 84 - "telegraf-vsphere"
Cohesion: 0.17
Nodes (12): VSPHERE_INSECURE_SKIP_VERIFY, VSPHERE_PASSWORD, VSPHERE_URL, VSPHERE_USERNAME, telegraf-vsphere, environment, expose, image (+4 more)

### Community 85 - "volumes"
Cohesion: 0.22
Nodes (9): volumes, alertmanager_data, grafana_data, librenms_data, librenms_db_data, librenms_rrd_data, librenms_rrd_journal, postgres_data (+1 more)

### Community 86 - "Deployment Linux dan cPanel"
Cohesion: 0.17
Nodes (12): Aktivasi LibreNMS, Alert Telegram, Backup dan pemulihan, Checklist sebelum go-live, Deployment Linux dan cPanel, HTTPS dan firewall, Integrasi ESXi opsional, Monitoring Windows, MikroTik, dan ISP (+4 more)

### Community 87 - "CONCISE"
Cohesion: 0.18
Nodes (10): Before / After, Benchmarks, Commands, CONCISE, Configuration, How it works, Install on any Agent Skills compatible tool, Install the full plugin (Claude Code only) (+2 more)

### Community 88 - "Client-Side and Browser Hunting"
Cohesion: 0.18
Nodes (10): Client-Side and Browser Hunting, Core discipline (include in every agent prompt for this domain), Cross-origin messaging and network attack classes (subagent_type: `general`), Cross-site information leak classes (subagent_type: `general`), DOM and object-state attack classes (subagent_type: `general`), Service-worker and browser-storage attack classes (subagent_type: `general`), UI-redress and navigation attack classes (subagent_type: `general`), Universal moves (apply across the above) (+2 more)

### Community 89 - "Cloud and Deployment Hunting"
Cohesion: 0.18
Nodes (10): Cloud and Deployment Hunting, Configuration and secret lifecycle attack classes (subagent_type: `general`), Container and orchestration attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Ingress, network, and control-plane attack classes (subagent_type: `general`), Managed storage, events, and edge attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+2 more)

### Community 90 - "Desktop, Mobile, and Local IPC Hunting"
Cohesion: 0.18
Nodes (10): Application-state and device-lifecycle attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Deep-link, callback, and navigation attack classes (subagent_type: `general`), Desktop, Mobile, and Local IPC Hunting, Local IPC and exported-component attack classes (subagent_type: `general`), Privileged-helper and local-file attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+2 more)

### Community 91 - "Memory Safety, Binary, and Kernel Hunting"
Cohesion: 0.18
Nodes (10): Binary loading and runtime attack classes (subagent_type: `general`), Bounds, integer, and representation attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), FFI and ABI attack classes (subagent_type: `general`), Kernel and privileged-interface attack classes (subagent_type: `general`), Lifetime, type, and concurrency attack classes (subagent_type: `general`), Memory Safety, Binary, and Kernel Hunting, Universal moves (apply across the above) (+2 more)

### Community 92 - "HTTP-Protocol and Authentication Hunting"
Cohesion: 0.18
Nodes (10): API-key and mTLS attack classes (subagent_type: `general`), Browser-session attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Federated-identity attack classes (subagent_type: `general`), HTTP framing and cache attack classes (subagent_type: `general`), HTTP-Protocol and Authentication Hunting, MFA, passkey, and account-transition attack classes (subagent_type: `general`), Universal moves (apply across the above) (+2 more)

### Community 93 - "Required content, reconstruction, and scan completeness"
Cohesion: 0.18
Nodes (9): Passive documentation images, Algorithm and trust boundaries, Bounds and cancellation, Observable decisions and exact public behavior, Required bytes and decoding, Required content, reconstruction, and scan completeness, Review critique and remaining limits, Singleton reconstruction and provenance (+1 more)

### Community 94 - "services/auth.py"
Cohesion: 0.27
Nodes (6): InvalidCredentialsError, verify_password(), authenticate_user(), check_rate_limit(), record_login_failure(), record_login_success()

### Community 95 - "gateway"
Cohesion: 0.18
Nodes (11): frontend, grafana, condition, depends_on, image, networks, ports, restart (+3 more)

### Community 97 - "preflightJsonText"
Cohesion: 0.40
Nodes (11): JsonStructureError, preflightJsonText(), beginContainer(), beginString(), beginValue(), closeContainer(), countValue(), currentContainer() (+3 more)

### Community 98 - "Dealing with Generalization"
Cohesion: 0.20
Nodes (10): Collapse Hierarchy, Dealing with Generalization, Extract Interface, Extract Subclass, Extract Superclass, Form Template Method ★, Pull Up Method / Field / Constructor Body, Push Down Method / Field (+2 more)

### Community 99 - "Composing Methods"
Cohesion: 0.20
Nodes (10): Composing Methods, Extract Method ★, Extract Variable ★, Inline Method, Inline Temp, Remove Assignments to Parameters, Replace Method with Method Object, Replace Temp with Query ★ (+2 more)

### Community 100 - "AI, LLM, and Agent Hunting"
Cohesion: 0.20
Nodes (9): AI, LLM, and Agent Hunting, Context, retrieval, and memory attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), MCP and sub-agent trust classes (subagent_type: `general`), Output and disclosure attack classes (subagent_type: `general`), Tool and action attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 101 - "ATTACK-CLASSES.md"
Cohesion: 0.22
Nodes (7): Attack Classes, Attack classes — choose and split based on Phase 1, Architecture summary and companion selection, Deterministic coverage ledger, Phase 1: Map the source and plan coverage, Prior-run input, Reconnaissance

### Community 102 - "Data Isolation and Lifecycle Hunting"
Cohesion: 0.20
Nodes (9): Core discipline (include in every agent prompt for this domain), Data Isolation and Lifecycle Hunting, Deletion, revocation, and lifecycle attack classes (subagent_type: `general`), Derived-data and disclosure attack classes (subagent_type: `general`), Export, backup, restore, and migration attack classes (subagent_type: `general`), Tenant and object-isolation attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 103 - "Vulnerability Hunting"
Cohesion: 0.20
Nodes (9): Core hunting method — include in every hunter prompt, Core validation rules — include in every hunter prompt, Coverage-critic waves, Local validation boundaries, Parent consolidation and ledger update, Phase 2: Run coverage-led hunting waves, Promotion procedure — copy this promotion procedure verbatim into every hunter prompt, Required hunter prompt (+1 more)

### Community 104 - "Protocols, RPC, and Messaging Hunting"
Cohesion: 0.20
Nodes (9): Broker and queue isolation attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Framing, schema, and interpretation attack classes (subagent_type: `general`), Protocols, RPC, and Messaging Hunting, Replay, ordering, and transaction attack classes (subagent_type: `general`), RPC identity and authorization attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 105 - "security-audit"
Cohesion: 0.20
Nodes (9): Contact, Design principles, Files, Installation, License, Requirements, security-audit, Usage (+1 more)

### Community 106 - "Resource Exhaustion and Availability Hunting"
Cohesion: 0.20
Nodes (9): Computational amplification attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Failure and recovery attack classes (subagent_type: `general`), Quota and scheduling attack classes (subagent_type: `general`), Resource accumulation attack classes (subagent_type: `general`), Resource Exhaustion and Availability Hunting, Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 107 - "Skillspector Development Guide"
Cohesion: 0.20
Nodes (10): 11. Linting and formatting, 12. Quick reference, 1. Overview, 2. Prerequisites and setup, 3. Make targets, 5. Package layout, 7. Testing, 8. Data models (+2 more)

### Community 109 - "frontend"
Cohesion: 0.20
Nodes (10): context, target, NEXT_PUBLIC_APP_NAME, NODE_ENV, build, environment, expose, networks (+2 more)

### Community 110 - "Uji LibreNMS dengan perangkat fisik dari laptop Windows"
Cohesion: 0.20
Nodes (10): Aktivasi LibreNMS dan discovery Monitora, Alamat lab, Kesetaraan dengan deployment ESXi, Konfigurasi perangkat, Konfigurasi Windows, Kriteria lulus, Matriks uji kondisi jaringan, Preflight dari Windows dan container (+2 more)

### Community 111 - "datasources"
Cohesion: 0.20
Nodes (9): apiVersion, datasources, access, editable, isDefault, name, type, uid (+1 more)

### Community 112 - "networks"
Cohesion: 0.29
Nodes (7): internal, internal, networks, edge, egress, internal, monitoring

### Community 113 - "Simplifying Conditional Expressions"
Cohesion: 0.22
Nodes (9): Consolidate Conditional Expression, Consolidate Duplicate Conditional Fragments, Decompose Conditional ★, Introduce Assertion, Introduce Null Object, Remove Control Flag, Replace Conditional with Polymorphism ★, Replace Nested Conditional with Guard Clauses ★ (+1 more)

### Community 114 - "Moving Features Between Objects"
Cohesion: 0.22
Nodes (9): Extract Class ★, Hide Delegate, Inline Class, Introduce Foreign Method, Introduce Local Extension, Move Field, Move Method ★, Moving Features Between Objects (+1 more)

### Community 115 - "Supply Chain and Release Hunting"
Cohesion: 0.22
Nodes (8): CI and automation attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Dependency and build-input attack classes (subagent_type: `general`), Release and update attack classes (subagent_type: `general`), Supply Chain and Release Hunting, Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here), When to use this file

### Community 116 - "Baseline / False-Positive Suppression"
Cohesion: 0.22
Nodes (9): Baseline / False-Positive Suppression, Baseline file format, CLI, `fingerprints` — exact suppression, How it fits the pipeline, Migrating version 1 baselines, Quick start, Recommended workflow (+1 more)

### Community 117 - "bootstrap.py"
Cohesion: 0.14
Nodes (17): bootstrap(), demo_link_key(), has_legacy_demo_server(), seed_demo_network(), get_settings(), Settings, NetworkLink, test_bootstrap_does_not_seed_demo_devices_by_default() (+9 more)

### Community 118 - "db"
Cohesion: 0.22
Nodes (9): environment, image, networks, restart, volumes, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER (+1 more)

### Community 119 - "librenms-rrdcached"
Cohesion: 0.22
Nodes (9): librenms-rrd-init, condition, depends_on, image, networks, restart, tmpfs, volumes (+1 more)

### Community 122 - "snmp-exporter"
Cohesion: 0.22
Nodes (9): SNMP_COMMUNITY, snmp-exporter, command, environment, expose, image, networks, restart (+1 more)

### Community 123 - "alertmanager"
Cohesion: 0.22
Nodes (8): networks, secrets, volumes, secrets, telegram_bot_token, services, alertmanager, file

### Community 124 - "alertmanager"
Cohesion: 0.22
Nodes (8): networks, secrets, volumes, secrets, telegram_bot_token, services, alertmanager, file

### Community 125 - "app/page.tsx"
Cohesion: 0.34
Nodes (10): AlertsPage(), AlertRow(), DashboardPage(), internetTitle(), SummaryCard(), EmptyState(), MetricBar(), StatusBadge() (+2 more)

### Community 126 - "Inference usage telemetry"
Cohesion: 0.25
Nodes (7): Cache and total-token semantics, Downstream handoff, Inference usage telemetry, JSON contract, Missing usage and fail-closed integrations, Model provenance, Privacy and trust boundary

### Community 127 - "SkillSpector OpenCode Extension"
Cohesion: 0.25
Nodes (8): Basic scan, Install, LLM-backed analysis, Remove, Requirements, SkillSpector OpenCode Extension, Tool parameters, Unit tests

### Community 128 - "Skill Inspector"
Cohesion: 0.25
Nodes (7): Goal, Manual Fallback, Operating Rules, Report Style, Review Workflow, Score Interpretation, Skill Inspector

### Community 129 - "routes/system.py"
Cohesion: 0.50
Nodes (3): capabilities(), SystemCapabilities, get_system_capabilities()

### Community 130 - "grafana"
Cohesion: 0.12
Nodes (17): build, depends_on, expose, networks, restart, condition, db, prometheus (+9 more)

### Community 131 - "network-worker"
Cohesion: 0.25
Nodes (8): condition, backend, build, command, depends_on, networks, restart, network-worker

### Community 132 - "blackbox-exporter"
Cohesion: 0.25
Nodes (8): cap_add, command, expose, image, networks, restart, volumes, blackbox-exporter

### Community 133 - "librenms-dispatcher"
Cohesion: 0.25
Nodes (8): librenms, condition, depends_on, image, networks, restart, volumes, librenms-dispatcher

### Community 134 - "validateDocument"
Cohesion: 0.67
Nodes (4): createErrorList(), preflightDocument(), errorsFor(), validateDocument()

### Community 135 - "environment"
Cohesion: 0.25
Nodes (8): FLUSH_DEAD_DATA_INTERVAL, LOG_LEVEL, PGID, PUID, WRITE_JITTER, WRITE_THREADS, WRITE_TIMEOUT, environment

### Community 136 - "node-exporter"
Cohesion: 0.25
Nodes (8): command, expose, image, networks, pid, restart, volumes, node-exporter

### Community 137 - "5. Skenario Pengujian Siber pada Monitora (Cyber Test Scenarios)"
Cohesion: 0.25
Nodes (8): 5. Skenario Pengujian Siber pada Monitora (Cyber Test Scenarios), Skenario 1: Broken Object Level Authorization (BOLA) & Privilege Escalation, Skenario 2: Injeksi Kueri SQL (SQLi) & OS Command Injection, Skenario 4: Brute-Force Resilience & Credential Tampering Test, Skenario 5: Network Perimeter & Port Leakage Audit, Skenario 6: Exporter Spoofing & Sniffing Protection Audit, Skenario 7: Denial of Service (DoS) & Resource Starvation Resilience, Skenario 8: Enkripsi Kredensial Database At-Rest Verification

### Community 138 - "next"
Cohesion: 0.17
Nodes (6): metadata, LoginPage(), User, nextConfig, next, react

### Community 139 - "clean-code skill"
Cohesion: 0.29
Nodes (6): clean-code skill, Install, License, Source & credit, What's inside, When it triggers

### Community 140 - "Code Smells — the diagnostic catalog"
Cohesion: 0.29
Nodes (7): Bloaters, Change Preventers, Code Smells — the diagnostic catalog, Couplers, Dispensables, How to use this catalog, Object-Orientation Abusers

### Community 141 - "Clean Code"
Cohesion: 0.29
Nodes (7): Clean Code, References (load on demand), Rules of engagement (non-negotiable), The refactoring loop, What "clean" means (the target you refactor toward), When to refactor (and when not to), Workflow for a whole-codebase cleanup

### Community 142 - "SkillSpector Pi Extension"
Cohesion: 0.29
Nodes (7): Basic scan, Install, LLM-backed analysis, Remove, Requirements, SkillSpector Pi Extension, Tool parameters

### Community 143 - "alertmanager"
Cohesion: 0.29
Nodes (7): command, expose, image, networks, restart, volumes, alertmanager

### Community 145 - "prometheus"
Cohesion: 0.29
Nodes (7): command, expose, image, networks, restart, volumes, prometheus

### Community 150 - "environment"
Cohesion: 0.33
Nodes (6): MARIADB_DATABASE, MARIADB_PASSWORD, MARIADB_ROOT_PASSWORD, MARIADB_USER, TZ, environment

### Community 151 - "librenms-db"
Cohesion: 0.33
Nodes (6): command, image, networks, restart, volumes, librenms-db

### Community 152 - "librenms-redis"
Cohesion: 0.33
Nodes (6): command, image, networks, restart, tmpfs, librenms-redis

### Community 155 - "Dependency Source Redirection"
Cohesion: 0.40
Nodes (4): Dependency Source Redirection, Evidence, Supported ecosystems and surfaces, Trust model

### Community 156 - "4. Architecture and graph structure"
Cohesion: 0.40
Nodes (5): 4. Architecture and graph structure, Flow diagram, Graph, Nodes, State

### Community 157 - "9. Adding or modifying analyzer nodes"
Cohesion: 0.40
Nodes (5): 9. Adding or modifying analyzer nodes, Node signature, Placeholder analyzers, Registering an analyzer, Static pattern analyzers

### Community 158 - "Catatan Penting & Panduan Debugging"
Cohesion: 0.40
Nodes (4): 1. Sisi Server (Linux/Ubuntu & Docker), 2. Sisi Target (Windows Server), Catatan Penting & Panduan Debugging, Dokumentasi Instalasi & Troubleshooting Monitora

### Community 159 - "office_v2"
Cohesion: 0.40
Nodes (4): auths, office_v2, community, version

### Community 160 - "Uji perangkat fisik saat ini"
Cohesion: 0.40
Nodes (5): Arti status perangkat, Hasil preflight yang telah dicapai, ICMP dan SNMP, Mendaftarkan perangkat ke Monitora, Uji perangkat fisik saat ini

### Community 162 - "Phase 6: Produce target-neutral reports from final records"
Cohesion: 0.50
Nodes (4): `FINDINGS-DETAIL.md`, `NEEDS-VALIDATION.md`, Phase 6: Produce target-neutral reports from final records, `REPORT.md`

### Community 163 - "Integrating SkillSpector"
Cohesion: 0.50
Nodes (4): Exit codes, Integrating SkillSpector, Machine-readable output, Recommended gate mapping

### Community 164 - "10. Environment and configuration"
Cohesion: 0.50
Nodes (4): 10. Environment and configuration, Constants, token budgets, and LLM, .env, Live provider tests

### Community 165 - "6. Running the workflow"
Cohesion: 0.50
Nodes (4): 6. Running the workflow, CLI, LangGraph dev server (primary for development), Programmatic

### Community 168 - "Detail perangkat uji"
Cohesion: 0.50
Nodes (4): Detail perangkat uji, Perangkat kedua, Perangkat ketiga, Perangkat pertama

### Community 169 - "Configuration"
Cohesion: 0.67
Nodes (3): CLI Options, Configuration, Environment Variables

### Community 170 - "How It Works"
Cohesion: 0.67
Nodes (3): How It Works, Stage 1: Static Analysis, Stage 2: LLM Semantic Analysis (Optional)

### Community 171 - "Risk Scoring"
Cohesion: 0.67
Nodes (3): Risk Scoring, Score Calculation, Severity Levels

### Community 172 - "services/operations.py"
Cohesion: 0.28
Nodes (4): list_problems(), ProblemLocatorRead, list_problems(), location_path()

## Knowledge Gaps
- **1 isolated node(s):** `pantau-infrastruktur-api`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1380 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `api()` connect `api` to `User`, `device-health-drawer.tsx`, `next`, `B.3.1: MCP Least-Privilege Analysis (LP1 -- LP4)`, `Template & Pola Kode Standar per Layer`, `perangkat/page.tsx`, `peta/page.tsx`, `topologi/page.tsx`, `Icon`, `app/page.tsx`?**
  _High betweenness centrality (0.203) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `Device` (e.g. with `bulk_place_devices_api()` and `create_device()`) actually correct?**
  _`Device` has 41 INFERRED edges - model-reasoned connections that need verification._
- **What connects `pantau-infrastruktur-api` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `validate-coverage-ledger.cjs` be split into smaller, more focused modules?**
  _Cohesion score 0.12987012987012986 - nodes in this community are weakly interconnected._
- **Why does `4. Alur Kerja Migrasi & Refactoring (Step-by-Step)` connect `User` to `api`, `main.py`, `Device`, `Template & Pola Kode Standar per Layer`?**
  _High betweenness centrality (0.188) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `User` (e.g. with `get_current_user()` and `require_admin()`) actually correct?**
  _`User` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Should `DeviceKind` be split into smaller, more focused modules?**
  _Cohesion score 0.05003734129947722 - nodes in this community are weakly interconnected._