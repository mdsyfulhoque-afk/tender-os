import { NextRequest, NextResponse } from "next/server";
import { createPublicKey } from "node:crypto";
import {
  all,
  audit,
  config,
  hash,
  id,
  now,
  one,
  run,
  transaction,
} from "@/lib/store";
import {
  ApiError,
  checkPassword,
  fail,
  loopback,
  nodeAuth,
  publicUsers,
  register,
  sameOrigin,
  session,
  text,
  throttle,
  userFor,
} from "@/lib/security";
import {
  completeJob,
  createJob,
  createProject,
  GATES,
  jobFor,
  leasedJob,
  leaseJob,
  nodeInfo,
  projectDetails,
  projectFor,
  projectList,
  reserveAsset,
  SERVICES,
  storeAsset,
} from "@/lib/broker";
import type { Job, User } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function jsonBody(
  req: NextRequest,
  cap = 128 * 1024,
): Promise<Record<string, unknown>> {
  if (!req.headers.get("content-type")?.startsWith("application/json"))
    fail("JSON_REQUIRED", "Send JSON content.", 415);
  if (Number(req.headers.get("content-length") || 0) > cap)
    fail("PAYLOAD_TOO_LARGE", "Request is too large.", 413);
  const chunks: Uint8Array[] = [];
  let size = 0;
  if (req.body) {
    const reader = req.body.getReader();
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > cap) {
        await reader.cancel();
        fail("PAYLOAD_TOO_LARGE", "Request is too large.", 413);
      }
      chunks.push(value);
    }
  }
  let body: unknown;
  try {
    body = JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}");
  } catch {
    fail("INVALID_JSON", "Request contains invalid JSON.", 422);
  }
  if (!body || typeof body !== "object" || Array.isArray(body))
    fail("INVALID_JSON", "Request must be a JSON object.", 422);
  return body as Record<string, unknown>;
}
const out = (body: unknown, status = 200) =>
  NextResponse.json(body, { status, headers: { "Cache-Control": "no-store" } });
function withSession(user: User, status = 200) {
  const res = out({ user }, status);
  res.cookies.set("tenderos_session", session(user.id), {
    httpOnly: true,
    sameSite: "strict",
    path: "/",
    maxAge: 8 * 60 * 60,
    secure: false,
  });
  return res;
}
async function handle(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const requestId = id();
  try {
    loopback(req);
    const { path: p } = await context.params,
      route = p.join("/"),
      method = req.method;
    const isNode = p[0] === "node";
    if (isNode) nodeAuth(req);
    else if (!["GET", "HEAD"].includes(method)) sameOrigin(req);

    if (route === "health" && method === "GET")
      return out({
        status: "ok",
        product: "TenderOS",
        protocol: "pen-dev-v0.1",
        platform_id: config().owner.id,
        mode: "PILOT_PC",
        public_launch: false,
      });
    if (route === "auth/register" && method === "POST") {
      throttle("auth:register", 10, 60 * 60 * 1000);
      const body = await jsonBody(req);
      return withSession(register(body), 201);
    }
    if (route === "auth/login" && method === "POST") {
      throttle("auth:login", 30, 15 * 60 * 1000);
      const body = await jsonBody(req),
        email = text(body.email, "Email", 254, 3).toLowerCase(),
        password = text(body.password, "Password", 128, 1);
      throttle(`login:${hash(email)}`, 10, 15 * 60 * 1000);
      const stored = one<User & { password_hash: string }>(
        "SELECT * FROM users WHERE email=?",
        email,
      );
      if (!stored || !checkPassword(password, stored.password_hash))
        fail("INVALID_LOGIN", "Email or password is incorrect.", 401);
      const { password_hash, ...user } = stored;
      void password_hash;
      audit(user.tenant_id, user.id, "session_started", null);
      return withSession(user);
    }
    if (route === "auth/logout" && method === "POST") {
      const token = req.cookies.get("tenderos_session")?.value;
      if (token) run("DELETE FROM sessions WHERE token_hash=?", hash(token));
      const res = out({ signed_out: true });
      res.cookies.delete("tenderos_session");
      return res;
    }
    if (route === "bootstrap" && method === "GET") {
      const user = userFor(req, false);
      const projects = user ? projectList(user) : [];
      const caseIds = new Set(projects.map((c) => c.id));
      const jobs = user
        ? all<Job>(
            "SELECT id,tenant_id,case_id,service_id,action,state,snapshot_digest,project_version,attempts,lease_until,created_at,updated_at FROM jobs ORDER BY created_at DESC LIMIT 500",
          ).filter((j) => caseIds.has(j.case_id))
        : [];
      return out({
        user,
        projects,
        jobs,
        node: user ? nodeInfo() : { online: false },
        gates: GATES,
        mode: "PILOT_PC",
        services: SERVICES,
        version: "0.1.0",
        payments_enabled: false,
        external_retrieval: false,
      });
    }
    if (isNode) {
      const body = await jsonBody(
        req,
        route.endsWith("/complete") ? 40 * 1024 * 1024 : 128 * 1024,
      );
      if (route === "node/register" && method === "POST") {
        const nodeId = text(body.node_id, "Node ID", 100, 1),
          keyId = text(body.key_id, "Public key ID", 128, 1),
          publicKey = text(body.public_key, "Public key", 4096, 100),
          fingerprint = text(body.fingerprint, "Fingerprint", 128, 16);
        if (body.mode !== "PILOT_PC")
          fail("PILOT_ONLY", "Production node registration is disabled.", 403);
        let computed = "";
        try {
          const der = Buffer.from(publicKey, "base64"),
            key = createPublicKey({ key: der, format: "der", type: "spki" });
          if (
            key.asymmetricKeyType !== "rsa" ||
            key.asymmetricKeyDetails?.modulusLength !== 3072
          )
            fail("INVALID_KEY", "RSA-3072 development profile required.", 422);
          computed = hash(der);
        } catch {
          fail("INVALID_KEY", "Invalid node public key.", 422);
        }
        if (
          fingerprint
            .replace(/^sha256:/i, "")
            .replaceAll(":", "")
            .toLowerCase() !== computed
        )
          fail("INVALID_KEY", "Public key fingerprint mismatch.", 422);
        const prior = one<{ id: string; key_id: string; public_key: string }>(
          "SELECT id,key_id,public_key FROM nodes LIMIT 1",
        );
        if (
          prior &&
          (prior.id !== nodeId ||
            prior.key_id !== keyId ||
            prior.public_key !== publicKey)
        )
          fail(
            "KEY_ROTATION_REVIEW_REQUIRED",
            "Changing the pinned private node requires owner recovery review.",
            409,
          );
        const caps = Array.isArray(body.capabilities)
          ? body.capabilities
              .filter((c: unknown) => typeof c === "string" && c.length < 80)
              .slice(0, 20)
          : [];
        run(
          "INSERT INTO nodes VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET last_seen_at=excluded.last_seen_at,capabilities=excluded.capabilities",
          nodeId,
          keyId,
          publicKey,
          computed,
          "PILOT_PC",
          JSON.stringify(caps),
          now(),
        );
        return out({ registered: true, mode: "PILOT_PC" });
      }
      if (route === "node/lease" && method === "POST") {
        const nodeId = text(body.node_id, "Node", 100, 1);
        if (!one("SELECT id FROM nodes WHERE id=?", nodeId))
          fail("NODE_NOT_REGISTERED", "Register the private node first.", 409);
        return out(leaseJob(nodeId));
      }
      if (p[1] === "jobs" && p.length === 4 && method === "POST") {
        if (p[3] === "heartbeat") {
          const job = leasedJob(p[2], body);
          const until = new Date(Date.now() + 180_000).toISOString();
          run(
            "UPDATE jobs SET state='RUNNING',lease_until=?,updated_at=? WHERE id=?",
            until,
            now(),
            job.id,
          );
          return out({ renewed: true, lease_until: until });
        }
        if (p[3] === "complete") return out(completeJob(p[2], body));
      }
      fail("NOT_FOUND", "Node route not found.", 404);
    }

    const user = userFor(req)!;
    throttle(`user:${user.id}`, 180);
    if (route === "projects" && method === "POST")
      return out(createProject(user, await jsonBody(req)), 201);
    if (route === "projects" && method === "GET")
      return out({ projects: projectList(user) });
    if (p[0] === "projects" && p[1]) {
      const caseId = p[1];
      const project = projectFor(user, caseId);
      if (p.length === 2 && method === "GET")
        return out(projectDetails(user, caseId));
      if (p[2] === "assets" && p[3] === "reserve" && method === "POST")
        return out(reserveAsset(user, caseId, await jsonBody(req)), 201);
      if (p[2] === "assets" && p[3] && p.length === 4 && method === "PUT")
        return out(
          storeAsset(user, caseId, p[3], await jsonBody(req, 40 * 1024 * 1024)),
          201,
        );
      if (p[2] === "jobs" && method === "POST")
        return out(
          createJob(user, caseId, await jsonBody(req, 4 * 1024 * 1024)),
          202,
        );
      if (p[2] === "checkout" && method === "POST")
        fail(
          "PAYMENTS_DISABLED",
          "This is a free local development workspace. Merchant settlement and paid launch are not enabled.",
          503,
        );
      if (p[2] === "orders" && p.length === 3 && method === "POST") {
        if (!["C_MANAGED_CV", "D_PROPOSAL"].includes(project.service_id))
          fail(
            "INVALID_SERVICE",
            "Work orders are for managed CV and proposal services.",
            422,
          );
        const body = await jsonBody(req),
          orderId = id();
        // Notes are metadata only. Proprietary instructions and source content belong in encrypted job commands.
        const note = text(
          body.note || "Managed service requested",
          "Order note",
          500,
          1,
        );
        transaction(() => {
          run(
            "INSERT INTO orders VALUES (?,?,?,?,?,?,?)",
            orderId,
            project.tenant_id,
            caseId,
            user.id,
            note,
            "REQUESTED",
            now(),
          );
          audit(project.tenant_id, user.id, "work_order_requested", caseId, {
            order_id: orderId,
          });
        });
        return out({ id: orderId, state: "REQUESTED" }, 201);
      }
      if (p[2] === "orders" && p[3] && p[4] === "accept" && method === "POST") {
        if (
          user.role === "CUSTOMER" ||
          (user.role === "STAFF" && project.assigned_to !== user.id)
        )
          fail(
            "FORBIDDEN",
            "An assigned operator must accept this order.",
            403,
          );
        const changed = run(
          "UPDATE orders SET state='ACCEPTED' WHERE id=? AND case_id=? AND state='REQUESTED'",
          p[3],
          caseId,
        );
        if (!changed.changes)
          fail(
            "ORDER_STATE",
            "This work order is not awaiting acceptance.",
            409,
          );
        audit(project.tenant_id, user.id, "work_order_accepted", caseId, {
          order_id: p[3],
        });
        return out({ id: p[3], state: "ACCEPTED" });
      }
      if (p[2] === "assign" && method === "POST") {
        if (user.role !== "OWNER")
          fail("FORBIDDEN", "Owner assignment required.", 403);
        const body = await jsonBody(req),
          staffId = text(body.user_id, "Assigned operator", 100, 1);
        if (
          !one(
            "SELECT id FROM users WHERE id=? AND role IN ('OWNER','STAFF')",
            staffId,
          )
        )
          fail(
            "INVALID_OPERATOR",
            "Choose an authorized internal operator.",
            422,
          );
        run(
          "UPDATE projects SET assigned_to=?,updated_at=? WHERE id=?",
          staffId,
          now(),
          caseId,
        );
        audit(project.tenant_id, user.id, "operator_assigned", caseId, {
          user_id: staffId,
        });
        return out({ assigned_to: staffId });
      }
      if (
        ["consultations", "deletion-requests"].includes(p[2]) &&
        method === "POST"
      ) {
        const body = await jsonBody(req),
          kind = p[2] === "consultations" ? "CONSULTATION" : "DELETION";
        const note = text(
            (kind === "CONSULTATION" ? body.message : body.reason) ||
              "Requested by case owner",
            "Request note",
            1000,
            1,
          ),
          request = id();
        run(
          "INSERT INTO requests VALUES (?,?,?,?,?,?,?,?)",
          request,
          project.tenant_id,
          caseId,
          user.id,
          kind,
          note,
          "REQUESTED",
          now(),
        );
        audit(
          project.tenant_id,
          user.id,
          kind === "DELETION" ? "deletion_requested" : "consultation_requested",
          caseId,
          { request_id: request },
        );
        return out(
          {
            id: request,
            state: "REQUESTED",
            message:
              kind === "DELETION"
                ? "Request recorded. Deletion of private records and retained backups requires owner review."
                : "Consultation request recorded locally.",
          },
          201,
        );
      }
    }
    if (p[0] === "jobs" && p[1]) {
      const job = jobFor(user, p[1]);
      if (p.length === 2 && method === "GET") return out(job);
      if (p[2] === "cancel" && method === "POST") {
        const changed = run(
          "UPDATE jobs SET state='CANCELLED',lease_token=NULL,lease_until=NULL,updated_at=? WHERE id=? AND state IN ('QUEUED','LEASED','RUNNING')",
          now(),
          p[1],
        );
        if (!changed.changes)
          fail("JOB_STATE", "This job is no longer active.", 409);
        run(
          "UPDATE projects SET state='DRAFT',updated_at=? WHERE id=?",
          now(),
          job.case_id,
        );
        audit(job.tenant_id, user.id, "job_cancelled", job.case_id, {
          job_id: job.id,
        });
        return out({ job_id: job.id, state: "CANCELLED" });
      }
    }
    if (route === "operations" && method === "GET") {
      if (user.role === "CUSTOMER")
        fail("FORBIDDEN", "Internal operator access required.", 403);
      const projects = projectList(user),
        ids = new Set(projects.map((c) => c.id));
      return out({
        node: nodeInfo(),
        gates: GATES,
        projects,
        jobs: all(
          "SELECT id,tenant_id,case_id,service_id,action,state,attempts,lease_until,created_at,updated_at FROM jobs ORDER BY created_at DESC LIMIT 200",
        ).filter((j) => ids.has(String(j.case_id))),
        requests: all(
          "SELECT * FROM requests ORDER BY created_at DESC LIMIT 200",
        ).filter((r) => ids.has(String(r.case_id))),
        operators: user.role === "OWNER" ? publicUsers() : [user],
        payments: { enabled: false, state: "NOT_CONFIGURED" },
        privacy: {
          broker_payload: "CIPHERTEXT_ONLY",
          engine_location: "OWNER_COMPUTER",
          external_ai: false,
          external_retrieval: false,
        },
      });
    }
    if (route === "payments/paystation/ipn" && method === "POST")
      fail(
        "PAYMENTS_DISABLED",
        "Payment notifications cannot grant entitlement in this development edition.",
        503,
      );
    fail("NOT_FOUND", "API route not found.", 404);
  } catch (err) {
    if (err instanceof ApiError)
      return out(
        {
          code: err.code,
          message: err.message,
          request_id: requestId,
          retryable: err.status === 429 || err.status === 503,
        },
        err.status,
      );
    if (err instanceof Error && err.message === "LOCAL_SETUP_REQUIRED")
      return out(
        {
          code: "LOCAL_SETUP_REQUIRED",
          message:
            "Run npm run setup:local on the owner computer before opening this workspace.",
          request_id: requestId,
          retryable: false,
        },
        503,
      );
    console.error(
      "TenderOS API failure",
      requestId,
      err instanceof Error ? err.name : "UnknownError",
    );
    return out(
      {
        code: "SYSTEM_ERROR",
        message:
          "The local platform could not complete this action. Please retry or check owner-side logs.",
        request_id: requestId,
        retryable: true,
      },
      500,
    );
  }
}
export { handle as GET, handle as POST, handle as PUT, handle as PATCH };
