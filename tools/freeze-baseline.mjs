import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import path from "node:path";

const base = path.join(
  process.env.LOCALAPPDATA || path.join(homedir(), ".local", "share"),
  "TenderOS",
  "baseline",
  "2026-10-23",
);
mkdirSync(base, { recursive: true, mode: 0o700 });
const sha = execFileSync("git", ["rev-parse", "HEAD"], {
  encoding: "utf8",
}).trim();
const entries = execFileSync("git", ["ls-tree", "-rz", "--full-tree", sha], {
  encoding: "utf8",
})
  .split("\0")
  .filter(Boolean);
const inventory = entries.map((entry) => {
  const [meta, file] = entry.split("\t");
  const [mode, type, oid] = meta.split(" ");
  return { file, mode, type, git_object_id: oid };
});
const target = path.join(base, `source-${sha}.zip`);
if (!existsSync(target))
  execFileSync("git", ["archive", "--format=zip", `--output=${target}`, sha]);
writeFileSync(
  path.join(base, "baseline.json"),
  JSON.stringify(
    {
      git_sha: sha,
      recorded_at: new Date().toISOString(),
      source_archive: target,
      source_archive_sha256: createHash("sha256")
        .update(readFileSync(target))
        .digest("hex"),
      files: inventory,
      original_app: "tenderproof_os/",
      original_data:
        "Not copied or migrated. Remains in its existing local storage.",
      release_012: "Preserved isolated; not integrated.",
    },
    null,
    2,
  ),
);
console.log(
  `Pinned ${sha}; archived and hashed ${inventory.length} tracked files outside Git.`,
);
