import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(new URL(".", import.meta.url).pathname, "..");
const createSessionsApi = readFileSync(resolve(root, "src/api/create-sessions.ts"), "utf8");
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const createPage = readFileSync(resolve(root, "src/pages/CreatePage.tsx"), "utf8");
const mockRuntime = readFileSync(resolve(root, "src/mock/runtime.ts"), "utf8");
const packageJson = readFileSync(resolve(root, "package.json"), "utf8");

const failures = [];

const requiredApiTokens = [
  "export async function sendCreateSessionEvent",
  "type: \"chat\" | \"upload_assets\" | \"regenerate\" | \"confirm\"",
  "requestJson<CreateSessionState>(`/api/create-sessions/${sessionId}/events`",
];

const requiredAppTokens = [
  "sendCreateSessionEvent",
  "sendMockCreateSessionEvent",
  "optimisticMessage",
  "optimistic: true",
  "thinkingMessage",
  "content: \"思考中...\"",
  "THINKING_MESSAGE_DELAY_MS = 1000",
  "window.setTimeout(() => {",
  "messages: [...current.messages, thinkingMessage]",
  "window.clearTimeout(thinkingMessageTimerId)",
  "setCreateSession((current) =>",
  "messages: [...current.messages, optimisticMessage]",
  "const [createSessionSending, setCreateSessionSending] = useState(false)",
  "async function handleSendCreateMessage(message: string)",
  "type: \"chat\"",
  "message: normalizedMessage",
  "setCreateSession(session)",
  "function alertCreateBackendError",
  "alertCreateBackendError(userError)",
  "onSendMessage={handleSendCreateMessage}",
  "createSessionSending={createSessionSending}",
];

const requiredCreatePageTokens = [
  "createSessionSending: boolean;",
  "onSendMessage: (message: string) => Promise<boolean>;",
  "type MessageAttachmentItem = {",
  "type RenderableConversationMessage = CreateSessionMessage & {",
  "function hasCardPayload(",
  "function getMessageAttachments(",
  "function buildRenderableMessages(",
  "message.payload?.event_type === \"upload_assets\"",
  "message.role === \"assistant\" && hasCardPayload(message)",
  "pendingAttachments = getMessageAttachments(message);",
  "message.attachments.length > 0",
  "className=\"message-attachments\"",
  "className=\"message-attachment-chip\"",
  "messageStreamRef",
  "scrollTop = messageStream.scrollHeight",
  "requestAnimationFrame(() => {",
  "async function handleSubmitMessage()",
  "setComposerText(\"\");\n    const sent = await onSendMessage(normalizedMessage)",
  "await onSendMessage(normalizedMessage)",
  "setComposerText(\"\")",
  "function handleComposerKeyDown",
  "event.key === \"Enter\"",
  "!event.shiftKey",
  "onKeyDown={handleComposerKeyDown}",
  "onClick={() => void handleSubmitMessage()}",
  "disabled={isConversationLocked || createSessionSending}",
  "const lastVisibleMessage = visibleMessages.at(-1);",
  "const shouldShowSuggestions = lastVisibleMessage?.role !== \"user\";",
  "const isPendingAssistantReply =",
  "lastVisibleMessage?.payload?.optimistic === true",
  "lastVisibleMessage?.content === \"思考中...\"",
  "!isPendingAssistantReply",
];

const requiredMockTokens = [
  "export function sendMockCreateSessionEvent",
  "event.type === \"chat\"",
  "event.message",
  "mockCreateSessions[sessionId] = nextSession",
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

for (const token of requiredMockTokens) {
  if (!mockRuntime.includes(token)) {
    failures.push(`Expected mock runtime to include: ${token}`);
  }
}

if (!packageJson.includes("\"test:create-chat-event\"")) {
  failures.push("Expected package.json to expose test:create-chat-event.");
}

if (createPage.includes("handleSuggestionSelect(suggestion);") && createPage.includes("await onSendMessage(suggestion)")) {
  failures.push("Expected suggestion click to fill composer text without auto-sending.");
}

if (/const sent = await onSendMessage\(normalizedMessage\);\s*if \(sent\) \{\s*setComposerText\(""\);/s.test(createPage)) {
  failures.push("Expected composer text to clear before awaiting chat response.");
}

if (
  !/assistant_response\?\.suggestions\.length\s*&&\s*!isConversationLocked\s*&&\s*!isPendingAssistantReply\s*&&\s*shouldShowSuggestions/s.test(
    createPage,
  )
) {
  failures.push(
    "Expected CreatePage.tsx to hide assistant suggestions while the optimistic assistant placeholder is visible.",
  );
}

if (
  !/attachments:\s*message\.role === "user"\s*\?\s*pendingAttachments\s*:\s*\[\]/s.test(
    createPage,
  )
) {
  failures.push(
    "Expected CreatePage.tsx to attach pending uploaded assets to the next rendered user message.",
  );
}

if (failures.length > 0) {
  console.error("Create chat event checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Create chat event checks passed.");
