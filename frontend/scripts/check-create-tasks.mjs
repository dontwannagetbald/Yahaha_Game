import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const jobsApi = readFileSync(resolve(root, "src/api/jobs.ts"), "utf8");
const createPage = readFileSync(resolve(root, "src/pages/CreatePage.tsx"), "utf8");

const failures = [];

const requiredAppTokens = [
  "const [createTasks, setCreateTasks] = useState<",
  "const [createTasksLoading, setCreateTasksLoading] = useState(false)",
  "const [createTasksError, setCreateTasksError] = useState<UserFacingError | null>(null)",
  "async function handleLoadCreateTasks(",
  "setCreateTasksLoading(true)",
  "const nextTasks = response.jobs.map(mapRawJobToCreateTask);",
  "setCreateTasks(nextTasks)",
  "const selectedTaskStillExists = selectedTaskId",
  "if (selectedTaskStillExists && selectedCreateSessionId) {",
  "requestPath: \"/api/jobs\"",
  "businessStatus: mockEnabled ? \"mock_jobs\" : \"loaded\"",
  "getJob(selectedTaskId)",
  "getJobLogs(selectedTaskId)",
  "const JOB_POLL_INTERVAL_MS = 1500;",
  "setSelectedAgentLogs(logsResponse.logs)",
  "[create][debug] selected job snapshot",
  "preview_inputs",
  "[create][debug] created job response",
  "window.setInterval",
  "window.clearInterval",
  "if (!isLoggedIn) {",
  "setCreateTasks([])",
  "<CreatePage",
  "tasks={createTasks}",
  "tasksLoading={createTasksLoading}",
  "tasksError={createTasksError}",
  "onRetryTasks={handleLoadCreateTasks}",
];

const requiredCreatePageTokens = [
  "type CreateTaskItem = {",
  "tasksLoading: boolean;",
  "tasksError: UserFacingError | null;",
  "onRetryTasks: () => void;",
  "if (tasksLoading && tasks.length === 0)",
  "任务历史加载中",
  "if (tasksError)",
  "重试任务历史",
  "tasks.length === 0",
  "暂无历史任务",
];

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

for (const token of [
  "[create][api] ${label}",
  "GET /api/jobs raw response",
  "POST /api/jobs raw response",
  "raw response",
]) {
  if (!jobsApi.includes(token)) {
    failures.push(`Expected jobs.ts to include debug logging token: ${token}`);
  }
}

if (app.includes("const tasks = useMemo(() => mockRuntime.tasks, [])")) {
  failures.push("Expected legacy static task memo to be removed from App.tsx");
}

const forbiddenAppTokens = [
  "function presentFailedCreateTask(task: CreateTaskItem)",
  "presentFailedCreateTask(nextTask)",
  "presentFailedCreateTask(currentFailedTask)",
  "presentFailedCreateTask(task)",
];

for (const token of forbiddenAppTokens) {
  if (app.includes(token)) {
    failures.push(`Expected App.tsx to remove auto failed-task dialog token: ${token}`);
  }
}

if (failures.length > 0) {
  console.error("Create task history checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Create task history checks passed.");
