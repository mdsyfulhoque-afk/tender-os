import { DatabaseSync } from "node:sqlite";
import { createHash, randomUUID } from "node:crypto";
import { mkdirSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import path from "node:path";

export interface PlatformConfig {
  mode: "PILOT_PC";
  runtime_dir: string;
  node_token: string;
  owner: {
    id: string;
    tenant_id: string;
    name: string;
    email: string;
    password_hash: string;
  };
}
const base =
  process.env.LOCALAPPDATA || path.join(homedir(), ".local", "share");
export const CONFIG_PATH =
  process.env.TENDEROS_PLATFORM_CONFIG ||
  path.join(base, "TenderOS", "public-platform", "config.json");

export function config(): PlatformConfig {
  let cfg: PlatformConfig;
  try {
    cfg = JSON.parse(
      readFileSync(/* turbopackIgnore: true */ CONFIG_PATH, "utf8"),
    );
  } catch {
    throw new Error("LOCAL_SETUP_REQUIRED");
  }
  if (
    cfg.mode !== "PILOT_PC" ||
    !cfg.runtime_dir ||
    !cfg.node_token ||
    !cfg.owner?.password_hash
  )
    throw new Error("LOCAL_SETUP_REQUIRED");
  return cfg;
}

type Params = Array<string | number | null>;
export function db(): DatabaseSync {
  const globalDb = globalThis as typeof globalThis & {
    tenderosDb?: DatabaseSync;
  };
  if (globalDb.tenderosDb) return globalDb.tenderosDb;
  const cfg = config();
  mkdirSync(cfg.runtime_dir, { recursive: true });
  const database = new DatabaseSync(
    path.join(cfg.runtime_dir, "platform.sqlite"),
  );
  database.exec(`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000;
    CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('OWNER','STAFF','CUSTOMER')),created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),expires_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,owner_id TEXT NOT NULL REFERENCES users(id),assigned_to TEXT,title TEXT NOT NULL,bidder TEXT NOT NULL,issuer TEXT NOT NULL,deadline TEXT NOT NULL,service_id TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,state TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS project_tenant ON projects(tenant_id,updated_at);
    CREATE TABLE IF NOT EXISTS assets (id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,case_id TEXT NOT NULL REFERENCES projects(id),category TEXT NOT NULL,state TEXT NOT NULL,key_id TEXT NOT NULL,aad TEXT NOT NULL,envelope TEXT,sha256 TEXT,size_bytes INTEGER,created_at TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS asset_case ON assets(case_id,state);
    CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,case_id TEXT NOT NULL REFERENCES projects(id),service_id TEXT NOT NULL,action TEXT NOT NULL,state TEXT NOT NULL,idempotency_key TEXT NOT NULL,request_digest TEXT NOT NULL,snapshot_digest TEXT NOT NULL,project_version INTEGER NOT NULL,input_assets TEXT NOT NULL,command_envelope TEXT NOT NULL,recipient_public_key TEXT NOT NULL,actor TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,lease_owner TEXT,lease_token TEXT,lease_until TEXT,result_envelope TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(tenant_id,case_id,idempotency_key));
    CREATE INDEX IF NOT EXISTS job_queue ON jobs(state,lease_until,created_at);
    CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,case_id TEXT NOT NULL REFERENCES projects(id),requested_by TEXT NOT NULL,note TEXT NOT NULL,state TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,case_id TEXT NOT NULL,actor_id TEXT NOT NULL,kind TEXT NOT NULL,note TEXT NOT NULL,state TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE NOT NULL,tenant_id TEXT NOT NULL,case_id TEXT,actor_id TEXT NOT NULL,action TEXT NOT NULL,details TEXT NOT NULL,previous_hash TEXT NOT NULL,event_hash TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS nodes (id TEXT PRIMARY KEY,key_id TEXT NOT NULL,public_key TEXT NOT NULL,fingerprint TEXT NOT NULL,mode TEXT NOT NULL,capabilities TEXT NOT NULL,last_seen_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS limits (bucket TEXT PRIMARY KEY,count INTEGER NOT NULL,reset_at INTEGER NOT NULL);
  `);
  const o = cfg.owner;
  database
    .prepare(
      "INSERT OR IGNORE INTO users (id,tenant_id,name,email,password_hash,role,created_at) VALUES (?,?,?,?,?,?,?)",
    )
    .run(o.id, o.tenant_id, o.name, o.email, o.password_hash, "OWNER", now());
  globalDb.tenderosDb = database;
  return database;
}
export function one<T = Record<string, unknown>>(
  sql: string,
  ...params: Params
): T | undefined {
  return db()
    .prepare(sql)
    .get(...params) as T | undefined;
}
export function all<T = Record<string, unknown>>(
  sql: string,
  ...params: Params
): T[] {
  return db()
    .prepare(sql)
    .all(...params) as T[];
}
export function run(sql: string, ...params: Params) {
  return db()
    .prepare(sql)
    .run(...params);
}
export function transaction<T>(fn: () => T): T {
  db().exec("BEGIN IMMEDIATE");
  try {
    const result = fn();
    db().exec("COMMIT");
    return result;
  } catch (err) {
    db().exec("ROLLBACK");
    throw err;
  }
}
export const now = () => new Date().toISOString();
export const id = () => randomUUID();
export const hash = (value: string | Buffer) =>
  createHash("sha256").update(value).digest("hex");
export function audit(
  tenant: string,
  actor: string,
  action: string,
  caseId: string | null,
  details: Record<string, unknown> = {},
) {
  const prior = one<{ event_hash: string }>(
    "SELECT event_hash FROM events WHERE tenant_id=? ORDER BY seq DESC LIMIT 1",
    tenant,
  );
  const event = {
    id: id(),
    tenant_id: tenant,
    case_id: caseId,
    actor_id: actor,
    action,
    details,
    previous_hash: prior?.event_hash || "GENESIS",
    created_at: now(),
  };
  const digest = hash(JSON.stringify(event));
  run(
    "INSERT INTO events (id,tenant_id,case_id,actor_id,action,details,previous_hash,event_hash,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
    event.id,
    tenant,
    caseId,
    actor,
    action,
    JSON.stringify(details),
    event.previous_hash,
    digest,
    event.created_at,
  );
}
