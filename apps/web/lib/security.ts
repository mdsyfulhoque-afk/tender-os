import { randomBytes, scryptSync, timingSafeEqual } from "node:crypto";
import type { NextRequest } from "next/server";
import { all, audit, config, hash, id, now, one, run } from "./store";
import type { User } from "./types";

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status = 400,
  ) {
    super(message);
  }
}
export function fail(code: string, message: string, status = 400): never {
  throw new ApiError(code, message, status);
}
export const text = (
  value: unknown,
  label: string,
  max = 240,
  min = 0,
): string => {
  if (
    typeof value !== "string" ||
    value.trim().length < min ||
    value.length > max ||
    /[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(value)
  )
    fail("INVALID_INPUT", `${label} is invalid.`, 422);
  return value.trim();
};
export const safeEqual = (a: string, b: string) => {
  const left = Buffer.from(a),
    right = Buffer.from(b);
  return left.length === right.length && timingSafeEqual(left, right);
};
export function hashPassword(password: string) {
  const salt = randomBytes(16).toString("hex");
  return `scrypt$${salt}$${scryptSync(password, salt, 64).toString("hex")}`;
}
export function checkPassword(password: string, stored: string) {
  const [scheme, salt, expected] = stored.split("$");
  return (
    scheme === "scrypt" &&
    !!salt &&
    !!expected &&
    safeEqual(scryptSync(password, salt, 64).toString("hex"), expected)
  );
}
export function loopback(req: NextRequest) {
  const hostname = req.nextUrl.hostname;
  if (!["localhost", "127.0.0.1", "[::1]"].includes(hostname))
    fail(
      "PILOT_LOCAL_ONLY",
      "This development platform is restricted to the owner computer.",
      403,
    );
  const host = req.headers.get("host") || "";
  if (!/^(127\.0\.0\.1|localhost|\[::1\])(?::\d+)?$/i.test(host))
    fail("PILOT_LOCAL_ONLY", "Invalid local host.", 403);
}
export function sameOrigin(req: NextRequest) {
  const origin = req.headers.get("origin");
  const fetchSite = req.headers.get("sec-fetch-site");
  const expectedOrigin = `${req.nextUrl.protocol}//${req.headers.get("host")}`;
  if (
    origin !== expectedOrigin ||
    (fetchSite && !["same-origin", "none"].includes(fetchSite))
  )
    fail(
      "ORIGIN_DENIED",
      "Use this workstation’s TenderOS page for this action.",
      403,
    );
}
export function throttle(bucket: string, max = 60, interval = 60_000) {
  const current = Date.now();
  const prior = one<{ count: number; reset_at: number }>(
    "SELECT count,reset_at FROM limits WHERE bucket=?",
    bucket,
  );
  if (!prior || prior.reset_at < current) {
    run(
      "INSERT INTO limits VALUES (?,?,?) ON CONFLICT(bucket) DO UPDATE SET count=excluded.count,reset_at=excluded.reset_at",
      bucket,
      1,
      current + interval,
    );
  } else {
    if (prior.count >= max)
      fail("RATE_LIMITED", "Too many requests. Please try again shortly.", 429);
    run("UPDATE limits SET count=count+1 WHERE bucket=?", bucket);
  }
  if (Math.random() < 0.01)
    run("DELETE FROM limits WHERE reset_at<?", current - interval);
}
export function userFor(req: NextRequest, required = true): User | null {
  const token = req.cookies.get("tenderos_session")?.value;
  const user = token
    ? one<User>(
        "SELECT u.id,u.tenant_id,u.name,u.email,u.role FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token_hash=? AND s.expires_at>?",
        hash(token),
        now(),
      )
    : undefined;
  if (!user && required)
    fail("AUTH_REQUIRED", "Please sign in to your workspace.", 401);
  return user || null;
}
export function session(userId: string) {
  const token = randomBytes(32).toString("base64url");
  run("DELETE FROM sessions WHERE expires_at<?", now());
  run(
    "INSERT INTO sessions VALUES (?,?,?)",
    hash(token),
    userId,
    new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString(),
  );
  return token;
}
export function register(body: Record<string, unknown>) {
  const email = text(body.email, "Email", 254, 3).toLowerCase();
  const name = text(body.name, "Name", 100, 2);
  const password = text(body.password, "Password", 128, 12);
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
    fail("INVALID_INPUT", "Enter a valid email address.", 422);
  if (one("SELECT id FROM users WHERE email=?", email))
    fail("ACCOUNT_EXISTS", "An account already exists. Please sign in.", 409);
  const user: User = {
    id: id(),
    tenant_id: id(),
    name,
    email,
    role: "CUSTOMER",
  };
  run(
    "INSERT INTO users (id,tenant_id,name,email,password_hash,role,created_at) VALUES (?,?,?,?,?,?,?)",
    user.id,
    user.tenant_id,
    name,
    email,
    hashPassword(password),
    "CUSTOMER",
    now(),
  );
  audit(user.tenant_id, user.id, "account_created", null, { mode: "PILOT_PC" });
  return user;
}
export function nodeAuth(req: NextRequest) {
  const expected = `Bearer ${config().node_token}`;
  if (!safeEqual(req.headers.get("authorization") || "", expected))
    fail("NODE_AUTH_REQUIRED", "Private node authentication failed.", 401);
}
export function publicUsers() {
  return all<User>(
    "SELECT id,tenant_id,name,email,role FROM users WHERE role IN ('OWNER','STAFF')",
  );
}
