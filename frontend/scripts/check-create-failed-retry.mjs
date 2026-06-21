import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");

const failures = [];

const requiredTokens = [
  "retryableFailedTaskId",
  "setRetryableFailedTaskId(nextTask.job_id)",
  "async function handleRetryFailedGenerationTask(): Promise<void>",
  "await createGenerationJobFromSession(session, {",
  "fallbackTitle: failedTask.title",
  "requestPath: \"/api/jobs\"",
  "businessStatus: mockEnabled ? \"mock_failed_job_retry_created\" : \"failed_job_retry_created\"",
  "confirmLabel={retryableFailedTaskId ? \"重新生成\" : \"知道了\"}",
  "onConfirm={retryableFailedTaskId ? () => void handleRetryFailedGenerationTask() : undefined}",
];

for (const token of requiredTokens) {
  if (!app.includes(token)) {
    failures.push(`Expected App.tsx to include: ${token}`);
  }
}

if (!/setCreateDialogError\(\{\s*title: "任务生成失败"[\s\S]*setRetryableFailedTaskId\(nextTask\.job_id\)/.test(app)) {
  failures.push("Expected failed generation dialog to mark the failed job as retryable.");
}

if (
  !/const session =\s*createSession\?\.session_id === failedTask\.session_id[\s\S]*:\s*await getCreateSession\(failedTask\.session_id\)/.test(
    app,
  )
) {
  failures.push("Expected retry flow to reload the original create session by failedTask.session_id.");
}

if (failures.length > 0) {
  console.error("Create failed retry checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Create failed retry checks passed.");
