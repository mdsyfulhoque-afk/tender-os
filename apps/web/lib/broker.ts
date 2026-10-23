import { createPublicKey } from "node:crypto";
import { all, audit, hash, id, now, one, run, transaction } from "./store";
import { fail, text } from "./security";
import {
  SERVICE_IDS,
  type Envelope,
  type Job,
  type Project,
  type User,
} from "./types";

export const SERVICES = [
  {
    id: "A_COMPLIANCE",
    name: "Bid Compliance",
    description: "Understand requirements, evidence and gaps.",
    channel: "SELF_SERVICE",
  },
  {
    id: "B_CV_FIT",
    name: "CV Fit",
    description: "Review candidate evidence against a role.",
    channel: "SELF_SERVICE",
  },
  {
    id: "C_MANAGED_CV",
    name: "Managed CV",
    description: "Request source-backed CV drafting with staff review.",
    channel: "MANAGED",
  },
  {
    id: "D_PROPOSAL",
    name: "Managed Proposal",
    description: "Request technical and financial proposal drafting.",
    channel: "MANAGED",
  },
  {
    id: "R_RESEARCH",
    name: "Private Research",
    description: "Internal evidence workspace. External retrieval is disabled.",
    channel: "INTERNAL",
  },
];
export const GATES = [
  {
    id: "G0",
    name: "Design and owner decisions",
    state: "PENDING",
    detail:
      "Custody, policy owners, benchmark thresholds and reviewed cryptography remain open.",
  },
  {
    id: "G1A",
    name: "Private engine quality",
    state: "PENDING",
    detail:
      "Development kernel only; representative bilingual expert benchmark is not approved or executed.",
  },
  {
    id: "G1B",
    name: "Public / private integration",
    state: "DEVELOPMENT",
    detail:
      "Local encrypted transport and persisted queue; independent security and recovery assessment pending.",
  },
  {
    id: "G2",
    name: "Controlled pilot acceptance",
    state: "PENDING",
    detail: "Real-domain pilot and independent procurement review required.",
  },
  {
    id: "GS",
    name: "Dedicated owner server",
    state: "NOT_STARTED",
    detail:
      "Replacement-machine recovery, signed rollback and capacity proof required before paid launch.",
  },
  {
    id: "GA-L",
    name: "Paid public launch",
    state: "BLOCKED",
    detail:
      "Payments and public hosting are disabled. No commercial readiness is asserted.",
  },
];

export function projectFor(user: User, caseId: string): Project {
  const project = one<Project>("SELECT * FROM projects WHERE id=?", caseId);
  if (
    !project ||
    !(
      user.role === "OWNER" ||
      (user.role === "STAFF" && project.assigned_to === user.id) ||
      (project.owner_id === user.id && project.tenant_id === user.tenant_id)
    )
  )
    fail("NOT_FOUND", "Case not found.", 404);
  return project;
}
export function projectList(user: User): Project[] {
  return user.role === "OWNER"
    ? all<Project>("SELECT * FROM projects ORDER BY updated_at DESC LIMIT 200")
    : user.role === "STAFF"
      ? all<Project>(
          "SELECT * FROM projects WHERE assigned_to=? ORDER BY updated_at DESC LIMIT 200",
          user.id,
        )
      : all<Project>(
          "SELECT * FROM projects WHERE owner_id=? AND tenant_id=? ORDER BY updated_at DESC LIMIT 200",
          user.id,
          user.tenant_id,
        );
}
export function nodeInfo(): {
  online: boolean;
  key_id?: string;
  public_key?: string;
  fingerprint?: string;
  mode?: string;
  last_seen_at?: string;
  capabilities: string[];
  [key: string]: unknown;
} {
  const n = one<{
    node_id: string;
    key_id: string;
    public_key: string;
    fingerprint: string;
    mode: string;
    capabilities: string;
    last_seen_at: string;
  }>(
    "SELECT id AS node_id,key_id,public_key,fingerprint,mode,capabilities,last_seen_at FROM nodes ORDER BY last_seen_at DESC LIMIT 1",
  );
  return n
    ? {
        ...n,
        online: Date.now() - Date.parse(String(n.last_seen_at)) < 30_000,
        capabilities: JSON.parse(String(n.capabilities)),
      }
    : { online: false, mode: "PILOT_PC", capabilities: [] };
}
export function createProject(
  user: User,
  body: Record<string, unknown>,
): Project {
  const title = text(body.title, "Case title", 160, 3),
    bidder = text(body.bidder, "Bidder", 160, 2),
    issuer = text(body.issuer, "Issuer", 160, 2);
  const service = text(body.service_id, "Service", 40, 1);
  if (!SERVICE_IDS.includes(service as (typeof SERVICE_IDS)[number]))
    fail("INVALID_INPUT", "Choose a supported service.", 422);
  if (service === "R_RESEARCH" && user.role === "CUSTOMER")
    fail(
      "FORBIDDEN",
      "Research is restricted to assigned internal staff.",
      403,
    );
  const deadline = text(body.deadline || "", "Deadline", 40);
  if (deadline && !Number.isFinite(Date.parse(deadline)))
    fail("INVALID_INPUT", "Deadline is invalid.", 422);
  const project: Project = {
    id: id(),
    tenant_id: user.tenant_id,
    owner_id: user.id,
    assigned_to:
      user.role === "OWNER" || user.role === "STAFF" ? user.id : null,
    title,
    bidder,
    issuer,
    deadline,
    service_id: service as Project["service_id"],
    version: 1,
    state: "DRAFT",
    created_at: now(),
    updated_at: now(),
  };
  transaction(() => {
    run(
      "INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
      project.id,
      project.tenant_id,
      project.owner_id,
      project.assigned_to,
      title,
      bidder,
      issuer,
      deadline,
      service,
      1,
      "DRAFT",
      project.created_at,
      project.updated_at,
    );
    audit(project.tenant_id, user.id, "case_created", project.id, {
      service_id: service,
      mode: "PILOT_PC",
    });
  });
  return project;
}
export function jobsFor(project: Project): Job[] {
  return all<Job>(
    "SELECT id,tenant_id,case_id,service_id,action,state,snapshot_digest,project_version,attempts,lease_until,created_at,updated_at FROM jobs WHERE case_id=? ORDER BY created_at DESC LIMIT 100",
    project.id,
  );
}
export function projectDetails(user: User, caseId: string) {
  const project = projectFor(user, caseId);
  return {
    project,
    assets: all(
      "SELECT id,category,state,key_id,sha256,size_bytes,created_at FROM assets WHERE case_id=? ORDER BY created_at",
      caseId,
    ),
    jobs: jobsFor(project),
    events: all(
      "SELECT id,actor_id,action,details,event_hash,created_at FROM events WHERE case_id=? ORDER BY seq DESC LIMIT 200",
      caseId,
    ).map((e) => ({ ...e, details: JSON.parse(String(e.details)) })),
    orders: all(
      "SELECT * FROM orders WHERE case_id=? ORDER BY created_at DESC",
      caseId,
    ),
  };
}
const BASE64 =
  /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/;
export function validateEnvelope(
  raw: unknown,
  expectedAad: string,
  keyId?: string,
): Envelope {
  if (!raw || typeof raw !== "object" || Array.isArray(raw))
    fail("INVALID_ENVELOPE", "Encrypted envelope is required.", 422);
  const e = raw as Envelope;
  if (
    Object.keys(e).some(
      (k) =>
        ![
          "version",
          "key_id",
          "wrapped_key",
          "iv",
          "ciphertext",
          "aad",
          ...(keyId === "recipient" ? ["result_mac"] : []),
        ].includes(k),
    ) ||
    e.version !== "pen-envelope-v0.1" ||
    e.aad !== expectedAad ||
    (keyId && e.key_id !== keyId)
  )
    fail(
      "INVALID_ENVELOPE",
      "Encrypted payload does not match this case context.",
      422,
    );
  for (const field of ["wrapped_key", "iv", "ciphertext"] as const)
    if (typeof e[field] !== "string" || !BASE64.test(e[field]) || !e[field])
      fail("INVALID_ENVELOPE", "Invalid encrypted payload encoding.", 422);
  if (
    keyId === "recipient" &&
    (typeof e.result_mac !== "string" ||
      !BASE64.test(e.result_mac) ||
      Buffer.from(e.result_mac, "base64").length !== 32)
  )
    fail(
      "INVALID_RESULT_AUTH",
      "A case-bound result authentication receipt is required.",
      422,
    );
  if (
    Buffer.from(e.iv, "base64").length !== 12 ||
    Buffer.from(e.ciphertext, "base64").length < 16 ||
    Buffer.from(e.wrapped_key, "base64").length !== 384
  )
    fail("INVALID_ENVELOPE", "Invalid encryption parameters.", 422);
  if (
    e.ciphertext.length > 32 * 1024 * 1024 ||
    typeof e.key_id !== "string" ||
    e.key_id.length > 128
  )
    fail(
      "PAYLOAD_TOO_LARGE",
      "This development edition accepts files up to 12 MiB.",
      413,
    );
  return e;
}
export function reserveAsset(
  user: User,
  caseId: string,
  body: Record<string, unknown>,
) {
  const project = projectFor(user, caseId),
    n = nodeInfo();
  if (!n.online || !n.key_id)
    fail(
      "NODE_OFFLINE",
      "Start the local private engine before uploading.",
      503,
    );
  const category = text(body.category, "Document category", 24, 1);
  if (
    !["TENDER", "AMENDMENT", "BIDDER", "CV", "RESEARCH", "DERIVED"].includes(
      category,
    )
  )
    fail("INVALID_INPUT", "Choose a supported document category.", 422);
  const assetId = id(),
    keyId = String(n.key_id);
  const aad = JSON.stringify({
    tenant_id: project.tenant_id,
    case_id: caseId,
    asset_id: assetId,
    service_id: project.service_id,
    kind: "ASSET",
  });
  run(
    "INSERT INTO assets (id,tenant_id,case_id,category,state,key_id,aad,created_at) VALUES (?,?,?,?,?,?,?,?)",
    assetId,
    project.tenant_id,
    caseId,
    category,
    "UPLOAD_PENDING",
    keyId,
    aad,
    now(),
  );
  return { asset_id: assetId, aad, key_id: keyId };
}
export function storeAsset(
  user: User,
  caseId: string,
  assetId: string,
  body: Record<string, unknown>,
) {
  const project = projectFor(user, caseId);
  const asset = one<{ aad: string; key_id: string; state: string }>(
    "SELECT aad,key_id,state FROM assets WHERE id=? AND case_id=? AND tenant_id=?",
    assetId,
    caseId,
    project.tenant_id,
  );
  if (!asset) fail("NOT_FOUND", "Upload slot not found.", 404);
  if (asset.state !== "UPLOAD_PENDING")
    fail(
      "IMMUTABLE_ASSET",
      "This upload slot has already been used. Create a new version.",
      409,
    );
  const envelope = validateEnvelope(body.envelope, asset.aad, asset.key_id),
    serialized = JSON.stringify(envelope),
    digest = hash(serialized);
  transaction(() => {
    const changed = run(
      "UPDATE assets SET state='ENCRYPTED',envelope=?,sha256=?,size_bytes=? WHERE id=? AND state='UPLOAD_PENDING'",
      serialized,
      digest,
      Buffer.byteLength(serialized),
      assetId,
    );
    if (!changed.changes)
      fail("IMMUTABLE_ASSET", "This upload slot has already been used.", 409);
    run(
      "UPDATE projects SET version=version+1,state='DRAFT',updated_at=? WHERE id=?",
      now(),
      caseId,
    );
    run(
      "UPDATE jobs SET state='CANCELLED',lease_token=NULL,lease_until=NULL,updated_at=? WHERE case_id=? AND state IN ('QUEUED','LEASED','RUNNING')",
      now(),
      caseId,
    );
    audit(project.tenant_id, user.id, "source_ciphertext_received", caseId, {
      asset_id: assetId,
      ciphertext_sha256: digest,
      private_validation: "PENDING",
    });
    audit(project.tenant_id, user.id, "approval_stale", caseId, {
      reason: "Source set changed; all prior results are historical.",
    });
  });
  return {
    asset_id: assetId,
    state: "ENCRYPTED",
    sha256: digest,
    private_validation: "PENDING",
  };
}
function publicJob(job: Job & { result_envelope?: Envelope | string | null }) {
  const { result_envelope, ...metadata } = job;
  return {
    ...metadata,
    result_envelope:
      typeof result_envelope === "string"
        ? JSON.parse(result_envelope)
        : result_envelope,
  };
}
export function jobFor(user: User, jobId: string) {
  const job = one<Job>(
    "SELECT id,tenant_id,case_id,service_id,action,state,snapshot_digest,project_version,attempts,lease_until,result_envelope,created_at,updated_at FROM jobs WHERE id=?",
    jobId,
  );
  if (!job) fail("NOT_FOUND", "Job not found.", 404);
  projectFor(user, job.case_id);
  return publicJob(job);
}
export function createJob(
  user: User,
  caseId: string,
  body: Record<string, unknown>,
) {
  const project = projectFor(user, caseId),
    n = nodeInfo();
  if (!n.online || !n.key_id)
    fail(
      "NODE_OFFLINE",
      "The private engine is offline. Your documents remain saved.",
      503,
    );
  const action = text(body.action, "Action", 32, 1),
    idem = text(body.idempotency_key, "Idempotency key", 128, 8);
  if (
    ![
      "ANALYZE",
      "REVIEW",
      "MANAGED_DRAFT",
      "FINANCIAL",
      "RESEARCH",
      "RELEASE",
    ].includes(action)
  )
    fail("INVALID_ACTION", "Unsupported service action.", 422);
  if (
    user.role === "CUSTOMER" &&
    (action !== "ANALYZE" ||
      !["A_COMPLIANCE", "B_CV_FIT"].includes(project.service_id))
  )
    fail(
      "FORBIDDEN",
      "This action requires an assigned TenderOS operator.",
      403,
    );
  if (
    ["MANAGED_DRAFT", "FINANCIAL"].includes(action) &&
    !["C_MANAGED_CV", "D_PROPOSAL"].includes(project.service_id)
  )
    fail(
      "INVALID_ACTION",
      "Managed production requires a managed service case.",
      422,
    );
  if (action === "FINANCIAL" && project.service_id !== "D_PROPOSAL")
    fail(
      "INVALID_ACTION",
      "Financial drafting is available for Service D.",
      422,
    );
  if (
    action === "RESEARCH" &&
    project.service_id !== "R_RESEARCH" &&
    project.service_id !== "D_PROPOSAL"
  )
    fail(
      "INVALID_ACTION",
      "Research requires an internal research or managed proposal case.",
      422,
    );
  if (action === "RELEASE")
    fail(
      "RELEASE_GATES_PENDING",
      "Formal release is disabled until approved policy, qualified review, security and launch gates are evidenced.",
      409,
    );
  if (
    ["MANAGED_DRAFT", "FINANCIAL"].includes(action) &&
    !one("SELECT id FROM orders WHERE case_id=? AND state='ACCEPTED'", caseId)
  )
    fail(
      "WORK_ORDER_REQUIRED",
      "Accept a managed work order before starting staff production.",
      409,
    );
  const commandAad = JSON.stringify({
    tenant_id: project.tenant_id,
    case_id: caseId,
    service_id: project.service_id,
    kind: "COMMAND",
  });
  const command = validateEnvelope(
    body.command_envelope,
    commandAad,
    String(n.key_id),
  );
  const recipient = text(
    body.recipient_public_key,
    "Recipient public key",
    4096,
    100,
  );
  try {
    const k = createPublicKey({
      key: Buffer.from(recipient, "base64"),
      format: "der",
      type: "spki",
    });
    if (
      k.asymmetricKeyType !== "rsa" ||
      k.asymmetricKeyDetails?.modulusLength !== 3072
    )
      fail(
        "INVALID_RECIPIENT",
        "Recipient must use the development RSA-3072 profile.",
        422,
      );
  } catch {
    fail("INVALID_RECIPIENT", "Invalid recipient key.", 422);
  }
  const requestDigest = hash(
    JSON.stringify({
      action,
      command,
      recipient,
      version: body.expected_version,
    }),
  );
  const prior = one<{ id: string; state: string; request_digest: string }>(
    "SELECT id,state,request_digest FROM jobs WHERE tenant_id=? AND case_id=? AND idempotency_key=?",
    project.tenant_id,
    caseId,
    idem,
  );
  if (prior) {
    if (prior.request_digest !== requestDigest)
      fail(
        "IDEMPOTENCY_CONFLICT",
        "This request key belongs to a different payload.",
        409,
      );
    return {
      job_id: prior.id,
      state: prior.state,
      status_url: `/api/v1/jobs/${prior.id}`,
    };
  }
  if (body.expected_version !== project.version)
    fail(
      "STALE_CASE",
      "Documents changed. Refresh the case before continuing.",
      409,
    );
  const assets = all<{
    id: string;
    category: string;
    sha256: string;
    envelope: string;
  }>(
    "SELECT id,category,sha256,envelope FROM assets WHERE case_id=? AND state='ENCRYPTED' ORDER BY created_at,id",
    caseId,
  );
  if (!assets.length && action !== "FINANCIAL")
    fail(
      "INPUT_REQUIRED",
      "Upload source documents before requesting analysis.",
      422,
    );
  if (assets.length > 30)
    fail(
      "DOCUMENT_LIMIT",
      "This pilot supports at most 30 source documents per case.",
      422,
    );
  if (
    one(
      "SELECT id FROM jobs WHERE case_id=? AND state IN ('QUEUED','LEASED','RUNNING')",
      caseId,
    )
  )
    fail(
      "JOB_ACTIVE",
      "Wait for the current case job to finish or cancel it.",
      409,
    );
  const jobId = id(),
    stamp = now();
  const snapshot = hash(
    JSON.stringify({
      case_id: caseId,
      tenant_id: project.tenant_id,
      service_id: project.service_id,
      project_version: project.version,
      assets: assets.map((a) => ({
        id: a.id,
        sha256: a.sha256,
        category: a.category,
      })),
      command_digest: hash(JSON.stringify(command)),
      recipient_digest: hash(recipient),
    }),
  );
  transaction(() => {
    run(
      "INSERT INTO jobs (id,tenant_id,case_id,service_id,action,state,idempotency_key,request_digest,snapshot_digest,project_version,input_assets,command_envelope,recipient_public_key,actor,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
      jobId,
      project.tenant_id,
      caseId,
      project.service_id,
      action,
      "QUEUED",
      idem,
      requestDigest,
      snapshot,
      project.version,
      JSON.stringify(assets),
      JSON.stringify(command),
      recipient,
      JSON.stringify({ id: user.id, name: user.name, role: user.role }),
      stamp,
      stamp,
    );
    run(
      "UPDATE projects SET state='QUEUED',updated_at=? WHERE id=?",
      stamp,
      caseId,
    );
    audit(project.tenant_id, user.id, "job_queued", caseId, {
      job_id: jobId,
      action,
      snapshot_digest: snapshot,
      entitlement: "FREE_LOCAL_DEVELOPMENT",
    });
  });
  return {
    job_id: jobId,
    state: "QUEUED",
    status_url: `/api/v1/jobs/${jobId}`,
  };
}
export function leaseJob(nodeId: string) {
  return transaction(() => {
    run("UPDATE nodes SET last_seen_at=? WHERE id=?", now(), nodeId);
    const exhausted = all<{ id: string; tenant_id: string; case_id: string }>(
      "SELECT id,tenant_id,case_id FROM jobs WHERE state IN ('LEASED','RUNNING') AND lease_until<? AND attempts>=3",
      now(),
    );
    for (const expired of exhausted) {
      run(
        "UPDATE jobs SET state='DEAD_LETTER',lease_token=NULL,lease_until=NULL,updated_at=? WHERE id=?",
        now(),
        expired.id,
      );
      run(
        "UPDATE projects SET state='DEAD_LETTER',updated_at=? WHERE id=?",
        now(),
        expired.case_id,
      );
      audit(expired.tenant_id, nodeId, "job_dead_letter", expired.case_id, {
        job_id: expired.id,
        reason: "Lease expired after three attempts.",
      });
    }
    const job = one<Record<string, unknown>>(
      "SELECT * FROM jobs WHERE state='QUEUED' OR (state IN ('LEASED','RUNNING') AND lease_until<? AND attempts<3) ORDER BY created_at LIMIT 1",
      now(),
    );
    if (!job) return { job: null };
    const project = one<Project>(
      "SELECT * FROM projects WHERE id=?",
      String(job.case_id),
    );
    if (!project || project.version !== job.project_version) {
      run(
        "UPDATE jobs SET state='CANCELLED',updated_at=? WHERE id=?",
        now(),
        String(job.id),
      );
      return { job: null };
    }
    const token = id(),
      expiry = new Date(Date.now() + 180_000).toISOString();
    run(
      "UPDATE jobs SET state='LEASED',lease_owner=?,lease_token=?,lease_until=?,attempts=attempts+1,updated_at=? WHERE id=?",
      nodeId,
      token,
      expiry,
      now(),
      String(job.id),
    );
    audit(project.tenant_id, nodeId, "job_leased", project.id, {
      job_id: job.id,
      attempt: Number(job.attempts) + 1,
    });
    return {
      job: {
        id: job.id,
        tenant_id: job.tenant_id,
        case_id: job.case_id,
        service_id: job.service_id,
        action: job.action,
        snapshot_digest: job.snapshot_digest,
        command_envelope: JSON.parse(String(job.command_envelope)),
        recipient_public_key: job.recipient_public_key,
        lease_token: token,
        lease_until: expiry,
        actor: JSON.parse(String(job.actor)),
        project: {
          title: project.title,
          bidder: project.bidder,
          issuer: project.issuer,
          deadline: project.deadline,
          version: project.version,
        },
        assets: JSON.parse(String(job.input_assets)).map(
          (a: Record<string, unknown>) => ({
            ...a,
            envelope: JSON.parse(String(a.envelope)),
          }),
        ),
      },
    };
  });
}
export function leasedJob(jobId: string, body: Record<string, unknown>) {
  const nodeId = text(body.node_id, "Node", 100, 1),
    token = text(body.lease_token, "Lease token", 100, 1);
  const job = one<Job & { lease_owner: string; lease_token: string }>(
    "SELECT * FROM jobs WHERE id=?",
    jobId,
  );
  if (
    !job ||
    !["LEASED", "RUNNING"].includes(job.state) ||
    job.lease_owner !== nodeId ||
    job.lease_token !== token ||
    !job.lease_until ||
    job.lease_until < now()
  )
    fail("LEASE_LOST", "This job lease has expired or was superseded.", 409);
  const project = one<Project>(
    "SELECT * FROM projects WHERE id=?",
    job.case_id,
  );
  if (!project || project.version !== job.project_version)
    fail(
      "STALE_SNAPSHOT",
      "The source set changed. Completion is refused.",
      409,
    );
  run("UPDATE nodes SET last_seen_at=? WHERE id=?", now(), nodeId);
  return job;
}
export function completeJob(jobId: string, body: Record<string, unknown>) {
  return transaction(() => {
    const existing = one<{ state: string; result_envelope: string }>(
      "SELECT state,result_envelope FROM jobs WHERE id=?",
      jobId,
    );
    if (
      existing?.result_envelope &&
      existing.state === body.state &&
      existing.result_envelope === JSON.stringify(body.result_envelope)
    )
      return { job_id: jobId, state: existing.state, idempotent: true };
    const job = leasedJob(jobId, body),
      state = text(body.state, "Job state", 32, 1);
    if (
      !["COMPLETED", "NEEDS_INPUT", "INCONCLUSIVE", "SYSTEM_ERROR"].includes(
        state,
      )
    )
      fail("INVALID_STATE", "Invalid completion state.", 422);
    const aad = JSON.stringify({
      tenant_id: job.tenant_id,
      case_id: job.case_id,
      job_id: job.id,
      snapshot_digest: job.snapshot_digest,
      kind: "RESULT",
    });
    const envelope = validateEnvelope(body.result_envelope, aad, "recipient");
    run(
      "UPDATE jobs SET state=?,result_envelope=?,lease_token=NULL,lease_until=NULL,updated_at=? WHERE id=?",
      state,
      JSON.stringify(envelope),
      now(),
      jobId,
    );
    run(
      "UPDATE projects SET state=?,updated_at=? WHERE id=?",
      state === "COMPLETED" ? "ANALYSIS_AVAILABLE" : state,
      now(),
      job.case_id,
    );
    audit(job.tenant_id, String(body.node_id), "job_completed", job.case_id, {
      job_id: job.id,
      state,
      snapshot_digest: job.snapshot_digest,
    });
    return { job_id: jobId, state };
  });
}
