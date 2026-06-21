import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const createPage = readFileSync(resolve(root, "src/pages/CreatePage.tsx"), "utf8");
const packageJson = readFileSync(resolve(root, "package.json"), "utf8");

const requiredTokens = [
  "GENERATION_AGENT_PROGRESS_STEPS",
  "init_generation_context",
  "orchestrator",
  "coding_agent",
  "asset_agent",
  "debug_agent",
  "validator_agent",
  "初始化生成上下文",
  "Orchestrator 编排方案",
  "Coding Agent 生成代码",
  "Asset Agent 生成素材",
  "Debug Agent 联调修复",
  "Validator Agent 验收",
  "getJobProgressView(currentJobStatus, agentLogs)",
  "getStepStatusFromLogs",
];

const failures = [];

for (const token of requiredTokens) {
  if (!createPage.includes(token)) {
    failures.push(`Expected CreatePage.tsx to include: ${token}`);
  }
}

if (createPage.includes("分析创意")) {
  failures.push("Expected CreatePage progress to stop using legacy 分析创意 label.");
}

if (
  /function getJobProgressView\(status: CreateTaskItem\["status"\] \| null\): JobProgressView/.test(
    createPage,
  )
) {
  failures.push("Expected getJobProgressView to accept agentLogs and derive progress from node logs.");
}

if (
  !/function getJobProgressView\(\s*status: CreateTaskItem\["status"\] \| null,\s*agentLogs: CreateAgentLogItem\[],\s*\): JobProgressView/.test(
    createPage,
  )
) {
  failures.push("Expected getJobProgressView(status, agentLogs) signature.");
}

if (
  !/GENERATION_AGENT_PROGRESS_STEPS\.map\(\(step\) => \(\{[\s\S]*getStepStatusFromLogs\(step\.nodeNames, agentLogs, status\)/.test(
    createPage,
  )
) {
  failures.push("Expected progress steps to map node names to statuses from AgentLog.");
}

if (/label:\s*"上传产物"/.test(createPage)) {
  failures.push("Expected CreatePage progress to stop rendering 上传产物 as a separate progress stage.");
}

if (/function getUploadStepStatus\(/.test(createPage)) {
  failures.push("Expected CreatePage progress to stop using getUploadStepStatus.");
}

if (
  !/const\s+steps\s*=\s*agentSteps;[\s\S]*succeededCount\s*=\s*steps\.filter/.test(createPage)
) {
  failures.push("Expected progress percent calculation to use only the six agent steps.");
}

if (/\(\(succeededCount \+ 0\.5\) \/ steps\.length\)/.test(createPage)) {
  failures.push("Expected running progress to stop pre-paying a half step before a stage completes.");
}

if (!packageJson.includes('"test:create-agent-progress"')) {
  failures.push("Expected package.json to expose test:create-agent-progress.");
}

if (failures.length > 0) {
  console.error("Create agent progress checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Create agent progress checks passed.");
