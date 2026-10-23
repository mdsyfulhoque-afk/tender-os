# TenderOS development integration contract

This public contract contains transport shapes only. The proprietary Knowledge Engine implementation, rules, prompts, model policy, source data and keys live outside this repository. Version: `pen-dev-v0.1`; execution mode: `PILOT_PC`. This is an owner workstation development build, not an approved public or paid service.

## Browser API

All routes use `/api/v1`. JSON errors: `{code,message,request_id,retryable}`. Cookie sessions require same-origin mutations. No secrets or plaintext file content may be submitted to the broker.

- `POST /auth/register {name,email,password}` creates CUSTOMER only. `POST /auth/login {email,password}`; `POST /auth/logout`; `GET /bootstrap` returns `{user,projects,jobs,node,gates,mode,services}`. Null user means signed out. First owner account is provisioned by the local setup command, never by a public role selector.
- `POST /projects {title,bidder,issuer,deadline,service_id}`; `GET /projects/:id` returns `{project,assets,jobs,events,orders}`.
- `POST /projects/:id/assets/reserve {category}` returns `{asset_id,aad,key_id}`. Categories: TENDER, AMENDMENT, BIDDER, CV, RESEARCH, DERIVED. Encrypt `{filename,mime,content_base64}` on the browser, then `PUT /projects/:id/assets/:asset_id {envelope}`. The broker holds opaque ciphertext and metadata; only the private node parses files.
- `POST /projects/:id/jobs {action,command_envelope,recipient_public_key,idempotency_key,expected_version}` creates a durable job and returns `{job_id,state,status_url}`. AAD for commands is exactly `JSON.stringify({tenant_id:project.tenant_id,case_id:project.id,service_id:project.service_id,kind:'COMMAND'})`. Actions: ANALYZE, REVIEW, MANAGED_DRAFT, FINANCIAL, RESEARCH, RELEASE. CUSTOMER may ANALYZE A/B only; internal actions require assigned STAFF or OWNER. Pilot entitlement is explicitly free and local.
- `GET /jobs/:id` returns job metadata plus `result_envelope` when available. `POST /jobs/:id/cancel` cancels queued work. `POST /projects/:id/orders {note}` requests managed service; it does not invoke internal production.
- `POST /projects/:id/consultations {message}` and `POST /projects/:id/deletion-requests {reason}` record requests. `POST /projects/:id/checkout` fails closed: payments are unavailable. Raw `/payments/paystation/ipn` never grants entitlement.
- `GET /operations` returns permitted owner/staff operations information. `POST /projects/:id/assign {user_id}` is owner-only.

## Encrypted envelope

`{version:'pen-envelope-v0.1',key_id,wrapped_key,iv,ciphertext,aad}`. Binary fields are standard base64. Candidate development interoperability profile: RSA-OAEP with SHA-256 wraps a random AES-256-GCM key; 12 random nonce bytes; UTF-8 `aad` authenticates exact context. AES ciphertext includes its 16-byte tag. Production is disabled pending independent profile, trust-root, uploader-release and recovery review. Development public-key distribution is authenticated local bootstrap plus a displayed fingerprint; it is not a signed production trust manifest.

Browser creates a per-case RSA-OAEP recipient key pair in IndexedDB; the private key is non-extractable and never sent to the broker. Public key format is base64 DER SPKI. Node result AAD is `JSON.stringify({tenant_id,case_id,job_id,snapshot_digest,kind:'RESULT'})` without spaces, in that order. Result key_id is `recipient`. Browser verifies all result AAD fields against the persisted job before displaying it. Clearing the browser profile loses its private download keys. This development release has no cross-device recovery.

### Mandatory sealed source and command binding

Each browser user/case record also holds a random 32-byte `caseSecret` in IndexedDB. It never travels in plaintext to the broker. Every encrypted asset plaintext includes `category` and `binding:{version:'case-binding-v0.1',secret,actor_id,actor_role,recipient_digest}`. `recipient_digest` is lowercase SHA-256 of the UTF-8 base64 SPKI string. Every encrypted command includes that same binding, plus the exact `action`, `tenant_id`, `case_id`, `service_id`, `project_version`, a UUID `command_id`, an ISO `expires_at` no more than 30 minutes ahead, `assets:[{id,sha256,category}]` sorted by ID, and `project_context:{title,bidder,issuer,deadline,version}`. The client obtains the current authorized case before sealing this data.

The private node requires every field, compares the recipient/action/actor/version/source manifest against the leased job, checks expiry and command replay, and verifies all asset payload bindings/categories before parsing any source. An altered broker cannot simply redirect an existing sealed command to a different result recipient or reinterpret its action/category. This is a development binding protocol, not an independently approved production signing/identity design.

Result envelopes also require `result_mac`: standard base64 HMAC-SHA256 with the decoded 32-byte case secret as key, over UTF-8 compact JSON of `{version,key_id,wrapped_key,iv,ciphertext,aad}` in exactly that order. The browser verifies this receipt before decrypting/rendering. The broker only validates its shape and never receives the MAC key. Encryption to a public recipient key alone does not authenticate who created a result; this case-bound receipt prevents the broker from forging an accepted result without the source profile's secret. It is a shared case-capability proof, not an independent signed production identity or approval.

Inputs and subsequent processing must use their initiating user/browser profile. A different staff or browser profile cannot operate on those encrypted sources without a future owner-approved private delegation mechanism. Server-side assignment alone is insufficient. Legacy development assets without this binding are rejected with `NEEDS_INPUT`; they are not silently upgraded. This restriction protects source confidentiality and is an explicit remaining multi-operator workflow requirement.

## Outbound private node API

Node authenticates using a random local bearer credential read from an owner file outside the repository. The broker must bind only to loopback in this edition.

Before sending any bearer request, the node reads unauthenticated `/api/v1/health` and requires the expected product, protocol, local mode and owner-provisioned `platform_id`. A wrong local application/installation is rejected before receiving the connector credential. This prevents accidental port collisions; production mutual authentication and signed trust distribution remain pending.

- `POST /node/register {node_id,key_id,public_key,fingerprint,mode:'PILOT_PC',capabilities:[]}` persists public key and heartbeat. Every poll refreshes node health. No proprietary capability internals.
- `POST /node/lease {node_id}` returns `{job:null}` or `{job:{id,tenant_id,case_id,service_id,action,snapshot_digest,command_envelope,recipient_public_key,lease_token,actor:{id,name,role},project:{title,bidder,issuer,deadline,version},assets:[{id,category,sha256,envelope}]}}`.
- `POST /node/jobs/:id/heartbeat {node_id,lease_token}` renews a valid lease.
- `POST /node/jobs/:id/complete {node_id,lease_token,state,result_envelope}` accepts only current lease/current snapshot. States COMPLETED, NEEDS_INPUT, INCONCLUSIVE, SYSTEM_ERROR. No plaintext diagnostics sent to broker.

Node validates envelope AAD against job/case/tenant/service/asset, stores plaintext only locally, processes fixed service actions, encrypts result JSON to recipient public key, and submits encrypted completion. Broker input snapshot includes immutable asset ciphertext digests, version, command envelope digest and recipient key. It rejects expired or stale completion. Retries retain the same immutable snapshot. Work orders do not authorize cross-case access.

## Decrypted development result

`{schema_version,case_id,job_id,snapshot_digest,service_id,readiness,mandatory_clearance,business_recommendation,summary,coverage,requirements:[],gaps:[],sources:[],cv:object|null,managed:object|null,research:object|null,financial:object|null,approval:object|null,artifacts:[],events:[],limitations:[]}`.

Requirements expose source-backed rows `{id,quote,source_id,page,clause_ref,mandatory,domain,finding_status,assurance,evidence:[],rationale,next_action}`. Artifacts are `{id,name,mime,content_base64,readiness}` and travel inside result ciphertext. Review commands include `reviews:[{requirement_id,finding_status,evidence_source_id,evidence_page,evidence_quote,rationale,assurance}]`, `coverage_reviewed:boolean`; do not assume a caller-supplied PASS is valid. RELEASE remains blocked until policy and qualified-reviewer gates are recorded. Managed/research actions are drafts unless their respective gates are satisfied. No external model or retrieval fallback is allowed.
