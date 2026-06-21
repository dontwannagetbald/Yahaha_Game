import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const createPage = readFileSync(resolve(root, "src/pages/CreatePage.tsx"), "utf8");
const jobsApi = readFileSync(resolve(root, "src/api/jobs.ts"), "utf8");
const mockRuntime = readFileSync(resolve(root, "src/mock/runtime.ts"), "utf8");
const packageJson = readFileSync(resolve(root, "package.json"), "utf8");

let createSessionsApi = "";
try {
  createSessionsApi = readFileSync(resolve(root, "src/api/create-sessions.ts"), "utf8");
} catch {
  createSessionsApi = "";
}

const failures = [];

const requiredApiTokens = [
  "export type CreateSessionMessage",
  "export type CreateSessionState",
  "export async function createCreateSession",
  "export async function getCreateSession",
  "requestJson<CreateSessionState>(\"/api/create-sessions\"",
  "requestJson<CreateSessionState>(`/api/create-sessions/${sessionId}`",
];

const requiredAppTokens = [
  "const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)",
  "const [selectedCreateSessionId, setSelectedCreateSessionId] = useState<string | null>(null)",
  "const [currentJobStatus, setCurrentJobStatus] = useState<JobStatus | null>(null)",
  "const [createSession, setCreateSession] = useState<CreateSessionState | null>(null)",
  "const isConversationLocked = currentJobStatus === \"pending\" || currentJobStatus === \"running\"",
  "async function handleCreateNewSession",
  "async function handleSelectCreateTask",
  "getCreateSession(task.session_id)",
  "createCreateSession()",
  "if (location.pathname !== \"/create\") {",
  "}, [authBootstrapStatus, isLoggedIn, location.pathname, mockEnabled]);",
  "selectedTaskId={selectedTaskId}",
  "selectedCreateSessionId={selectedCreateSessionId}",
  "currentJobStatus={currentJobStatus}",
  "isConversationLocked={isConversationLocked}",
  "createSession={createSession}",
  "onCreateNewSession={handleCreateNewSession}",
  "onSelectTask={handleSelectCreateTask}",
];

const requiredCreatePageTokens = [
  "session_id: string | null;",
  "selectedTaskId: string | null;",
  "selectedCreateSessionId: string | null;",
  "currentJobStatus: CreateTaskItem[\"status\"] | null;",
  "isConversationLocked: boolean;",
  "createSession: CreateSessionState | null;",
  "onCreateNewSession: () => void;",
  "onSelectTask: (task: CreateTaskItem) => void;",
  "createSession?.messages",
  "assistant_response",
  "disabled={isConversationLocked}",
  "onClick={() => onSelectTask(task)}",
  "onClick={onCreateNewSession}",
];

const requiredJobTokens = [
  "session_id: string | null;",
  "parent_job_id: string | null;",
];

const requiredMockTokens = [
  "session_id:",
  "mockCreateSessions",
  "createMockCreateSession",
  "getMockCreateSession",
];

for (const token of requiredApiTokens) {
  if (!createSessionsApi.includes(token)) {
    failures.push(`Expected create-sessions API to include: ${token}`);
  }
}

for (const token of requiredAppTokens) {
  if (!app.includes(token)) {
    failures.push(`Expected App.tsx to include: ${token}`);
  }
}

for (const token of requiredCreatePageTokens) {
  if (!createPage.includes(token)) {
    failures.push(`Expected CreatePage.tsx to include: ${token}`);
  }
}

for (const token of requiredJobTokens) {
  if (!jobsApi.includes(token)) {
    failures.push(`Expected jobs API to include: ${token}`);
  }
}

for (const token of requiredMockTokens) {
  if (!mockRuntime.includes(token)) {
    failures.push(`Expected mock runtime to include: ${token}`);
  }
}

if (!packageJson.includes("\"test:create-session-state\"")) {
  failures.push("Expected package.json to expose test:create-session-state.");
}

if (/localStorage\.(?:getItem|setItem|removeItem)\([^)]*create_session_id/s.test(app)) {
  failures.push("Expected Step 6.2 not to rely on localStorage create_session_id restoration.");
}

if (failures.length > 0) {
  console.error("Create session state checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Create session state checks passed.");
