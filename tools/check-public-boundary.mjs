import { execFileSync } from "node:child_process";
import { readFileSync, statSync } from "node:fs";
import path from "node:path";

// Inspect the exact index bytes that Git will commit, not just working files.
const staged = execFileSync(
  "git",
  ["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
  { encoding: "utf8" },
)
  .split("\0")
  .filter(Boolean);
const prohibited =
  /(^|\/)(private[-_]engine|knowledge[-_]engine|model[-_]weights|embeddings|runtime|node_modules|\.next)(\/|$)|(^|\/)(HNSK_[^/]*|TenderOS_(Knowledge_Engine|Private_Engine|G0_|v1\.[34]_)[^/]*)\.(docx|zip|pdf)$|(^|\/)extracted_bangla\.txt$|\.(pem|key|sqlite|sqlite3|db|safetensors|gguf|onnx)$/i;
const secretPatterns = [
  /-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----/,
  /\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}/,
  /"node_token"\s*:\s*"[A-Za-z0-9_-]{24,}"/,
  /"password_hash"\s*:\s*"scrypt\$/,
];
const failures = [];
for (const file of staged) {
  if (
    prohibited.test(file) ||
    /TenderOS_v1\.4_PRD_TRD_Documentation_Pack\//.test(file)
  ) {
    failures.push(`${file}: private/runtime boundary`);
    continue;
  }
  const blob = execFileSync("git", ["show", `:${file}`], {
    maxBuffer: 64 * 1024 * 1024,
  });
  if (!blob.includes(0) && blob.length < 8 * 1024 * 1024) {
    const content = blob.toString("utf8");
    if (secretPatterns.some((pattern) => pattern.test(content)))
      failures.push(`${file}: secret-like content`);
    if (
      file.startsWith("apps/") &&
      /(?:AppData[\\/]+Local[\\/]+TenderOS[\\/]+private-engine|from\s+[^\n]*private_engine|import\s+[^\n]*private_engine)/i.test(
        content,
      )
    )
      failures.push(`${file}: private source dependency`);
  }
}
if (failures.length) {
  console.error(failures.join("\n"));
  process.exitCode = 1;
} else
  console.log(
    `Public boundary check passed for ${staged.length} staged files. No private engine files, runtime databases or detected credentials staged.`,
  );
// The checker is a practical publishing guard, not a guarantee that arbitrary confidential prose is detectable.
