import { useEffect, useRef, useState, type ChangeEvent, type KeyboardEvent } from "react";

import type { AuthUser } from "../api/auth";
import type {
  CreateSessionCard,
  CreateSessionMessage,
  CreateSessionState,
} from "../api/create-sessions";
import { MAX_CREATE_UPLOAD_SIZE_BYTES } from "../api/uploads";
import { logConsoleEvent } from "../lib/console";
import type { UserFacingError } from "../lib/errors";
import { fallbackCoverUrl } from "../lib/games";
import "./create.css";

export type CreateTaskItem = {
  job_id: string;
  session_id: string | null;
  parent_job_id: string | null;
  title: string;
  status: "pending" | "running" | "succeeded" | "failed";
  created_at: string;
  game_id: string | null;
  cover_url?: string | null;
  result_summary: string | null;
  error_message: string | null;
  validation_report: Record<string, unknown> | null;
  manifest_url?: string | null;
  artifact_base_url?: string | null;
};

export type CreateUploadedFileItem = {
  id: string;
  name: string;
  size: number;
  mimeType: string;
  status: "pending" | "uploading" | "failed";
  file?: File;
  error?: string;
};

type MessageAttachmentItem = {
  id: string;
  name: string;
  size: number;
  mimeType: string;
};

type JobProgressStepStatus = "pending" | "running" | "succeeded" | "failed";

type JobProgressStep = {
  label: string;
  status: JobProgressStepStatus;
};

type JobProgressView = {
  label: string;
  percent: number;
  steps: JobProgressStep[];
};

type AgentProgressStepDefinition = {
  label: string;
  nodeNames: string[];
};

export type CreateAgentLogItem = {
  step: string;
  level: "info" | "warning" | "error";
  message: string;
  created_at: string;
};

type RenderableConversationMessage = CreateSessionMessage & {
  attachments: MessageAttachmentItem[];
  card: CreateSessionCard | null;
};

type CreatePageProps = {
  tasks: CreateTaskItem[];
  tasksLoading: boolean;
  tasksError: UserFacingError | null;
  deletingTaskId: string | null;
  selectedTaskId: string | null;
  selectedCreateSessionId: string | null;
  currentJobStatus: CreateTaskItem["status"] | null;
  agentLogs: CreateAgentLogItem[];
  agentLogsError: UserFacingError | null;
  isConversationLocked: boolean;
  createSession: CreateSessionState | null;
  createSessionLoading: boolean;
  createSessionError: UserFacingError | null;
  createSessionSending: boolean;
  createSessionPendingEventType:
    | "chat"
    | "upload_assets"
    | "regenerate"
    | "confirm"
    | null;
  currentUser: AuthUser | null;
  publishingGameId: string | null;
  revisionPromptMessage: string;
  onRetryTasks: () => void;
  onCreateNewSession: () => void;
  onSelectTask: (task: CreateTaskItem) => void;
  onDeleteTask: (task: CreateTaskItem) => Promise<boolean>;
  onPublishGame: (task: CreateTaskItem) => Promise<boolean>;
  onConfirmCard: () => Promise<boolean>;
  onRegenerateCard: () => Promise<boolean>;
  onSendMessage: (message: string) => Promise<boolean>;
  onUploadFiles: (files: File[]) => Promise<boolean>;
};

function getUserAvatarInitial(user: AuthUser | null): string {
  const displayName = user?.display_name?.trim();
  const emailPrefix = user?.email?.split("@", 1)[0]?.trim();
  const label = displayName || emailPrefix || "我";
  return label.slice(0, 1).toUpperCase();
}

function hasCardPayload(message: CreateSessionMessage): boolean {
  return getMessageCard(message) !== null;
}

function getMessageCard(message: CreateSessionMessage): CreateSessionCard | null {
  if (!message.payload || typeof message.payload !== "object") {
    return null;
  }

  const card = (message.payload as Record<string, unknown>).card;
  if (!card || typeof card !== "object") {
    return null;
  }

  const cardRecord = card as Record<string, unknown>;
  if (
    typeof cardRecord.plan_id !== "string" ||
    typeof cardRecord.title !== "string" ||
    typeof cardRecord.introduction !== "string"
  ) {
    return null;
  }

  return {
    plan_id: cardRecord.plan_id,
    title: cardRecord.title,
    introduction: cardRecord.introduction,
    tags: Array.isArray(cardRecord.tags)
      ? cardRecord.tags.filter((tag): tag is string => typeof tag === "string")
      : [],
  };
}

function getMessageAttachments(message: CreateSessionMessage): MessageAttachmentItem[] {
  const payload =
    message.payload && typeof message.payload === "object"
      ? (message.payload as Record<string, unknown>)
      : null;
  if (!payload || payload.event_type !== "upload_assets") {
    return [];
  }

  const rawAssets = (payload as Record<string, unknown>).assets;
  if (!Array.isArray(rawAssets)) {
    return [];
  }

  return rawAssets.flatMap((asset, index) => {
    if (!asset || typeof asset !== "object") {
      return [];
    }

    const assetRecord = asset as Record<string, unknown>;
    const filename = typeof assetRecord.filename === "string" ? assetRecord.filename : null;
    const assetId =
      typeof assetRecord.asset_id === "string" ? assetRecord.asset_id : `${message.id}-${index}`;

    if (!filename) {
      return [];
    }

    return [
      {
        id: assetId,
        name: filename,
        size: typeof assetRecord.size_bytes === "number" ? assetRecord.size_bytes : 0,
        mimeType:
          typeof assetRecord.mime_type === "string"
            ? assetRecord.mime_type
            : "application/octet-stream",
      },
    ];
  });
}

function buildRenderableMessages(messages: CreateSessionMessage[]): RenderableConversationMessage[] {
  const renderableMessages: RenderableConversationMessage[] = [];
  let pendingAttachments: MessageAttachmentItem[] = [];
  let pendingAttachmentMessageId: string | null = null;
  let pendingAttachmentCreatedAt: string | null = null;
  let anchoredCardMessageIndex: number | null = null;

  for (const message of messages) {
    if (message.payload?.event_type === "upload_assets") {
      pendingAttachments = getMessageAttachments(message);
      pendingAttachmentMessageId = message.id;
      pendingAttachmentCreatedAt = message.created_at;
      continue;
    }

    if (message.role === "system") {
      continue;
    }

    const card = getMessageCard(message);
    const renderableMessage: RenderableConversationMessage = {
      ...message,
      attachments: message.role === "user" ? pendingAttachments : [],
      card,
    };

    if (card && anchoredCardMessageIndex !== null) {
      renderableMessages[anchoredCardMessageIndex] = {
        ...renderableMessages[anchoredCardMessageIndex],
        content: message.content,
        payload: message.payload,
        card,
      };
    } else {
      renderableMessages.push(renderableMessage);
      if (card) {
        anchoredCardMessageIndex = renderableMessages.length - 1;
      }
    }

    if (message.role === "user") {
      pendingAttachments = [];
      pendingAttachmentMessageId = null;
      pendingAttachmentCreatedAt = null;
    }
  }

  if (pendingAttachments.length > 0) {
    renderableMessages.push({
      id: `${pendingAttachmentMessageId ?? "pending-attachments"}-bubble`,
      role: "user",
      content: "",
      payload: null,
      attachments: pendingAttachments,
      card: null,
      created_at: pendingAttachmentCreatedAt ?? new Date(0).toISOString(),
    });
  }

  return renderableMessages;
}

const GENERATION_AGENT_PROGRESS_STEPS: AgentProgressStepDefinition[] = [
  {
    label: "初始化生成上下文",
    nodeNames: ["init_generation_context"],
  },
  {
    label: "Orchestrator 编排方案",
    nodeNames: ["orchestrator", "build_parallel_contracts"],
  },
  {
    label: "Coding Agent 生成代码",
    nodeNames: ["coding_agent", "draft_code"],
  },
  {
    label: "Asset Agent 生成素材",
    nodeNames: ["asset_agent", "run_asset_agent"],
  },
  {
    label: "Debug Agent 联调修复",
    nodeNames: ["join_assets_and_code", "debug_agent", "debug_code_with_assets"],
  },
  {
    label: "Validator Agent 验收",
    nodeNames: ["validator_agent", "validate_final_delivery"],
  },
];

function getJobProgressView(
  status: CreateTaskItem["status"] | null,
  agentLogs: CreateAgentLogItem[],
): JobProgressView {
  const agentSteps = GENERATION_AGENT_PROGRESS_STEPS.map((step) => ({
    label: step.label,
    status: getStepStatusFromLogs(step.nodeNames, agentLogs, status),
  }));
  const steps = agentSteps;
  const succeededCount = steps.filter((step) => step.status === "succeeded").length;
  const hasFailedStep = steps.some((step) => step.status === "failed");
  const percent =
    status === "succeeded"
      ? 100
      : status === "failed" || hasFailedStep
        ? Math.round((succeededCount / steps.length) * 100)
        : Math.round((succeededCount / steps.length) * 100);

  return {
    label:
      status === "succeeded"
        ? "生成完成"
        : status === "failed" || hasFailedStep
          ? "生成失败"
          : status === "running"
            ? "生成中"
            : status === "pending"
              ? "准备生成"
              : "等待生成",
    percent,
    steps,
  };
}

function getStepStatusFromLogs(
  nodeNames: string[],
  agentLogs: CreateAgentLogItem[],
  jobStatus: CreateTaskItem["status"] | null,
): JobProgressStepStatus {
  const matchingLogs = agentLogs.filter((log) => nodeNames.includes(log.step));
  if (matchingLogs.some((log) => log.level === "error" || log.message.includes(" failed"))) {
    return "failed";
  }
  if (
    matchingLogs.some(
      (log) =>
        log.message.includes(" completed") ||
        log.message.includes("Generated ") ||
        log.message.includes("Drafted ") ||
        log.message.includes("Joined ") ||
        log.message.includes("Completed ") ||
        log.message.includes("Initialized "),
    )
  ) {
    return "succeeded";
  }
  if (matchingLogs.some((log) => log.message.includes(" started"))) {
    return "running";
  }
  if (jobStatus === "succeeded") {
    return "succeeded";
  }
  return "pending";
}

function toAbsoluteUrl(rawUrl: string | null | undefined): string | null {
  if (!rawUrl) {
    return null;
  }

  try {
    return new URL(rawUrl, window.location.origin).toString();
  } catch {
    return null;
  }
}

function getPreviewCoverUrl(selectedTask: CreateTaskItem | null): string {
  return toAbsoluteUrl(selectedTask?.cover_url) ?? fallbackCoverUrl;
}

function getPreviewUrls(
  selectedTask: CreateTaskItem | null,
): { iframeSrc: string; bundleUrl: string } | null {
  const artifactBaseUrl = toAbsoluteUrl(selectedTask?.artifact_base_url);
  if (artifactBaseUrl) {
    const bundleUrl = new URL("index.html", artifactBaseUrl).toString();
    return {
      iframeSrc: bundleUrl,
      bundleUrl,
    };
  }

  const manifestUrl = toAbsoluteUrl(selectedTask?.manifest_url);
  if (manifestUrl) {
    const bundleUrl = new URL("index.html", manifestUrl).toString();
    return {
      iframeSrc: bundleUrl,
      bundleUrl,
    };
  }

  return null;
}

export function CreatePage({
  tasks,
  tasksLoading,
  tasksError,
  deletingTaskId,
  selectedTaskId,
  selectedCreateSessionId,
  currentJobStatus,
  agentLogs,
  agentLogsError,
  isConversationLocked,
  createSession,
  createSessionLoading,
  createSessionError,
  createSessionSending,
  createSessionPendingEventType,
  currentUser,
  publishingGameId,
  revisionPromptMessage,
  onRetryTasks,
  onCreateNewSession,
  onSelectTask,
  onDeleteTask,
  onPublishGame,
  onConfirmCard,
  onRegenerateCard,
  onSendMessage,
  onUploadFiles,
}: CreatePageProps) {
  const [tasksExpanded, setTasksExpanded] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<CreateUploadedFileItem[]>([]);
  const [composerText, setComposerText] = useState("");
  const [startedPreviewTaskIds, setStartedPreviewTaskIds] = useState<Record<string, true>>({});
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messageStreamRef = useRef<HTMLDivElement | null>(null);

  let taskHistoryContent: React.ReactNode = null;

  if (tasksLoading && tasks.length === 0) {
    taskHistoryContent = <p className="task-list-state">任务历史加载中</p>;
  } else if (tasksError) {
    taskHistoryContent = (
      <div className="task-list-state task-list-error" role="alert">
        <p>{tasksError.message}</p>
        <button className="secondary-pill full-width" onClick={onRetryTasks} type="button">
          重试任务历史
        </button>
      </div>
    );
  } else if (tasks.length === 0) {
    taskHistoryContent = <p className="task-list-state">暂无历史任务</p>;
  } else {
    taskHistoryContent = tasks.map((task) => (
      <div className={`task-item ${selectedTaskId === task.job_id ? "selected" : ""}`} key={task.job_id}>
        <button className="task-select-button" onClick={() => onSelectTask(task)} type="button">
          <div className="task-head">
            <strong>{task.title}</strong>
            <span className={`badge ${task.status}`}>{task.status}</span>
          </div>
        </button>
        <button
          aria-label={`删除任务 ${task.title}`}
          className="task-delete-button"
          disabled={
            Boolean(deletingTaskId) ||
            task.status === "pending" ||
            task.status === "running"
          }
          onClick={() => void onDeleteTask(task)}
          type="button"
        >
          ×
        </button>
      </div>
    ));
  }

  useEffect(() => {
    logConsoleEvent("create", {
      requestPath: "/api/jobs",
      status: 200,
      businessStatus: "rendered",
      count: tasks.length,
    });
  }, [tasks.length]);

  useEffect(() => {
    setSelectedFiles([]);
  }, [selectedCreateSessionId]);

  function handleFileSelect(event: ChangeEvent<HTMLInputElement>) {
    const nextFiles = Array.from(event.target.files ?? []);
    const nextItems: CreateUploadedFileItem[] = [];

    for (const file of nextFiles) {
      const id = `${file.name}-${file.size}-${file.lastModified}-${crypto.randomUUID()}`;
      if (file.size > MAX_CREATE_UPLOAD_SIZE_BYTES) {
        nextItems.push({
          id,
          name: file.name,
          size: file.size,
          mimeType: file.type || "application/octet-stream",
          status: "failed",
          error: "单文件不能超过 20MB。",
        });
        continue;
      }

      nextItems.push({
        id,
        name: file.name,
        size: file.size,
        mimeType: file.type || "application/octet-stream",
        status: "pending",
        file,
      });
    }

    setSelectedFiles((current) => [...current, ...nextItems]);
    event.target.value = "";
  }

  function handleRemoveFile(fileId: string) {
    setSelectedFiles((current) => current.filter((item) => item.id !== fileId));
  }

  async function uploadSelectedFiles(items: CreateUploadedFileItem[], files: File[]): Promise<boolean> {
    const itemIds = new Set(items.map((item) => item.id));
    const uploaded = await onUploadFiles(files);
    setSelectedFiles((current) =>
      current.flatMap((file) => {
        if (!itemIds.has(file.id)) {
          return [file];
        }
        if (uploaded) {
          return [];
        }
        return [
          {
            ...file,
            status: "failed" as const,
            error: "上传失败，请稍后重试。",
          },
        ];
      }),
    );
    return uploaded;
  }

  function handleRetryFile(file: CreateUploadedFileItem) {
    if (!file.file || file.size > MAX_CREATE_UPLOAD_SIZE_BYTES) {
      return;
    }
    setSelectedFiles((current) =>
      current.map((item) =>
        item.id === file.id
          ? {
              ...item,
              status: "pending",
              error: undefined,
            }
          : item,
      ),
    );
  }

  function handleSuggestionSelect(suggestion: string) {
    setComposerText(suggestion);
  }

  async function handleSubmitMessage() {
    const normalizedMessage = composerText.trim();
    const filesToUpload = selectedFiles.filter(
      (file): file is CreateUploadedFileItem & { file: File } =>
        file.status !== "failed" && Boolean(file.file),
    );
    if (isConversationLocked || createSessionSending) {
      return;
    }

    if (!normalizedMessage && filesToUpload.length === 0) {
      return;
    }

    setComposerText("");
    if (filesToUpload.length > 0) {
      const uploadIds = new Set(filesToUpload.map((file) => file.id));
      setSelectedFiles((current) =>
        current.map((file) =>
          uploadIds.has(file.id)
            ? {
                ...file,
                status: "uploading",
                error: undefined,
              }
            : file,
        ),
      );
      const uploaded = await uploadSelectedFiles(
        filesToUpload,
        filesToUpload.map((file) => file.file),
      );
      if (!uploaded) {
        setComposerText(normalizedMessage);
        return;
      }
    }

    if (!normalizedMessage) {
      return;
    }

    const sent = await onSendMessage(normalizedMessage);
    if (!sent) {
      setComposerText(normalizedMessage);
    }
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSubmitMessage();
    }
  }

  const assistant_response = createSession?.assistant_response;
  const sessionMessages = buildRenderableMessages(createSession?.messages ?? []);
  const visibleMessages =
    sessionMessages.length > 0
      ? sessionMessages
      : assistant_response?.message
        ? [
            {
              id: `${createSession?.session_id ?? "session"}-assistant-response`,
              role: "assistant" as const,
              content: assistant_response.message,
              payload: null,
              attachments: [],
              card: null,
              created_at: createSession?.updated_at ?? new Date(0).toISOString(),
            },
          ]
        : [];
  const hasAnchoredCard = visibleMessages.some((message) => message.card);
  const fallbackCard = !hasAnchoredCard ? assistant_response?.card ?? null : null;
  const lastVisibleMessage = visibleMessages.at(-1);
  const shouldShowSuggestions = lastVisibleMessage?.role !== "user";
  const isPendingAssistantReply =
    createSessionSending ||
    lastVisibleMessage?.payload?.optimistic === true ||
    lastVisibleMessage?.content === "思考中...";
  const suggestions =
    assistant_response?.suggestions.length &&
    !isConversationLocked &&
    !isPendingAssistantReply &&
    shouldShowSuggestions
      ? assistant_response.suggestions
      : [];
  const shouldShowCardActions =
    createSession?.conversation_status === "ready_to_confirm" && !isConversationLocked;
  const shouldShowRevisionPrompt =
    currentJobStatus === "succeeded" && createSession?.conversation_status === "confirmed";
  const isCardLoading =
    Boolean(fallbackCard || hasAnchoredCard) &&
    (createSessionPendingEventType === "chat" ||
      createSessionPendingEventType === "regenerate" ||
      createSessionPendingEventType === "confirm");
  const visibleFiles = selectedFiles;
  const jobProgress = getJobProgressView(currentJobStatus, agentLogs);
  const shouldShowGenerateEmptyState = !selectedTaskId && currentJobStatus === null;
  const selectedTask = tasks.find((task) => task.job_id === selectedTaskId) ?? null;
  const previewUrls = getPreviewUrls(selectedTask);
  const previewCoverUrl = getPreviewCoverUrl(selectedTask);
  const hasStartedPreview = selectedTask ? Boolean(startedPreviewTaskIds[selectedTask.job_id]) : false;
  const selectedTaskGameId = selectedTask?.game_id ?? null;
  const isPublishingSelectedGame =
    selectedTaskGameId !== null ? publishingGameId === selectedTaskGameId : false;

  useEffect(() => {
    const messageStream = messageStreamRef.current;
    if (!messageStream) {
      return;
    }

    const frameId = requestAnimationFrame(() => {
      messageStream.scrollTop = messageStream.scrollHeight;
    });

    return () => cancelAnimationFrame(frameId);
  }, [createSessionSending, selectedCreateSessionId, visibleMessages.length, currentJobStatus]);

  return (
    <main className="create-page create-layout" data-testid="create-workspace">
      <aside className="create-side-panel">
        <div className={`tasks-shell ${tasksExpanded ? "tasks-expanded" : ""}`}>
          <button
            aria-expanded={tasksExpanded}
            className="tasks-toggle"
            onClick={() => setTasksExpanded((current) => !current)}
            type="button"
          >
            <span>
              <strong>任务列表</strong>
              <small>查看历史任务和当前进度</small>
            </span>
            <span aria-hidden="true" className="tasks-toggle-icon">
              {tasksExpanded ? "⌃" : "⌄"}
            </span>
          </button>
          {tasksExpanded ? (
            <div className="tasks-list">
              {taskHistoryContent}
              <button className="secondary-pill full-width" onClick={onCreateNewSession} type="button">
                + 新建任务
              </button>
            </div>
          ) : null}
        </div>

        <section className="conversation-shell">
          {/* <div className="conversation-head">
            <h1>和 Agent 一起定义你的游戏</h1>
            <p>先聊创意、玩法和目标，确认后再进入生成。</p>
          </div> */}
          <div className="conversation-scroll-shell">
            <div className="message-stream" ref={messageStreamRef}>
              {visibleMessages.map((message) => {
                const card = message.card;
                return (
                  <article
                    className={`message-row ${message.role === "user" ? "user" : "agent"}`}
                    key={message.id}
                  >
                    <span className="message-avatar">
                      {message.role === "user" && currentUser?.avatar_url ? (
                        <img
                          className="message-avatar-image"
                          src={currentUser.avatar_url}
                          alt=""
                          aria-hidden="true"
                        />
                      ) : message.role === "user" ? (
                        <span className="message-avatar-default" aria-hidden="true">
                          {getUserAvatarInitial(currentUser)}
                        </span>
                      ) : (
                        "AI"
                      )}
                    </span>
                    {card ? (
                      <div className={`confirm-card ${isCardLoading ? "loading" : ""}`}>
                        {isCardLoading ? <div className="confirm-card-status">生成中...</div> : null}
                        <h2>{card.title}</h2>
                        <p>{card.introduction}</p>
                        {shouldShowCardActions ? (
                          <div className="confirm-card-actions">
                            <button
                              className="primary-pill"
                              disabled={isConversationLocked || createSessionSending}
                              onClick={() => void onConfirmCard()}
                              type="button"
                            >
                              确认
                            </button>
                            <button
                              className="secondary-pill"
                              disabled={isConversationLocked || createSessionSending}
                              onClick={() => void onRegenerateCard()}
                              type="button"
                            >
                              重新生成
                            </button>
                          </div>
                        ) : null}
                      </div>
                    ) : (
                      <div className="message-bubble">
                        {message.content.trim().length > 0 ? (
                          <div className="message-content">{message.content}</div>
                        ) : null}
                        {message.attachments.length > 0 ? (
                          <div className="message-attachments">
                            {message.attachments.map((attachment) => (
                              <span className="message-attachment-chip" key={attachment.id}>
                                {attachment.name}
                              </span>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    )}
                  </article>
                );
              })}

              {suggestions.length > 0 ? (
                <div className="suggestion-row" role="group" aria-label="建议答案">
                  {suggestions.map((suggestion) => (
                    <button
                      className="suggestion-chip"
                      disabled={isConversationLocked || createSessionSending}
                      key={suggestion}
                      onClick={() => handleSuggestionSelect(suggestion)}
                      type="button"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              ) : null}

              {fallbackCard ? (
                <article className="message-row agent">
                  <span className="message-avatar">AI</span>
                  <div className={`confirm-card ${isCardLoading ? "loading" : ""}`}>
                    {isCardLoading ? <div className="confirm-card-status">生成中...</div> : null}
                    <h2>{fallbackCard.title}</h2>
                    <p>{fallbackCard.introduction}</p>
                    {shouldShowCardActions ? (
                      <div className="confirm-card-actions">
                        <button
                          className="primary-pill"
                          disabled={isConversationLocked || createSessionSending}
                          onClick={() => void onConfirmCard()}
                          type="button"
                        >
                          确认
                        </button>
                        <button
                          className="secondary-pill"
                          disabled={isConversationLocked || createSessionSending}
                          onClick={() => void onRegenerateCard()}
                          type="button"
                        >
                          重新生成
                        </button>
                      </div>
                    ) : null}
                  </div>
                </article>
              ) : null}

              {shouldShowRevisionPrompt ? (
                <article className="message-row agent">
                  <span className="message-avatar">AI</span>
                  <div className="message-bubble">
                    <div className="message-content">{revisionPromptMessage}</div>
                  </div>
                </article>
              ) : null}
            </div>
          </div>

          <div className="composer-shell">
            {visibleFiles.length > 0 ? (
              <div className="selected-files">
                {visibleFiles.map((file) => (
                  <span className={`selected-file-chip ${file.status}`} key={file.id}>
                    <span className="selected-file-name">{file.name}</span>
                    <span className="selected-file-status">
                      {file.status === "pending"
                        ? "待发送"
                        : file.status === "uploading"
                          ? "上传中"
                          : "上传失败"}
                    </span>
                    {file.error ? <span className="selected-file-error">{file.error}</span> : null}
                    {file.status === "failed" && file.file ? (
                      <button
                        className="retry-file-button"
                        disabled={isConversationLocked || createSessionSending}
                        onClick={() => handleRetryFile(file)}
                        type="button"
                      >
                        重试
                      </button>
                    ) : null}
                    <button
                      aria-label={`删除附件 ${file.name}`}
                      className="remove-file-button"
                      disabled={isConversationLocked}
                      onClick={() => handleRemoveFile(file.id)}
                      type="button"
                    >
                      x
                    </button>
                  </span>
                ))}
              </div>
            ) : null}
            <div className="composer-input-wrap">
              <textarea
                disabled={isConversationLocked || createSessionSending}
                onChange={(event) => setComposerText(event.target.value)}
                onKeyDown={handleComposerKeyDown}
                placeholder=""
                value={composerText}
              />
              <input
                className="sr-only"
                disabled={isConversationLocked}
                onChange={handleFileSelect}
                ref={fileInputRef}
                type="file"
                multiple
              />
              <div className="composer-floating-actions">
                <button
                  className="icon-button"
                  disabled={isConversationLocked || createSessionSending}
                  aria-label="附件"
                  onClick={() => fileInputRef.current?.click()}
                  type="button"
                >
                  📎
                </button>
                <button
                  className="primary-pill"
                  disabled={isConversationLocked || createSessionSending}
                  onClick={() => void handleSubmitMessage()}
                  type="button"
                >
                  {createSessionSending ? "发送中" : "发送"}
                </button>
              </div>
            </div>
          </div>
        </section>
      </aside>

      <section className="workspace-stage">
        <div
          className={`generate-panel ${shouldShowGenerateEmptyState ? "empty" : currentJobStatus === "succeeded" ? "succeeded" : "in-progress"}`}
        >
          {shouldShowGenerateEmptyState ? (
            <div className="generate-panel-empty-state">
              还没有开始生成游戏？去和AI聊聊想要生成什么样的游戏吧！
            </div>
          ) : currentJobStatus === "succeeded" ? (
            <>
              <div className="workspace-head">
                {/* <h1>生成游戏显示面板</h1> */}
                {/* <p>这里展示当前任务状态、预览结果和 Agent 执行进度。</p> */}
              </div>
              <div className="preview-frame preview-sandbox" aria-label="游戏沙盒区域">
                {!hasStartedPreview ? (
                  <div
                    className="preview-cover-stage"
                    style={{ backgroundImage: `url("${previewCoverUrl}")` }}
                  >
                    <img
                      alt={selectedTask?.title ? `${selectedTask.title} 封面` : "游戏封面"}
                      className="preview-cover-image"
                      onError={(event) => {
                        if (event.currentTarget.src !== fallbackCoverUrl) {
                          event.currentTarget.src = fallbackCoverUrl;
                        }
                      }}
                      src={previewCoverUrl}
                    />
                    <div className="preview-cover-scrim" />
                    <div className="preview-cover-panel">
                      <p className="preview-cover-kicker">Draft Preview</p>
                      <strong>{selectedTask?.title ?? "游戏预览"}</strong>
                      <button
                        className="primary-pill preview-start-button"
                        disabled={!selectedTask?.job_id || !previewUrls?.iframeSrc}
                        onClick={() => {
                          if (!selectedTask?.job_id) {
                            return;
                          }
                          setStartedPreviewTaskIds((current) => ({
                            ...current,
                            [selectedTask.job_id]: true,
                          }));
                        }}
                        type="button"
                      >
                        开始游玩
                      </button>
                    </div>
                  </div>
                ) : previewUrls?.iframeSrc ? (
                  <div className="preview-runtime-shell">
                    <iframe
                      className="preview-sandbox-iframe"
                      sandbox="allow-scripts allow-same-origin"
                      scrolling="no"
                      src={previewUrls.iframeSrc}
                      title={selectedTask?.title ?? "游戏预览"}
                    />
                  </div>
                ) : (
                  <span>预览地址暂不可用</span>
                )}
              </div>
              <div className="action-row preview-actions">
                
                <button
                  className="primary-pill"
                  disabled={!selectedTask?.game_id || isPublishingSelectedGame}
                  onClick={() =>
                    void (selectedTask ? onPublishGame(selectedTask) : Promise.resolve(false))
                  }
                  type="button"
                >
                  {isPublishingSelectedGame ? "发布中" : "发布"}
                </button>
              </div>
            </>
          ) : (
            <>
              <div className="workspace-head">
                {/* <h1>生成游戏显示面板</h1> */}
                {/* <p>这里展示当前任务状态、预览结果和 Agent 执行进度。</p> */}
              </div>
              <div className="agent-status-scroll">
                <div className="agent-log">
                  {jobProgress.steps.map((step) => (
                    <div key={step.label}>
                      <span>{step.label}</span>
                      <span className={`badge ${step.status}`}>{step.status}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="progress-row">
                <span>{jobProgress.label}</span>
                <div className="progress-track" aria-hidden="true">
                  <div className="progress-fill" style={{ width: `${jobProgress.percent}%` }} />
                </div>
                <span>{jobProgress.percent}%</span>
              </div>
              <section className="agent-log-stream" aria-label="Agent 执行日志">
                <div className="agent-log-stream-head">
                  <strong>Agent 执行日志</strong>
                  <span>{agentLogs.length} 条</span>
                </div>
                {agentLogsError ? (
                  <p className="agent-log-empty">{agentLogsError.message}</p>
                ) : agentLogs.length === 0 ? (
                  <p className="agent-log-empty">等待 Agent 日志</p>
                ) : (
                  agentLogs.map((log, index) => (
                    <article
                      className={`agent-log-entry ${log.level}`}
                      key={`${log.step}-${log.created_at}-${index}`}
                    >
                      <div className="agent-log-meta">
                        <span>{log.step}</span>
                        <span className={`badge ${log.level === "error" ? "failed" : log.level}`}>
                          {log.level}
                        </span>
                      </div>
                      <p>{log.message}</p>
                    </article>
                  ))
                )}
              </section>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
