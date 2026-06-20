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
];

const requiredCssTokens = [
  ".create-page .create-side-panel",
  ".create-page .tasks-shell",
  ".create-page .conversation-shell",
  ".create-page .composer-shell",
  ".create-page .workspace-stage",
  ".create-page .composer-input-wrap",
  ".create-page .composer-floating-actions",
  ".create-page .selected-files",
  ".create-page .selected-file-chip",
  ".create-page .remove-file-button",
  "height: calc(100vh - 56px)",
  "overflow: hidden",
  "grid-template-columns: 430px minmax(0, 1fr)",
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

if (createPage.includes('className="task-sidebar"')) {
  failures.push("Expected task-sidebar layout to be removed from CreatePage.tsx");
}

if (createPage.includes("<h1>对话记录</h1>")) {
  failures.push("Expected legacy standalone 对话记录 panel to be removed");
}

if (failures.length > 0) {
  console.error("Create layout checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Create layout checks passed.");
