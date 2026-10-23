import { randomBytes, randomUUID, scryptSync } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const base = path.resolve(
  process.env.LOCALAPPDATA || path.join(homedir(), ".local", "share"),
  "TenderOS",
);
if (base.startsWith(repo + path.sep) || /[\\/]OneDrive(?:[\\/]|$)/i.test(base))
  throw new Error("Local runtime must be outside Git and OneDrive.");
const platform = path.join(base, "public-platform"),
  privateRoot = path.resolve(
    process.env.TENDEROS_PRIVATE_ROOT ||
      path.join(homedir(), "TenderOS-Private", "private-engine"),
  );
if (
  privateRoot.startsWith(repo + path.sep) ||
  /[\\/]OneDrive(?:[\\/]|$)/i.test(privateRoot)
)
  throw new Error("Private engine must remain outside Git and OneDrive.");
const configFile = path.join(platform, "config.json");
mkdirSync(platform, { recursive: true, mode: 0o700 });
mkdirSync(privateRoot, { recursive: true, mode: 0o700 });
let config;
if (existsSync(configFile)) {
  config = JSON.parse(readFileSync(configFile, "utf8"));
  if (config.mode !== "PILOT_PC")
    throw new Error("Only PILOT_PC setup is available.");
  console.log(
    "Preserved existing local platform configuration and owner account.",
  );
} else {
  const password = randomBytes(24).toString("base64url"),
    salt = randomBytes(16).toString("hex");
  config = {
    mode: "PILOT_PC",
    runtime_dir: platform,
    node_token: randomBytes(48).toString("base64url"),
    owner: {
      id: randomUUID(),
      tenant_id: randomUUID(),
      name: "TenderOS Owner",
      email: "owner@tenderos.local",
      password_hash: `scrypt$${salt}$${scryptSync(password, salt, 64).toString("hex")}`,
    },
  };
  writeFileSync(configFile, JSON.stringify(config, null, 2), {
    mode: 0o600,
    flag: "wx",
  });
  writeFileSync(
    path.join(platform, "OWNER_LOGIN.txt"),
    `TenderOS owner workstation login\nURL: http://127.0.0.1:3414\nEmail: owner@tenderos.local\nPassword: ${password}\n\nPrivate local credential. Do not upload or share this file.\nThis local development account is not a hosted production identity.\n`,
    { mode: 0o600, flag: "wx" },
  );
  console.log(
    "Created local owner credentials. Password is saved in OWNER_LOGIN.txt, not printed.",
  );
}
const workerConfig = path.join(privateRoot, "worker-config.json");
if (!existsSync(workerConfig))
  writeFileSync(
    workerConfig,
    JSON.stringify(
      {
        mode: "PILOT_PC",
        broker_url: "http://127.0.0.1:3414",
        broker_instance_id: config.owner.id,
        node_token: config.node_token,
        node_id: randomUUID(),
        runtime_dir: path.join(privateRoot, "runtime"),
      },
      null,
      2,
    ),
    { mode: 0o600, flag: "wx" },
  );
console.log(`Public platform runtime: ${platform}`);
console.log(`Private engine location: ${privateRoot}`);
console.log(
  "Private engine source is provisioned separately by its owner; it is never downloaded from GitHub.",
);
console.log(
  "Payments, external inference, retrieval and public hosting remain disabled.",
);
