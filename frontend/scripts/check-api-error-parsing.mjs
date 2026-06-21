import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const client = readFileSync(resolve(root, "src/api/client.ts"), "utf8");

const expectations = [
  "detail?:",
  "normalizeErrorDetail",
  "Array.isArray(body.detail)",
  "details?: unknown",
  "stringifyErrorDetails",
  "body?.error?.details",
  "body?.error?.message ?? detail.message",
  "body?.error?.code ?? detail.code",
  "body?.error?.retry_hint ?? detail.retryHint",
];

const failures = expectations.filter((token) => !client.includes(token));

if (failures.length > 0) {
  console.error("API error parsing checks failed:");
  for (const failure of failures) {
    console.error(`- Expected token missing: ${failure}`);
  }
  process.exit(1);
}

console.info("API error parsing checks passed.");
