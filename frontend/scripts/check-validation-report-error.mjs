import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const files = {
  jobs: readFileSync(resolve(root, "src/api/jobs.ts"), "utf8"),
  errors: readFileSync(resolve(root, "src/lib/errors.ts"), "utf8"),
  app: readFileSync(resolve(root, "src/App.tsx"), "utf8"),
};

const expectations = [
  [files.jobs, "validation_report: Record<string, unknown> | null;"],
  [files.errors, "details?: string;"],
  [files.app, "buildValidationReportDetails"],
  [files.app, "validation_report"],
  [files.app, "<pre className=\"error-dialog-details\">"],
  [files.app, "任务生成失败"],
];

const failures = expectations.filter(([contents, token]) => !contents.includes(token));

if (failures.length > 0) {
  console.error("Validation report error dialog checks failed:");
  for (const [, token] of failures) {
    console.error(`- Expected token missing: ${token}`);
  }
  process.exit(1);
}

console.info("Validation report error dialog checks passed.");
