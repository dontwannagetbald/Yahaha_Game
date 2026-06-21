import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const createPage = readFileSync(resolve(root, "src/pages/CreatePage.tsx"), "utf8");
const createCss = readFileSync(resolve(root, "src/pages/create.css"), "utf8");

const requiredPageTokens = [
  "create-side-panel",
  "tasks-shell",
  "tasks-toggle",
  "tasks-expanded",
  "conversation-shell",
  "composer-shell",
  "workspace-stage",
  "useRef",
  "selectedFiles",
  "fileInputRef",
  'type="file"',
  "fileInputRef.current?.click()",
  "handleRemoveFile",
  "remove-file-button",
  "current.filter",
  "composer-input-wrap",
  "selected-files",
  "currentUser:",
  "currentUser?.avatar_url",
  "message-avatar-image",
  "getUserAvatarInitial",
  "className=\"message-avatar-default\"",
  "className=\"task-head\"",
  "const shouldShowGenerateEmptyState = !selectedTaskId && currentJobStatus === null;",
  "还没有开始生成游戏？去和AI聊聊想要生成什么样的游戏吧！",
  "className=\"generate-panel-empty-state\"",
  "shouldShowGenerateEmptyState ? (",
  "shouldShowGenerateEmptyState ? \"empty\" : currentJobStatus === \"succeeded\" ? \"succeeded\" : \"in-progress\"",
  "currentJobStatus === \"succeeded\" ? (",
  "重做",
  "onRedoGeneratedGame",
  "className=\"agent-status-scroll\"",
];

const requiredCssTokens = [
  ".create-page .create-side-panel",
  ".create-page .tasks-shell",
  ".create-page .task-head",
  ".create-page .conversation-shell",
  ".create-page .composer-shell",
  ".create-page .workspace-stage",
  ".create-page .generate-panel.empty",
  ".create-page .generate-panel-empty-state",
  ".create-page .composer-input-wrap",
  ".create-page .composer-floating-actions",
  ".create-page .selected-files",
  ".create-page .selected-file-chip",
  ".create-page .remove-file-button",
  ".create-page .message-row.user",
  "flex-direction: row-reverse",
  ".create-page .message-row.user .message-avatar",
  ".create-page .message-avatar-default",
  ".create-page .message-avatar-image",
  "object-fit: cover",
  "linear-gradient(135deg, rgba(184, 109, 255, 0.16) 0%, rgba(124, 92, 255, 0.16) 52%, rgba(236, 140, 255, 0.16) 100%)",
  "max-width: 66.666%",
  ".create-page .message-stream::-webkit-scrollbar",
  "scrollbar-width: thin",
  "height: calc(100vh - 56px)",
  "overflow: hidden",
  "grid-template-columns: 430px minmax(0, 1fr)",
  ".create-page .agent-status-scroll",
  "max-height: 222px",
  "overflow-y: auto",
  "padding-right: 6px",
  "flex: 1 1 420px",
  "gap: 12px",
  "padding: 12px 18px 18px",
  "padding: 12px 14px",
];

const failures = [];

for (const token of requiredPageTokens) {
  if (!createPage.includes(token)) {
    failures.push(`Expected CreatePage.tsx to include: ${token}`);
  }
}

for (const token of requiredCssTokens) {
  if (!createCss.includes(token)) {
    failures.push(`Expected create.css to include: ${token}`);
  }
}

if (
  !/\.create-page \.message-row\.user\s*\{[^}]*gap:\s*14px;[^}]*\}/s.test(
    createCss,
  )
) {
  failures.push("Expected user message row to keep a 14px avatar gap");
}

if (
  !/\.create-page \.message-stream\s*\{[^}]*padding:\s*16px 12px 16px 2px;[^}]*\}/s.test(
    createCss,
  )
) {
  failures.push("Expected message stream to reserve right padding for avatar and scrollbar");
}

if (
  !/\.create-page \.message-stream::-webkit-scrollbar\s*\{[^}]*width:\s*6px;[^}]*\}/s.test(
    createCss,
  )
) {
  failures.push("Expected message stream scrollbar width to be 6px");
}

if (createPage.includes('className="task-sidebar"')) {
  failures.push("Expected task-sidebar layout to be removed from CreatePage.tsx");
}

if (createPage.includes("<h1>对话记录</h1>")) {
  failures.push("Expected legacy standalone 对话记录 panel to be removed");
}

if (
  createPage.includes("正在准备对话") ||
  createPage.includes("开始对话")
) {
  failures.push("Expected empty conversation placeholder to be removed");
}

if (createPage.includes("正在恢复对话")) {
  failures.push("Expected CreatePage conversation stream to avoid inline loading placeholder text.");
}

if (
  /message-stream[\s\S]*createSessionError[\s\S]*task-list-state task-list-error[\s\S]*onClick=\{onCreateNewSession\}/.test(
    createPage,
  )
) {
  failures.push("Expected CreatePage conversation stream to avoid inline error fallback with 新建任务 button.");
}

if (createPage.includes("当前会话")) {
  failures.push("Expected CreatePage workspace panel to hide the current session id text");
}

if (createPage.includes("Playable Preview")) {
  failures.push("Expected CreatePage workspace panel to hide the Playable Preview label");
}

if (createPage.includes("formatTaskSummary(") || createPage.includes("<p>{formatTaskSummary(task)}</p>")) {
  failures.push("Expected task list items to hide summary text and only render title plus status.");
}

if (createCss.includes(".create-page .task-item p")) {
  failures.push("Expected task item paragraph summary styles to be removed.");
}

const agentLogIndex = createPage.indexOf('className="agent-log"');
const progressRowIndex = createPage.indexOf('className="progress-row"');

if (agentLogIndex === -1 || progressRowIndex === -1 || agentLogIndex > progressRowIndex) {
  failures.push("Expected agent progress steps to render above the progress bar");
}

if (
  !/shouldShowGenerateEmptyState\s*\?\s*\([\s\S]*generate-panel-empty-state[\s\S]*\)\s*:\s*currentJobStatus === "succeeded"\s*\?\s*\([\s\S]*className="workspace-head"[\s\S]*className="preview-frame preview-sandbox"[\s\S]*发布[\s\S]*重做[\s\S]*\)\s*:\s*\([\s\S]*className="workspace-head"[\s\S]*className="agent-log"[\s\S]*className="progress-row"[\s\S]*\)/.test(
    createPage,
  )
) {
  failures.push("Expected CreatePage workspace panel to render empty state before confirmation, sandbox on success, and progress sections while jobs are running");
}

if (!/onClick=\{\(\) => void onRedoGeneratedGame\(\)\}[\s\S]*重做/.test(createPage)) {
  failures.push("Expected succeeded workspace redo button to trigger onRedoGeneratedGame.");
}

if (!createPage.includes("const [tasksExpanded, setTasksExpanded] = useState(false);")) {
  failures.push("Expected task list to be collapsed by default");
}

if (createCss.includes("#6f4bc8")) {
  failures.push("Expected default user avatar to avoid an opaque purple fallback");
}

if (createCss.includes('images.unsplash.com/photo-1511512578047-dfb367046420')) {
  failures.push("Expected preview frame to avoid a hard-coded background image");
}

if (failures.length > 0) {
  console.error("Create layout checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Create layout checks passed.");
