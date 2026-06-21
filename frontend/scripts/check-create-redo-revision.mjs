import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const jobsApi = readFileSync(resolve(root, "src/api/jobs.ts"), "utf8");

const failures = [];

const requiredTokens = [
  [jobsApi, "export async function createRevisionJob"],
  [jobsApi, "`/api/jobs/${jobId}/revisions`"],
  [jobsApi, "type CreateRevisionJobRequest"],
  [jobsApi, "type CreateRevisionJobResponse"],
  [app, "createRevisionJob"],
  [app, "await createRevisionJob(sourceTaskId"],
  [app, "parent_job_id: job.parent_job_id ?? sourceTaskId"],
  [app, "revision_intent"],
  [app, "requestPath: `/api/jobs/${sourceTaskId}/revisions`"],
  [app, "CREATE_REVISION_ACK_MESSAGE = \"好的，这就为您修改\""],
  [app, "content: CREATE_REVISION_ACK_MESSAGE"],
  [app, "businessStatus: mockEnabled ? \"mock_chat_revision_job_created\" : \"chat_revision_job_created\""],
];

for (const [contents, token] of requiredTokens) {
  if (!contents.includes(token)) {
    failures.push(`Expected token missing: ${token}`);
  }
}

const revisionFunctionMatch = app.match(
  /async function createRevisionJobFromChat\([\s\S]*?\): Promise<boolean> \{[\s\S]*?\n  \}/,
);

if (!revisionFunctionMatch) {
  failures.push("Expected createRevisionJobFromChat function to exist.");
} else if (revisionFunctionMatch[0].includes("createGenerationJobFromSession(createSession")) {
  failures.push("Expected chat revision flow to stop using initial createGenerationJobFromSession.");
}

if (app.includes("async function handleRedoGeneratedGame")) {
  failures.push("Expected the old right-panel redo function to be removed.");
}

if (app.includes("onRedoGeneratedGame={handleRedoGeneratedGame}")) {
  failures.push("Expected CreatePage to stop receiving a right-panel redo handler.");
}

if (failures.length > 0) {
  console.error("Create redo revision checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Create redo revision checks passed.");
