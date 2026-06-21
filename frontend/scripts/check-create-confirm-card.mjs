import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const createPage = readFileSync(resolve(root, "src/pages/CreatePage.tsx"), "utf8");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const mockRuntime = readFileSync(resolve(root, "src/mock/runtime.ts"), "utf8");
const jobsApi = readFileSync(resolve(root, "src/api/jobs.ts"), "utf8");

const failures = [];

const requiredCreatePageTokens = [
  "onRegenerateCard: () => Promise<boolean>;",
  "onConfirmCard: () => Promise<boolean>;",
  "createSessionPendingEventType:",
  "| \"chat\"",
  "| \"upload_assets\"",
  "| \"regenerate\"",
  "| \"confirm\"",
  "const isCardLoading =",
  "const hasAnchoredCard = visibleMessages.some((message) => message.card);",
  "const fallbackCard = !hasAnchoredCard ? assistant_response?.card ?? null : null;",
  "createSessionPendingEventType === \"chat\"",
  "createSessionPendingEventType === \"regenerate\"",
  "createSessionPendingEventType === \"confirm\"",
  "className={`confirm-card ${isCardLoading ? \"loading\" : \"\"}`}",
  "className=\"confirm-card-status\"",
  "生成中...",
  "const shouldShowCardActions =",
  "createSession?.conversation_status === \"ready_to_confirm\"",
  "shouldShowCardActions ? (",
  "<div className=\"confirm-card-actions\">",
  "确认",
  "重新生成",
  "className=\"primary-pill\"",
  "className=\"secondary-pill\"",
  "onClick={() => void onConfirmCard()}",
  "onClick={() => void onRegenerateCard()}",
];

const requiredAppTokens = [
  "createJob",
  "async function handleRegenerateCreateCard()",
  "async function handleConfirmCreateCard(): Promise<boolean>",
  "const [createSessionPendingEventType, setCreateSessionPendingEventType] = useState<",
  "setCreateSessionPendingEventType(\"chat\")",
  "setCreateSessionPendingEventType(\"upload_assets\")",
  "setCreateSessionPendingEventType(\"regenerate\")",
  "setCreateSessionPendingEventType(\"confirm\")",
  "setCreateSessionPendingEventType(null)",
  "type: \"confirm\"",
  "handoff_to_generation",
  "setCurrentJobStatus(\"pending\")",
  "setSelectedTaskId(job.job_id)",
  "setCreateTasks((current) =>",
  "type: \"regenerate\"",
  "selected_plan_id: currentCard.plan_id",
  "const shouldQueueThinkingMessage = !createSession.assistant_response.card;",
  "if (shouldQueueThinkingMessage) {",
  "createSessionPendingEventType={createSessionPendingEventType}",
  "onConfirmCard={handleConfirmCreateCard}",
  "onRegenerateCard={handleRegenerateCreateCard}",
];

const requiredMockTokens = [
  "event.type === \"confirm\"",
  "event.type === \"regenerate\"",
  "plan_id:",
  "conversation_status: \"ready_to_confirm\"",
];

const requiredJobsApiTokens = [
  "export async function createJob",
  "requestJson<CreateJobResponse>(\"/api/jobs\"",
  "session_id: string;",
  "prompt?: string;",
];

for (const token of requiredCreatePageTokens) {
  if (!createPage.includes(token)) {
    failures.push(`Expected CreatePage.tsx to include: ${token}`);
  }
}

for (const token of requiredAppTokens) {
  if (!app.includes(token)) {
    failures.push(`Expected App.tsx to include: ${token}`);
  }
}

for (const token of requiredMockTokens) {
  if (!mockRuntime.includes(token)) {
    failures.push(`Expected mock runtime to include: ${token}`);
  }
}

for (const token of requiredJobsApiTokens) {
  if (!jobsApi.includes(token)) {
    failures.push(`Expected jobs API to include: ${token}`);
  }
}

if (createPage.includes("方案 ID：{card.plan_id}")) {
  failures.push("Expected confirm card to hide plan_id from the rendered card body.");
}

if (createPage.includes("标签：{card.tags.join(\" / \") || \"暂无标签\"}")) {
  failures.push("Expected confirm card to hide tags from the rendered card body.");
}

if (/card\s*&&\s*createSession\?\.conversation_status === "ready_to_confirm"/.test(createPage)) {
  failures.push("Expected confirm card to remain visible after confirm instead of gating the whole card on ready_to_confirm.");
}

if (createPage.includes("const card = assistant_response?.card ?? null;")) {
  failures.push("Expected confirm card to avoid global end-of-stream rendering that moves after revision messages.");
}

if (
  !/shouldShowCardActions\s*\?\s*\([\s\S]*className="confirm-card-actions"[\s\S]*onClick=\{\(\) => void onConfirmCard\(\)\}[\s\S]*onClick=\{\(\) => void onRegenerateCard\(\)\}[\s\S]*\)\s*:\s*null/.test(
    createPage,
  )
) {
  failures.push("Expected confirm/regenerate buttons to render only while the card is still confirmable.");
}

if (failures.length > 0) {
  console.error("Create confirm card checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Create confirm card checks passed.");
