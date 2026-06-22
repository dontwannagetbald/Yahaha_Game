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
  "createRevisionJobFromChat(",
  "const canReviseGeneratedGame =",
  "CREATE_REVISION_ACK_MESSAGE = \"好的，这就为您修改\"",
  "content: CREATE_REVISION_ACK_MESSAGE",
  "有想要修改的地方欢迎随时告诉我～",
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
  "function getMessageCard(",
  "function getMessageAttachments(",
  "function buildRenderableMessages(",
  "let anchoredCardMessageIndex: number | null = null;",
  "message.payload?.event_type === \"upload_assets\"",
  "const card = getMessageCard(message);",
  "renderableMessages[anchoredCardMessageIndex]",
  "const hasAnchoredCard = visibleMessages.some((message) => message.card);",
  "const fallbackCard = !hasAnchoredCard ? assistant_response?.card ?? null : null;",
  "const card = message.card;",
  "pendingAttachments = getMessageAttachments(message);",
  "message.attachments.length > 0",
  "className=\"message-attachments\"",
  "className=\"message-attachment-chip\"",
  "messageStreamRef",
  "scrollTop = messageStream.scrollHeight",
  "requestAnimationFrame(() => {",
  "async function handleSubmitMessage()",
  "const filesToUpload = selectedFiles.filter(",
  "const uploaded = await uploadSelectedFiles(",
  "if (!normalizedMessage) {",
  "setComposerText(\"\");",
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

if (!createPage.includes("className=\"message-attachments\"")) {
  failures.push("Expected sent attachments to render as chat attachment bubbles after upload.");
}

if (createPage.includes("message.role === \"assistant\" && hasCardPayload(message)")) {
  failures.push("Expected card messages to stay in the chat stream so revisions do not move the original card.");
}

const mapIndex = createPage.indexOf("visibleMessages.map((message) => {");
const anchoredCardIndex = createPage.indexOf("const card = message.card;", mapIndex);
const confirmCardIndex = createPage.indexOf('className={`confirm-card ${isCardLoading ? "loading" : ""}`}', anchoredCardIndex);
const suggestionsIndex = createPage.indexOf("{suggestions.length > 0 ?", confirmCardIndex);

if (
  mapIndex === -1 ||
  anchoredCardIndex === -1 ||
  confirmCardIndex === -1 ||
  suggestionsIndex === -1 ||
  !(mapIndex < anchoredCardIndex && anchoredCardIndex < confirmCardIndex && confirmCardIndex < suggestionsIndex)
) {
  failures.push("Expected anchored cards to render inside their original message position before suggestions.");
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
  failures.push("Expected uploaded assets to attach to the next rendered user chat message.");
}

if (failures.length > 0) {
  console.error("Create chat event checks failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.info("Create chat event checks passed.");
