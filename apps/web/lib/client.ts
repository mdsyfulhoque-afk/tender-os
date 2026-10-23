export type Json = Record<string, any>;
export type Envelope = {
  version: string;
  key_id: string;
  wrapped_key: string;
  iv: string;
  ciphertext: string;
  aad: string;
  result_mac?: string;
};
export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
  ) {
    super(message);
  }
}
export async function api<T = Json>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    credentials: "same-origin",
    ...init,
    headers: {
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
  });
  const data =
    response.status === 204
      ? {}
      : await response.json().catch(() => ({
          message: "The local service did not return a readable response.",
        }));
  if (!response.ok)
    throw new ApiError(
      data.message || "The request could not be completed.",
      data.code || "REQUEST_FAILED",
      response.status,
    );
  return data as T;
}
export function post<T = Json>(path: string, body: unknown = {}) {
  return api<T>(path, { method: "POST", body: JSON.stringify(body) });
}
export function base64(bytes: Uint8Array): string {
  let text = "";
  for (let i = 0; i < bytes.length; i += 32768)
    text += String.fromCharCode(...bytes.subarray(i, i + 32768));
  return btoa(text);
}
export function unbase64(value: string): Uint8Array {
  const text = atob(value);
  return Uint8Array.from(text, (c) => c.charCodeAt(0));
}
function buffer(bytes: Uint8Array): ArrayBuffer {
  return bytes.slice().buffer as ArrayBuffer;
}
function secureContext() {
  if (!window.isSecureContext || !window.crypto?.subtle)
    throw new Error(
      "Encryption requires HTTPS or localhost. Open this pilot on localhost.",
    );
}
export async function fingerprint(publicKey: string): Promise<string> {
  secureContext();
  const hash = await crypto.subtle.digest(
    "SHA-256",
    buffer(unbase64(publicKey)),
  );
  return Array.from(new Uint8Array(hash), (v) =>
    v.toString(16).padStart(2, "0"),
  ).join("");
}
function normalizeFingerprint(value: string) {
  return value
    .toLowerCase()
    .replace(/^sha256:/, "")
    .replace(/:/g, "");
}
export async function nodeTrust(
  node: Json,
): Promise<{ fingerprint: string; trusted: boolean }> {
  if (!node?.public_key)
    throw new Error(
      "The local private node has not published an encryption key. Start the owner node first.",
    );
  const actual = await fingerprint(node.public_key);
  if (node.fingerprint && normalizeFingerprint(node.fingerprint) !== actual)
    throw new Error(
      "The node key does not match its advertised fingerprint. Encryption is blocked.",
    );
  const pinned = localStorage.getItem("tenderos.local-node-fingerprint");
  if (pinned && pinned !== actual)
    throw new Error(
      "The private node encryption key changed. Ask the owner to verify its fingerprint before trusting a replacement.",
    );
  return { fingerprint: actual, trusted: pinned === actual };
}
export async function trustNode(node: Json) {
  const trust = await nodeTrust(node);
  localStorage.setItem("tenderos.local-node-fingerprint", trust.fingerprint);
  return trust.fingerprint;
}
export async function encryptJson(
  value: unknown,
  node: Json,
  aad: string,
): Promise<Envelope> {
  secureContext();
  const trust = await nodeTrust(node);
  if (!trust.trusted)
    throw new Error(
      "Verify and trust the local node fingerprint before sending encrypted documents.",
    );
  const recipient = await crypto.subtle.importKey(
    "spki",
    buffer(unbase64(node.public_key)),
    { name: "RSA-OAEP", hash: "SHA-256" },
    false,
    ["wrapKey"],
  );
  const key = await crypto.subtle.generateKey(
    { name: "AES-GCM", length: 256 },
    true,
    ["encrypt"],
  );
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv: buffer(iv),
      additionalData: buffer(new TextEncoder().encode(aad)),
      tagLength: 128,
    },
    key,
    buffer(new TextEncoder().encode(JSON.stringify(value))),
  );
  const wrapped = await crypto.subtle.wrapKey("raw", key, recipient, {
    name: "RSA-OAEP",
  });
  return {
    version: "pen-envelope-v0.1",
    key_id: node.key_id,
    wrapped_key: base64(new Uint8Array(wrapped)),
    iv: base64(iv),
    ciphertext: base64(new Uint8Array(ciphertext)),
    aad,
  };
}
type Recipient = {
  privateKey: CryptoKey;
  publicKey: CryptoKey;
  caseSecret: string;
};
function randomCaseSecret() {
  return base64(crypto.getRandomValues(new Uint8Array(32)));
}
async function saveRecipient(db: IDBDatabase, keyId: string, value: Recipient) {
  await new Promise<void>((resolve, reject) => {
    const transaction = db.transaction("keys", "readwrite");
    transaction.objectStore("keys").put(value, keyId);
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
    transaction.onabort = () =>
      reject(new Error("The browser could not save its private case binding."));
  });
}
async function exportRecipient(pair: Recipient) {
  return base64(
    new Uint8Array(await crypto.subtle.exportKey("spki", pair.publicKey)),
  );
}
async function caseBinding(pair: Recipient, user: Json, publicKey: string) {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    buffer(new TextEncoder().encode(publicKey)),
  );
  return {
    version: "case-binding-v0.1",
    secret: pair.caseSecret,
    actor_id: user.id,
    actor_role: user.role,
    recipient_digest: Array.from(new Uint8Array(digest), (value) =>
      value.toString(16).padStart(2, "0"),
    ).join(""),
  };
}
async function recipientDatabase(): Promise<IDBDatabase> {
  secureContext();
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("tenderos-recipient-keys", 1);
    request.onupgradeneeded = () => request.result.createObjectStore("keys");
    request.onsuccess = () => resolve(request.result);
    request.onerror = () =>
      reject(
        new Error(
          "Browser key storage is unavailable. Use a normal browser profile with IndexedDB enabled.",
        ),
      );
  });
}
async function recipient(
  userId: string,
  caseId: string,
  create: boolean,
): Promise<Recipient> {
  const db = await recipientDatabase();
  const keyId = `${userId}:${caseId}`;
  try {
    const found = await new Promise<Recipient | undefined>(
      (resolve, reject) => {
        const request = db
          .transaction("keys", "readonly")
          .objectStore("keys")
          .get(keyId);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      },
    );
    if (found) {
      if (!found.caseSecret) {
        const migrated = { ...found, caseSecret: randomCaseSecret() };
        await saveRecipient(db, keyId, migrated);
        return migrated;
      }
      if (unbase64(found.caseSecret).length !== 32)
        throw new Error(
          "The private browser case binding is damaged. Use its original browser profile or create a new empty pilot case.",
        );
      return found;
    }
    if (!create)
      throw new Error(
        "This browser profile has no private source-processing/download key for the case. Use the same account and browser profile that uploaded its sources. Cross-browser and staff handoff require future private delegation; create a new empty case for a fictional walkthrough.",
      );
    const pair = (await crypto.subtle.generateKey(
      {
        name: "RSA-OAEP",
        modulusLength: 3072,
        publicExponent: new Uint8Array([1, 0, 1]),
        hash: "SHA-256",
      },
      false,
      ["unwrapKey", "wrapKey"],
    )) as CryptoKeyPair;
    const saved = {
      privateKey: pair.privateKey,
      publicKey: pair.publicKey,
      caseSecret: randomCaseSecret(),
    };
    await saveRecipient(db, keyId, saved);
    return saved;
  } finally {
    db.close();
  }
}
export async function recipientPublicKey(
  userId: string,
  caseId: string,
): Promise<string> {
  return exportRecipient(await recipient(userId, caseId, true));
}
export async function uploadFile(
  project: Json,
  user: Json,
  node: Json,
  file: File,
  category: string,
) {
  if (file.size > 12 * 1024 * 1024)
    throw new Error(
      "Pilot file limit is 12 MiB. Split the document into smaller files.",
    );
  if (!file.size) throw new Error("This file is empty.");
  if (!/\.(pdf|docx|txt)$/i.test(file.name))
    throw new Error("Choose a PDF, DOCX or TXT document.");
  const pair = await recipient(user.id, project.id, true);
  const binding = await caseBinding(pair, user, await exportRecipient(pair));
  const slot = await post(`/projects/${project.id}/assets/reserve`, {
    category,
  });
  const aad =
    typeof slot.aad === "string" ? slot.aad : JSON.stringify(slot.aad);
  const context = JSON.parse(aad);
  if (
    context.tenant_id !== project.tenant_id ||
    context.case_id !== project.id ||
    context.service_id !== project.service_id ||
    context.asset_id !== slot.asset_id ||
    context.kind !== "ASSET"
  )
    throw new Error("The reserved upload context does not match this case.");
  if (slot.key_id !== node.key_id)
    throw new Error(
      "The encryption key changed during upload. Refresh the workspace.",
    );
  const envelope = await encryptJson(
    {
      filename: file.name,
      mime: file.type || "application/octet-stream",
      content_base64: base64(new Uint8Array(await file.arrayBuffer())),
      category,
      binding,
    },
    node,
    aad,
  );
  return api(`/projects/${project.id}/assets/${slot.asset_id}`, {
    method: "PUT",
    body: JSON.stringify({ envelope }),
  });
}
export async function submitCommand(
  project: Json,
  user: Json,
  node: Json,
  action: string,
  command: Json = {},
) {
  const details = await api(`/projects/${project.id}`);
  const current = details.project;
  if (
    !current ||
    current.id !== project.id ||
    current.tenant_id !== project.tenant_id ||
    current.service_id !== project.service_id ||
    current.version !== project.version
  )
    throw new Error(
      "The case context or source version changed. Refresh the case before processing.",
    );
  const assets = (Array.isArray(details.assets) ? details.assets : [])
    .filter((asset: Json) => asset.state === "ENCRYPTED")
    .map((asset: Json) => ({
      id: asset.id,
      sha256: asset.sha256,
      category: asset.category,
    }))
    .sort((a: Json, b: Json) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  if (
    assets.some(
      (asset: Json) =>
        typeof asset.id !== "string" ||
        typeof asset.sha256 !== "string" ||
        typeof asset.category !== "string",
    )
  )
    throw new Error(
      "The source manifest is incomplete. Refresh the case before processing.",
    );
  const pair = await recipient(user.id, project.id, assets.length === 0);
  const recipient_public_key = await exportRecipient(pair);
  const binding = await caseBinding(pair, user, recipient_public_key);
  const aad = JSON.stringify({
    tenant_id: project.tenant_id,
    case_id: project.id,
    service_id: project.service_id,
    kind: "COMMAND",
  });
  const command_envelope = await encryptJson(
    {
      ...command,
      binding,
      action,
      tenant_id: project.tenant_id,
      case_id: project.id,
      service_id: project.service_id,
      project_version: project.version,
      command_id: crypto.randomUUID(),
      expires_at: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
      assets,
      project_context: {
        title: current.title,
        bidder: current.bidder,
        issuer: current.issuer,
        deadline: current.deadline,
        version: current.version,
      },
    },
    node,
    aad,
  );
  return post(`/projects/${project.id}/jobs`, {
    action,
    command_envelope,
    recipient_public_key,
    idempotency_key: crypto.randomUUID(),
    expected_version: project.version,
  });
}
export async function decryptResult(
  job: Json,
  user: Json,
  caseId: string,
  tenantId: string,
): Promise<Json> {
  secureContext();
  const envelope = job.result_envelope as Envelope;
  if (
    !envelope ||
    envelope.version !== "pen-envelope-v0.1" ||
    envelope.key_id !== "recipient"
  )
    throw new Error("Unsupported encrypted result envelope.");
  if (
    job.case_id !== caseId ||
    job.tenant_id !== tenantId ||
    !job.snapshot_digest ||
    !job.id
  )
    throw new Error(
      "The result job identity does not match the current authorized case.",
    );
  const expected = JSON.stringify({
    tenant_id: tenantId,
    case_id: caseId,
    job_id: job.id,
    snapshot_digest: job.snapshot_digest,
    kind: "RESULT",
  });
  if (envelope.aad !== expected)
    throw new Error(
      "Result context verification failed. This result will not be displayed.",
    );
  if (typeof envelope.result_mac !== "string" || !envelope.result_mac)
    throw new Error(
      "Legacy/unverified development result; start a new analysis in original source browser profile.",
    );
  const pair = await recipient(user.id, caseId, false);
  const macKey = await crypto.subtle.importKey(
    "raw",
    buffer(unbase64(pair.caseSecret)),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"],
  );
  const macData = JSON.stringify({
    version: envelope.version,
    key_id: envelope.key_id,
    wrapped_key: envelope.wrapped_key,
    iv: envelope.iv,
    ciphertext: envelope.ciphertext,
    aad: envelope.aad,
  });
  let authentic = false;
  try {
    const signature = unbase64(envelope.result_mac);
    authentic =
      signature.length === 32 &&
      (await crypto.subtle.verify(
        "HMAC",
        macKey,
        buffer(signature),
        buffer(new TextEncoder().encode(macData)),
      ));
  } catch {
    authentic = false;
  }
  if (!authentic)
    throw new Error(
      "Private-node result authenticity verification failed. This result will not be decrypted or displayed.",
    );
  const key = await crypto.subtle.unwrapKey(
    "raw",
    buffer(unbase64(envelope.wrapped_key)),
    pair.privateKey,
    { name: "RSA-OAEP" },
    { name: "AES-GCM", length: 256 },
    false,
    ["decrypt"],
  );
  const plaintext = await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv: buffer(unbase64(envelope.iv)),
      additionalData: buffer(new TextEncoder().encode(expected)),
      tagLength: 128,
    },
    key,
    buffer(unbase64(envelope.ciphertext)),
  );
  const result = JSON.parse(new TextDecoder().decode(plaintext));
  if (
    result.case_id !== caseId ||
    result.job_id !== job.id ||
    result.snapshot_digest !== job.snapshot_digest
  )
    throw new Error(
      "Decrypted result identity does not match the frozen job snapshot.",
    );
  return result;
}
export function downloadArtifact(artifact: Json) {
  if (typeof artifact.content_base64 !== "string")
    throw new Error("This artifact does not contain downloadable content.");
  const bytes = unbase64(artifact.content_base64);
  const blob = new Blob([buffer(bytes)], {
    type: artifact.mime || "application/octet-stream",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = String(artifact.name || "TenderOS-report").replace(
    /[\\/]/g,
    "_",
  );
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
