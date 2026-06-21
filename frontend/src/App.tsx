import { useEffect, useMemo, useRef, useState } from "react";
import { Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";

import {
  getCurrentUser,
  loginWithEmail,
  logout as logoutRequest,
  registerWithEmail,
  startGoogleOAuth,
  type AuthUser,
} from "./api/auth";
import { ApiError } from "./api/client";
import {
  createCreateSession,
  getCreateSession,
  sendCreateSessionEvent,
  type CreateSessionUploadedAsset,
  type CreateSessionMessage,
  type CreateSessionState,
} from "./api/create-sessions";
import { getGameDetail, likePublishedGame, listPublishedGames, publishGame } from "./api/games";
import {
  createJob,
  createRevisionJob,
  deleteJob,
  getJob,
  getJobLogs,
  listJobs,
  type JobStatus,
  type RawAgentLog,
} from "./api/jobs";
import {
  MAX_CREATE_UPLOAD_SIZE_BYTES,
  completeUpload,
  presignUpload,
  uploadFileBinary,
} from "./api/uploads";
import { AuthModal } from "./components/AuthModal";
import { TopNav } from "./components/TopNav";
import { logConsoleEvent } from "./lib/console";
import { createUserError, type UserFacingError } from "./lib/errors";
import { patchLikedGame } from "./lib/games";
import {
  createMockCreateSession,
  deleteMockJob,
  getMockCreateSession,
  getMockJob,
  getMockJobLogs,
  getMockGameDetail,
  isMockEnabled,
  likeMockGame,
  listMockGames,
  listMockJobs,
  mockAuthStore,
  sendMockCreateSessionEvent,
} from "./mock/runtime";
import { CreatePage, type CreateTaskItem } from "./pages/CreatePage";
import { HomePage } from "./pages/HomePage";
import { PlayPage } from "./pages/PlayPage";
import type { AuthMode, Game, GameSortParam } from "./types/ui";

const registerErrorTitle = "注册失败";
const loginErrorTitle = "登录失败";
const registerSuccessTitle = "注册成功";
const loginSuccessTitle = "登录成功";
const logoutErrorTitle = "退出登录失败";
const googleErrorTitle = "Google 登录失败";
const createLoginPromptTitle = "创建游戏需要先登录";
const THINKING_MESSAGE_DELAY_MS = 1000;
const JOB_POLL_INTERVAL_MS = 1500;
const CREATE_REVISION_ACK_MESSAGE = "好的，这就为您修改";
const CREATE_SUCCESS_REVISION_PROMPT = "有想要修改的地方欢迎随时告诉我～";

function buildValidationReportDetails(
  validationReport: Record<string, unknown> | null,
): string | undefined {
  if (!validationReport) {
    return undefined;
  }

  try {
    return JSON.stringify(validationReport, null, 2);
  } catch {
    return String(validationReport);
  }
}

function getOptionalJobField(job: object, field: string): unknown {
  return field in job ? (job as Record<string, unknown>)[field] : null;
}

function mapRawJobToCreateTask(job: {
  job_id: string;
  session_id: string | null;
  parent_job_id: string | null;
  game_id: string | null;
  title: string;
  status: JobStatus;
  created_at: string;
  result_summary: string | null;
  error_message: string | null;
  validation_report: Record<string, unknown> | null;
  cover_url?: string | null;
}): CreateTaskItem {
  const manifestUrl =
    typeof getOptionalJobField(job, "manifest_url") === "string"
      ? (getOptionalJobField(job, "manifest_url") as string)
      : null;
  const artifactBaseUrl =
    typeof getOptionalJobField(job, "artifact_base_url") === "string"
      ? (getOptionalJobField(job, "artifact_base_url") as string)
      : null;

  return {
    job_id: job.job_id,
    session_id: job.session_id,
    parent_job_id: job.parent_job_id,
    game_id: job.game_id,
    title: job.title,
    status: job.status,
    created_at: job.created_at,
    cover_url: typeof job.cover_url === "string" ? job.cover_url : null,
    result_summary: job.result_summary,
    error_message: job.error_message,
    validation_report: job.validation_report,
    manifest_url: manifestUrl,
    artifact_base_url: artifactBaseUrl,
  };
}

export function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const mockEnabled = isMockEnabled();
  const [createTasks, setCreateTasks] = useState<CreateTaskItem[]>([]);
  const [createTasksLoading, setCreateTasksLoading] = useState(false);
  const [createTasksError, setCreateTasksError] = useState<UserFacingError | null>(null);
  const [deletingCreateTaskId, setDeletingCreateTaskId] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedCreateSessionId, setSelectedCreateSessionId] = useState<string | null>(null);
  const [currentJobStatus, setCurrentJobStatus] = useState<JobStatus | null>(null);
  const [selectedAgentLogs, setSelectedAgentLogs] = useState<RawAgentLog[]>([]);
  const [selectedJobPollingError, setSelectedJobPollingError] =
    useState<UserFacingError | null>(null);
  const reportedFailedJobIdsRef = useRef<Set<string>>(new Set());
  const [createSession, setCreateSession] = useState<CreateSessionState | null>(null);
  const [createSessionLoading, setCreateSessionLoading] = useState(false);
  const [createSessionError, setCreateSessionError] = useState<UserFacingError | null>(null);
  const [createDialogError, setCreateDialogError] = useState<UserFacingError | null>(null);
  const [createSessionSending, setCreateSessionSending] = useState(false);
  const [publishingGameId, setPublishingGameId] = useState<string | null>(null);
  const [createSessionPendingEventType, setCreateSessionPendingEventType] = useState<
    "chat" | "upload_assets" | "regenerate" | "confirm" | null
  >(null);
  const [games, setGames] = useState<Game[]>([]);
  const [allGames, setAllGames] = useState<Game[]>([]);
  const [gamesLoading, setGamesLoading] = useState(false);
  const [gamesError, setGamesError] = useState<UserFacingError | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authDisplayName, setAuthDisplayName] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [authSubmitting, setAuthSubmitting] = useState(false);
  const [authRedirectPath, setAuthRedirectPath] = useState<string | null>(null);
  const [authDialog, setAuthDialog] = useState<UserFacingError | null>(null);
  const [authSuccessDialog, setAuthSuccessDialog] = useState<UserFacingError | null>(null);
  const [createLoginPromptOpen, setCreateLoginPromptOpen] = useState(false);
  const [authBootstrapStatus, setAuthBootstrapStatus] = useState<"loading" | "ready">(
    "loading",
  );
  const githubFeedbackVisible = true;
  const showTopNav = !location.pathname.startsWith("/play/");
  const isConversationLocked = currentJobStatus === "pending" || currentJobStatus === "running";
  const featuredGame = useMemo(() => {
    let candidate: Game | null = null;
    let bestScore = -1;

    for (const game of allGames) {
      const score = game.likeCount + game.playCount;
      if (score > bestScore) {
        candidate = game;
        bestScore = score;
      }
    }

    return candidate;
  }, [allGames]);

  useEffect(() => {
    let active = true;

    void (async () => {
      if (mockEnabled) {
        setCurrentUser(mockAuthStore.currentUser);
        setIsLoggedIn(Boolean(mockAuthStore.currentUser));
        logConsoleEvent("auth", {
          requestPath: "/api/auth/me",
          status: 200,
          businessStatus: "mock",
          user_id: mockAuthStore.currentUser?.user_id ?? "guest",
        });
        setAuthBootstrapStatus("ready");
        return;
      }

      try {
        const response = await getCurrentUser();
        if (!active) {
          return;
        }
        setCurrentUser(response.user);
        setIsLoggedIn(Boolean(response.user));
        if (response.user) {
          console.info("[auth] current user restored");
          logConsoleEvent("auth", {
            requestPath: "/api/auth/me",
            status: 200,
            businessStatus: "restored",
            user_id: response.user.user_id,
            nickname: response.user.display_name ?? response.user.email ?? "unknown",
          });
        }
      } catch (error) {
        if (!active) {
          return;
        }
        if (!(error instanceof ApiError) || error.status !== 401) {
          logConsoleEvent("auth", {
            requestPath: "/api/auth/me",
            status: error instanceof ApiError ? error.status : -1,
            businessStatus: "error",
            error_code: error instanceof ApiError ? error.code : "unknown_error",
          });
        }
        setCurrentUser(null);
        setIsLoggedIn(false);
      } finally {
        if (active) {
          setAuthBootstrapStatus("ready");
        }
      }
    })();

    return () => {
      active = false;
    };
  }, [mockEnabled]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const oauthError = params.get("authError");
    if (!oauthError) {
      return;
    }
    const userError = createUserError(
      loginErrorTitle,
      new Error(oauthError),
      "请重新登录或稍后重试。",
    );
    setAuthError(userError.message);
    setAuthDialog(userError);
    setAuthMode("login");
    setAuthOpen(true);
    window.history.replaceState({}, document.title, window.location.pathname);
  }, []);

  useEffect(() => {
    if (authBootstrapStatus !== "ready") {
      return;
    }

    let active = true;

    void (async () => {
      try {
        const response = mockEnabled
          ? listMockGames({ sort: "latest" })
          : await listPublishedGames({ sort: "latest" });

        if (!active) {
          return;
        }

        setAllGames(response.games);
      } catch (error) {
        if (!active) {
          return;
        }

        logConsoleEvent("home", {
          requestPath: "/api/games",
          status: error instanceof ApiError ? error.status : 500,
          businessStatus: "error",
          error_code: error instanceof ApiError ? error.code : "unknown_error",
          scope: "featured_catalog",
        });
      }
    })();

    return () => {
      active = false;
    };
  }, [authBootstrapStatus, isLoggedIn, mockEnabled]);

  function resetAuthForm() {
    setAuthEmail("");
    setAuthDisplayName("");
    setAuthPassword("");
    setConfirmPassword("");
    setAuthDialog(null);
    setAuthSuccessDialog(null);
    setAuthError(null);
  }

  function openAuthLoginModal() {
    setAuthMode("login");
    setAuthRedirectPath(null);
    setAuthError(null);
    setAuthMessage(null);
    setAuthDialog(null);
    setAuthSuccessDialog(null);
    setAuthOpen(true);
  }

  function openCreate() {
    logConsoleEvent("create", {
      requestPath: "create-navigation",
      status: 200,
      businessStatus: isLoggedIn ? "allowed" : "auth_required",
    });
    if (!isLoggedIn) {
      setAuthRedirectPath("/create");
      setAuthError(null);
      setAuthMessage(null);
      setCreateLoginPromptOpen(true);
      return;
    }
    navigate("/create");
    window.scrollTo({ top: 0 });
  }

  function openCreateLoginModal() {
    setCreateLoginPromptOpen(false);
    openAuthLoginModal();
  }

  function completeAuthenticatedFlow(user: AuthUser, source: "login" | "register") {
    setCurrentUser(user);
    setIsLoggedIn(true);
    setAuthOpen(false);
    resetAuthForm();
    const nextPath = authRedirectPath ?? "/";
    setAuthRedirectPath(null);
    setAuthMessage(source === "login" ? "登录成功。" : "注册成功。");
    setAuthSuccessDialog({
      title: source === "login" ? loginSuccessTitle : registerSuccessTitle,
      message: source === "login" ? "当前账号已成功登录。" : "当前账号已成功注册并登录。",
      retryHint: null,
      nextStep: "",
    });
    navigate(nextPath);
    window.scrollTo({ top: 0 });
  }

  function presentAuthFailureDialog(title: string, error: unknown, nextStep: string) {
    const userError = createUserError(title, error, nextStep);
    setAuthError(userError.message);
    setAuthDialog(userError);
    return userError;
  }

  function alertCreateBackendError(userError: UserFacingError) {
    setCreateDialogError(userError);
  }

  function prependCreateTask(task: CreateTaskItem) {
    setCreateTasks((current) => {
      const withoutDuplicate = current.filter((item) => item.job_id !== task.job_id);
      return [task, ...withoutDuplicate].sort(
        (taskA, taskB) =>
          new Date(taskB.created_at).getTime() - new Date(taskA.created_at).getTime(),
      );
    });
  }

  async function createGenerationJobFromSession(
    session: CreateSessionState,
    options: {
      fallbackTitle: string;
      eventType: "confirm";
    },
  ): Promise<boolean> {
    const { fallbackTitle, eventType } = options;
    const prompt =
      typeof session.user_requirements.intent_summary === "string"
        ? session.user_requirements.intent_summary
        : undefined;
    const job = mockEnabled
      ? {
          job_id: `mock-job-${Date.now()}`,
          session_id: session.session_id,
          status: "pending" as const,
          created_at: new Date().toISOString(),
        }
      : await createJob({
          session_id: session.session_id,
          ...(prompt ? { prompt } : {}),
        });
    const nextTask: CreateTaskItem = {
      job_id: job.job_id,
      session_id: job.session_id,
      parent_job_id: null,
      game_id: null,
      title: session.assistant_response.card?.title ?? fallbackTitle,
      status: "pending",
      created_at: job.created_at,
      cover_url: null,
      result_summary: "等待执行。",
      error_message: null,
      validation_report: null,
      manifest_url: null,
      artifact_base_url: null,
    };

    prependCreateTask(nextTask);
    setSelectedTaskId(job.job_id);
    setSelectedCreateSessionId(session.session_id);
    setCurrentJobStatus("pending");
    setSelectedAgentLogs([
      {
        step: "job",
        level: "info",
        message: "生成任务已创建，正在等待 Agent 接手。",
        created_at: job.created_at,
      },
    ]);
    setSelectedJobPollingError(null);
    logConsoleEvent("create", {
      requestPath: "/api/jobs",
      status: 201,
      businessStatus: mockEnabled ? "mock_job_created" : "job_created",
      job_id: job.job_id,
      session_id: job.session_id,
      prompt: prompt ?? null,
      event_type: eventType,
    });
    console.info("[create][debug] created job response", {
      raw_job: job,
      ui_task: nextTask,
      event_type: eventType,
    });
    return true;
  }

  async function refreshSelectedJobSnapshot(): Promise<CreateTaskItem | null> {
    if (!selectedTaskId) {
      setSelectedAgentLogs([]);
      setSelectedJobPollingError(null);
      return null;
    }

    try {
      const [job, logsResponse] = mockEnabled
        ? [getMockJob(selectedTaskId), getMockJobLogs(selectedTaskId)] as const
        : await Promise.all([getJob(selectedTaskId), getJobLogs(selectedTaskId)]);

      if (!job) {
        throw new Error("未找到当前生成任务。");
      }

      const nextTask = mapRawJobToCreateTask(job);

      setCreateTasks((current) => {
        const nextTasks = current.map((task) =>
          task.job_id === nextTask.job_id ? { ...task, ...nextTask } : task,
        );
        return nextTasks.some((task) => task.job_id === nextTask.job_id)
          ? nextTasks
          : [nextTask, ...nextTasks];
      });
      setCurrentJobStatus(nextTask.status);
      setSelectedAgentLogs(logsResponse.logs);
      setSelectedJobPollingError(null);
      console.info("[create][debug] selected job snapshot", {
        raw_job: job,
        raw_logs: logsResponse.logs,
        ui_task: nextTask,
        preview_inputs: {
          game_id: job.game_id,
          artifact_prefix: getOptionalJobField(job, "artifact_prefix"),
          manifest_url: nextTask.manifest_url,
          artifact_base_url: nextTask.artifact_base_url,
          cover_url: nextTask.cover_url,
        },
      });
      if (nextTask.status === "failed" && !reportedFailedJobIdsRef.current.has(nextTask.job_id)) {
        reportedFailedJobIdsRef.current.add(nextTask.job_id);
        setCreateDialogError({
          title: "任务生成失败",
          message: nextTask.error_message ?? "生成失败，请查看 validation_report。",
          retryHint: null,
          nextStep: "请根据 validation_report 调整素材或重试生成。",
          details: buildValidationReportDetails(nextTask.validation_report),
        });
      }

      logConsoleEvent("create", {
        requestPath: `/api/jobs/${selectedTaskId}`,
        status: 200,
        businessStatus: mockEnabled ? "mock_job_polled" : "job_polled",
        job_id: selectedTaskId,
        job_status: nextTask.status,
        log_count: logsResponse.logs.length,
      });

      return nextTask;
    } catch (error) {
      const userError = createUserError("任务状态刷新失败", error, "请稍后重试或刷新页面。");
      setSelectedJobPollingError(userError);
      logConsoleEvent("create", {
        requestPath: `/api/jobs/${selectedTaskId}`,
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "error",
        error_code: error instanceof ApiError ? error.code : "unknown_error",
      });
      return null;
    }
  }

  useEffect(() => {
    if (!selectedTaskId) {
      setSelectedAgentLogs([]);
      setSelectedJobPollingError(null);
      return;
    }

    let active = true;
    void (async () => {
      if (!active) {
        return;
      }
      await refreshSelectedJobSnapshot();
    })();

    if (currentJobStatus !== "pending" && currentJobStatus !== "running") {
      return () => {
        active = false;
      };
    }

    const intervalId = window.setInterval(() => {
      void refreshSelectedJobSnapshot();
    }, JOB_POLL_INTERVAL_MS);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, [selectedTaskId, currentJobStatus, mockEnabled]);

  async function handleLoadGames({
    sort,
    q,
    tag,
  }: {
    sort: GameSortParam;
    q: string;
    tag: string;
  }) {
    setGamesLoading(true);
    setGamesError(null);

    try {
      const response = mockEnabled
        ? listMockGames({ sort, q, tag })
        : await listPublishedGames({ sort, q, tag });

      setGames(response.games);
      logConsoleEvent("home", {
        requestPath: "/api/games",
        status: 200,
        businessStatus: mockEnabled ? "mock_list" : "loaded",
        sort,
        tag: tag || "all",
        query: q || "all",
        count: response.games.length,
      });
    } catch (error) {
      const userError = createUserError("游戏列表加载失败", error, "请刷新页面或稍后重试。");
      setGamesError(userError);
      logConsoleEvent("home", {
        requestPath: "/api/games",
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "error",
        error_code: error instanceof ApiError ? error.code : "unknown_error",
        sort,
        tag: tag || "all",
        query: q || "all",
      });
    } finally {
      setGamesLoading(false);
    }
  }

  async function handleLoadCreateTasks() {
    if (!isLoggedIn) {
      setCreateTasks([]);
      setCreateTasksError(null);
      setCreateTasksLoading(false);
      setSelectedTaskId(null);
      setSelectedCreateSessionId(null);
      setCurrentJobStatus(null);
      setSelectedAgentLogs([]);
      setSelectedJobPollingError(null);
      setCreateSession(null);
      setCreateSessionPendingEventType(null);
      return;
    }

    setCreateTasksLoading(true);
    setCreateTasksError(null);

    try {
      const response = mockEnabled ? listMockJobs() : await listJobs();
      setCreateTasks(response.jobs.map(mapRawJobToCreateTask));
      const recoverableTask = response.jobs.find((task) => task.session_id);
      if (recoverableTask) {
        void handleSelectCreateTask(recoverableTask);
      } else if (location.pathname === "/create") {
        void handleCreateNewSession();
      }
      logConsoleEvent("create", {
        requestPath: "/api/jobs",
        status: 200,
        businessStatus: mockEnabled ? "mock_jobs" : "loaded",
        count: response.jobs.length,
      });
    } catch (error) {
      const userError = createUserError("任务历史加载失败", error, "请刷新页面或稍后重试。");
      setCreateTasksError(userError);
      alertCreateBackendError(userError);
      logConsoleEvent("create", {
        requestPath: "/api/jobs",
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "error",
        error_code: error instanceof ApiError ? error.code : "unknown_error",
      });
    } finally {
      setCreateTasksLoading(false);
    }
  }

  async function handleCreateNewSession() {
    setSelectedTaskId(null);
    setCurrentJobStatus(null);
    setSelectedAgentLogs([]);
    setSelectedJobPollingError(null);
    setCreateSessionPendingEventType(null);
    setCreateSessionLoading(true);
    setCreateSessionError(null);
    setCreateDialogError(null);

    try {
      const session = mockEnabled ? createMockCreateSession() : await createCreateSession();
      setCreateSession(session);
      setSelectedCreateSessionId(session.session_id);
      logConsoleEvent("create", {
        requestPath: "/api/create-sessions",
        status: mockEnabled ? 200 : 201,
        businessStatus: mockEnabled ? "mock_created" : "created",
        selected_task_id: null,
        selected_create_session_id: session.session_id,
        message_count: session.messages.length,
      });
    } catch (error) {
      const userError = createUserError("Create 会话创建失败", error, "请稍后重试或刷新页面。");
      setCreateSessionError(userError);
      alertCreateBackendError(userError);
      logConsoleEvent("create", {
        requestPath: "/api/create-sessions",
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "error",
        error_code: error instanceof ApiError ? error.code : "unknown_error",
      });
    } finally {
      setCreateSessionLoading(false);
    }
  }

  async function handleSelectCreateTask(task: CreateTaskItem) {
    setSelectedTaskId(task.job_id);
    setCurrentJobStatus(task.status);
    setCreateSessionError(null);
    setCreateDialogError(null);

    if (!task.session_id) {
      setSelectedCreateSessionId(null);
      setCreateSession(null);
      setCreateSessionPendingEventType(null);
      logConsoleEvent("create", {
        requestPath: "/api/jobs",
        status: 200,
        businessStatus: "task_without_session",
        job_id: task.job_id,
      });
      return;
    }

    setCreateSessionLoading(true);
    setSelectedCreateSessionId(task.session_id);
    setCreateSessionPendingEventType(null);

    try {
      const session = mockEnabled
        ? getMockCreateSession(task.session_id)
        : await getCreateSession(task.session_id);

      if (!session) {
        throw new Error("未找到该任务关联的 Create 会话。");
      }

      setCreateSession(session);
      logConsoleEvent("create", {
        requestPath: `/api/create-sessions/${task.session_id}`,
        status: 200,
        businessStatus: mockEnabled ? "mock_restored" : "restored",
        job_id: task.job_id,
        selected_create_session_id: session.session_id,
        conversation_status: session.conversation_status,
        message_count: session.messages.length,
      });
    } catch (error) {
      const userError = createUserError("Create 会话恢复失败", error, "可以重新新建任务。");
      setCreateSessionError(userError);
      alertCreateBackendError(userError);
      setCreateSession(null);
      logConsoleEvent("create", {
        requestPath: `/api/create-sessions/${task.session_id}`,
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "error",
        job_id: task.job_id,
        error_code: error instanceof ApiError ? error.code : "unknown_error",
      });
    } finally {
      setCreateSessionLoading(false);
    }
  }

  async function handleDeleteCreateTask(task: CreateTaskItem): Promise<boolean> {
    if (deletingCreateTaskId) {
      return false;
    }

    setDeletingCreateTaskId(task.job_id);

    try {
      if (mockEnabled) {
        deleteMockJob(task.job_id);
      } else {
        await deleteJob(task.job_id);
      }

      reportedFailedJobIdsRef.current.delete(task.job_id);
      const remainingTasks = createTasks
        .filter((item) => item.job_id !== task.job_id)
        .sort(
          (taskA, taskB) =>
            new Date(taskB.created_at).getTime() - new Date(taskA.created_at).getTime(),
        );
      setCreateTasks(remainingTasks);

      logConsoleEvent("create", {
        requestPath: `/api/jobs/${task.job_id}`,
        status: 204,
        businessStatus: mockEnabled ? "mock_deleted" : "deleted",
        job_id: task.job_id,
      });

      if (selectedTaskId === task.job_id) {
        if (remainingTasks.length > 0) {
          void handleSelectCreateTask(remainingTasks[0]);
        } else {
          void handleCreateNewSession();
        }
      }

      return true;
    } catch (error) {
      const userError = createUserError("删除任务失败", error, "请稍后重试。");
      setCreateSessionError(userError);
      alertCreateBackendError(userError);
      logConsoleEvent("create", {
        requestPath: `/api/jobs/${task.job_id}`,
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "error",
        error_code: error instanceof ApiError ? error.code : "unknown_error",
      });
      return false;
    } finally {
      setDeletingCreateTaskId(null);
    }
  }

  async function handleSendCreateMessage(message: string): Promise<boolean> {
    const normalizedMessage = message.trim();
    if (!normalizedMessage) {
      const userError = createUserError(
        "消息发送失败",
        new Error("请输入要发送的内容。"),
        "输入游戏创意或补充要求后再发送。",
      );
      setCreateSessionError(userError);
      return false;
    }

    if (!selectedCreateSessionId || !createSession) {
      const userError = createUserError(
        "消息发送失败",
        new Error("当前没有可用的 Create 会话。"),
        "请先新建任务后再发送。",
      );
      setCreateSessionError(userError);
      return false;
    }

    const canReviseGeneratedGame =
      currentJobStatus === "succeeded" &&
      Boolean(selectedTaskId) &&
      createSession.conversation_status === "confirmed";

    if (
      isConversationLocked ||
      createSessionSending ||
      (!["collecting", "ready_to_confirm"].includes(createSession.conversation_status) &&
        !canReviseGeneratedGame)
    ) {
      return false;
    }

    if (canReviseGeneratedGame && selectedTaskId) {
      return createRevisionJobFromChat({
        message: normalizedMessage,
        sourceTaskId: selectedTaskId,
        session: createSession,
      });
    }

    const currentSessionId = selectedCreateSessionId;
    setCreateSessionSending(true);
    setCreateSessionPendingEventType("chat");
    setCreateSessionError(null);

    const optimisticMessage: CreateSessionMessage = {
      id: `optimistic-${currentSessionId}-${Date.now()}-user`,
      role: "user",
      content: normalizedMessage,
      payload: { optimistic: true },
      created_at: new Date().toISOString(),
    };
    const thinkingMessage: CreateSessionMessage = {
      id: `optimistic-${currentSessionId}-${Date.now()}-assistant`,
      role: "assistant",
      content: "思考中...",
      payload: { optimistic: true },
      created_at: new Date().toISOString(),
    };
    let thinkingMessageTimerId: number | null = null;

    setCreateSession((current) => {
      if (!current || current.session_id !== currentSessionId) {
        return current;
      }

      return {
        ...current,
        messages: [...current.messages, optimisticMessage],
      };
    });

    const shouldQueueThinkingMessage = !createSession.assistant_response.card;
    if (shouldQueueThinkingMessage) {
      thinkingMessageTimerId = window.setTimeout(() => {
        setCreateSession((current) => {
          if (!current || current.session_id !== currentSessionId) {
            return current;
          }

          const hasThinkingMessage = current.messages.some((item) => item.id === thinkingMessage.id);
          if (hasThinkingMessage) {
            return current;
          }

          return {
            ...current,
            messages: [...current.messages, thinkingMessage],
          };
        });
      }, THINKING_MESSAGE_DELAY_MS);
    }

    try {
      const session = mockEnabled
        ? sendMockCreateSessionEvent(currentSessionId, {
            type: "chat",
            message: normalizedMessage,
          })
        : await sendCreateSessionEvent(currentSessionId, {
            type: "chat",
            message: normalizedMessage,
          });

      setCreateSession(session);
      setSelectedCreateSessionId(session.session_id);
      logConsoleEvent("create", {
        requestPath: `/api/create-sessions/${currentSessionId}/events`,
        status: 200,
        businessStatus: mockEnabled ? "mock_chat_sent" : "chat_sent",
        event_type: "chat",
        selected_create_session_id: session.session_id,
        conversation_status: session.conversation_status,
        message_count: session.messages.length,
        suggestion_count: session.assistant_response.suggestions.length,
      });
      return true;
    } catch (error) {
      setCreateSession((current) => {
        if (!current || current.session_id !== currentSessionId) {
          return current;
        }

        return {
          ...current,
          messages: current.messages.filter(
            (item) => item.id !== optimisticMessage.id && item.id !== thinkingMessage.id,
          ),
        };
      });
      const userError = createUserError("消息发送失败", error, "请稍后重试。");
      setCreateSessionError(userError);
      alertCreateBackendError(userError);
      logConsoleEvent("create", {
        requestPath: `/api/create-sessions/${currentSessionId}/events`,
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "error",
        event_type: "chat",
        error_code: error instanceof ApiError ? error.code : "unknown_error",
      });
      return false;
    } finally {
      if (thinkingMessageTimerId !== null) {
        window.clearTimeout(thinkingMessageTimerId);
      }
      setCreateSessionSending(false);
      setCreateSessionPendingEventType(null);
    }
  }

  async function handleRegenerateCreateCard(): Promise<boolean> {
    if (!selectedCreateSessionId || !createSession) {
      const userError = createUserError(
        "重新生成失败",
        new Error("当前没有可用的 Create 会话。"),
        "请先恢复或新建任务后再试。",
      );
      setCreateSessionError(userError);
      return false;
    }

    if (createSession.conversation_status !== "ready_to_confirm") {
      const userError = createUserError(
        "重新生成失败",
        new Error("当前方案还不能重新生成。"),
        "请先等待可确认卡片出现后再试。",
      );
      setCreateSessionError(userError);
      return false;
    }

    const currentCard = createSession.assistant_response.card;
    if (!currentCard) {
      const userError = createUserError(
        "重新生成失败",
        new Error("当前没有可用的方案卡片。"),
        "请先生成一张可确认卡片后再试。",
      );
      setCreateSessionError(userError);
      return false;
    }

    if (isConversationLocked || createSessionSending) {
      return false;
    }

    setCreateSessionSending(true);
    setCreateSessionPendingEventType("regenerate");
    setCreateSessionError(null);

    try {
      const session = mockEnabled
        ? sendMockCreateSessionEvent(selectedCreateSessionId, {
            type: "regenerate",
            selected_plan_id: currentCard.plan_id,
          })
        : await sendCreateSessionEvent(selectedCreateSessionId, {
            type: "regenerate",
            selected_plan_id: currentCard.plan_id,
          });

      setCreateSession(session);
      setSelectedCreateSessionId(session.session_id);
      logConsoleEvent("create", {
        requestPath: `/api/create-sessions/${selectedCreateSessionId}/events`,
        status: 200,
        businessStatus: mockEnabled ? "mock_regenerated" : "regenerated",
        event_type: "regenerate",
        selected_create_session_id: session.session_id,
        selected_plan_id: currentCard.plan_id,
        next_plan_id: session.assistant_response.card?.plan_id ?? null,
        conversation_status: session.conversation_status,
        message_count: session.messages.length,
      });
      return true;
    } catch (error) {
      const userError = createUserError("重新生成失败", error, "请稍后重试。");
      setCreateSessionError(userError);
      alertCreateBackendError(userError);
      logConsoleEvent("create", {
        requestPath: `/api/create-sessions/${selectedCreateSessionId}/events`,
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "error",
        event_type: "regenerate",
        selected_plan_id: currentCard.plan_id,
        error_code: error instanceof ApiError ? error.code : "unknown_error",
      });
      return false;
    } finally {
      setCreateSessionSending(false);
      setCreateSessionPendingEventType(null);
    }
  }

  async function handleConfirmCreateCard(): Promise<boolean> {
    if (!selectedCreateSessionId || !createSession) {
      const userError = createUserError(
        "创建任务失败",
        new Error("当前没有可用的 Create 会话。"),
        "请先恢复或新建任务后再试。",
      );
      setCreateSessionError(userError);
      return false;
    }

    if (createSession.conversation_status !== "ready_to_confirm") {
      const userError = createUserError(
        "创建任务失败",
        new Error("当前方案还不能确认生成。"),
        "请先等待可确认卡片出现后再试。",
      );
      setCreateSessionError(userError);
      return false;
    }

    const currentCard = createSession.assistant_response.card;
    if (!currentCard) {
      const userError = createUserError(
        "创建任务失败",
        new Error("当前没有可用的方案卡片。"),
        "请先生成一张可确认卡片后再试。",
      );
      setCreateSessionError(userError);
      return false;
    }

    if (isConversationLocked || createSessionSending) {
      return false;
    }

    setCreateSessionSending(true);
    setCreateSessionPendingEventType("confirm");
    setCreateSessionError(null);

    try {
      const confirmedSession = mockEnabled
        ? sendMockCreateSessionEvent(selectedCreateSessionId, {
            type: "confirm",
            selected_plan_id: currentCard.plan_id,
          })
        : await sendCreateSessionEvent(selectedCreateSessionId, {
            type: "confirm",
            selected_plan_id: currentCard.plan_id,
          });

      setCreateSession(confirmedSession);
      setSelectedCreateSessionId(confirmedSession.session_id);
      logConsoleEvent("create", {
        requestPath: `/api/create-sessions/${selectedCreateSessionId}/events`,
        status: 200,
        businessStatus: mockEnabled ? "mock_confirmed" : "confirmed",
        event_type: "confirm",
        selected_create_session_id: confirmedSession.session_id,
        selected_plan_id: currentCard.plan_id,
        conversation_status: confirmedSession.conversation_status,
        handoff_to_generation: confirmedSession.handoff_to_generation ?? false,
      });

      if (!confirmedSession.handoff_to_generation) {
        const userError = createUserError(
          "创建任务失败",
          new Error("当前会话尚未准备好进入生成阶段。"),
          "请稍后重试。",
        );
        setCreateSessionError(userError);
        alertCreateBackendError(userError);
        return false;
      }

      return await createGenerationJobFromSession(confirmedSession, {
        fallbackTitle: currentCard.title,
        eventType: "confirm",
      });
    } catch (error) {
      const userError = createUserError("创建任务失败", error, "请稍后重试。");
      setCreateSessionError(userError);
      alertCreateBackendError(userError);
      logConsoleEvent("create", {
        requestPath: "/api/jobs",
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "error",
        event_type: "confirm",
        error_code: error instanceof ApiError ? error.code : "unknown_error",
      });
      return false;
    } finally {
      setCreateSessionSending(false);
      setCreateSessionPendingEventType(null);
    }
  }

  async function createRevisionJobFromChat({
    message,
    sourceTaskId,
    session,
  }: {
    message: string;
    sourceTaskId: string;
    session: CreateSessionState;
  }): Promise<boolean> {
    const now = new Date().toISOString();
    const optimisticMessage: CreateSessionMessage = {
      id: `optimistic-${session.session_id}-${Date.now()}-revision-user`,
      role: "user",
      content: message,
      payload: { optimistic: true, event_type: "revision_request" },
      created_at: now,
    };
    const revisionAckMessage: CreateSessionMessage = {
      id: `optimistic-${session.session_id}-${Date.now()}-revision-assistant`,
      role: "assistant",
      content: CREATE_REVISION_ACK_MESSAGE,
      payload: { optimistic: true, event_type: "revision_ack" },
      created_at: now,
    };

    setCreateSessionSending(true);
    setCreateSessionPendingEventType(null);
    setCreateSessionError(null);
    setCreateSession((current) => {
      if (!current || current.session_id !== session.session_id) {
        return current;
      }

      return {
        ...current,
        messages: [...current.messages, optimisticMessage, revisionAckMessage],
      };
    });

    try {
      const fallbackTitle =
        session.assistant_response.card?.title ??
        (typeof session.game_plan?.title === "string" ? session.game_plan.title : null) ??
        createTasks.find((task) => task.job_id === sourceTaskId)?.title ??
        "未命名游戏";
      const sourceTask = createTasks.find((task) => task.job_id === sourceTaskId) ?? null;
      const job = mockEnabled
        ? {
            job_id: `mock-revision-job-${Date.now()}`,
            session_id: session.session_id,
            parent_job_id: sourceTaskId,
            revision_intent: message,
            status: "pending" as const,
            created_at: new Date().toISOString(),
          }
        : await createRevisionJob(sourceTaskId, { message });
      const nextTask: CreateTaskItem = {
        job_id: job.job_id,
        session_id: job.session_id ?? session.session_id,
        parent_job_id: job.parent_job_id ?? sourceTaskId,
        game_id: null,
        title: `${sourceTask?.title ?? fallbackTitle} 修改`,
        status: "pending",
        created_at: job.created_at,
        cover_url: null,
        result_summary: "等待执行。",
        error_message: null,
        validation_report: null,
        manifest_url: null,
        artifact_base_url: null,
      };

      prependCreateTask(nextTask);
      setSelectedTaskId(job.job_id);
      setSelectedCreateSessionId(session.session_id);
      setCurrentJobStatus("pending");
      setSelectedAgentLogs([
        {
          step: "revision_job",
          level: "info",
          message: "修改任务已创建，正在基于上一版游戏生成新版本。",
          created_at: job.created_at,
        },
      ]);
      setSelectedJobPollingError(null);
      logConsoleEvent("create", {
        requestPath: `/api/jobs/${sourceTaskId}/revisions`,
        businessStatus: mockEnabled ? "mock_chat_revision_job_created" : "chat_revision_job_created",
        job_id: job.job_id,
        parent_job_id: job.parent_job_id ?? sourceTaskId,
        session_id: job.session_id ?? session.session_id,
        revision_intent: job.revision_intent ?? message,
        event_type: "chat_revision",
      });
      console.info("[create][debug] created revision job response", {
        raw_job: job,
        ui_task: nextTask,
        revision_intent: job.revision_intent ?? message,
      });
      return true;
    } catch (error) {
      setCreateSession((current) => {
        if (!current || current.session_id !== session.session_id) {
          return current;
        }

        return {
          ...current,
          messages: current.messages.filter(
            (item) => item.id !== optimisticMessage.id && item.id !== revisionAckMessage.id,
          ),
        };
      });
      const userError = createUserError("修改失败", error, "请稍后重试。");
      setCreateSessionError(userError);
      alertCreateBackendError(userError);
      logConsoleEvent("create", {
        requestPath: `/api/jobs/${sourceTaskId}/revisions`,
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "error",
        event_type: "chat_revision",
        error_code: error instanceof ApiError ? error.code : "unknown_error",
      });
      return false;
    } finally {
      setCreateSessionSending(false);
      setCreateSessionPendingEventType(null);
    }
  }

  async function handleUploadCreateFiles(files: File[]): Promise<boolean> {
    if (!selectedCreateSessionId || !createSession) {
      const userError = createUserError(
        "文件上传失败",
        new Error("当前没有可用的 Create 会话。"),
        "请先新建任务后再上传素材。",
      );
      setCreateSessionError(userError);
      alertCreateBackendError(userError);
      return false;
    }

    if (
      isConversationLocked ||
      createSessionSending ||
      !["collecting", "ready_to_confirm"].includes(createSession.conversation_status)
    ) {
      return false;
    }

    const oversizedFile = files.find((file) => file.size > MAX_CREATE_UPLOAD_SIZE_BYTES);
    if (oversizedFile) {
      const userError = createUserError(
        "文件上传失败",
        new Error(`${oversizedFile.name} 超过 20MB。`),
        "请选择 20MB 以内的文件。",
      );
      setCreateSessionError(userError);
      alertCreateBackendError(userError);
      return false;
    }

    setCreateSessionSending(true);
    setCreateSessionPendingEventType("upload_assets");
    setCreateSessionError(null);

    try {
      const uploadedAssets: CreateSessionUploadedAsset[] = [];

      if (mockEnabled) {
        for (const file of files) {
          uploadedAssets.push({
            asset_id: `mock-asset-${Date.now()}-${uploadedAssets.length}`,
            filename: file.name,
            mime_type: file.type || "application/octet-stream",
            size_bytes: file.size,
            object_key: `uploads/mock/${file.name}`,
            user_hint: null,
          });
        }
      } else {
        for (const file of files) {
          const draft = await presignUpload(file);
          await uploadFileBinary(draft.upload_url, file);
          const completed = await completeUpload(draft, file);
          uploadedAssets.push({
            asset_id: completed.asset_id,
            filename: completed.filename,
            mime_type: completed.mime_type,
            size_bytes: completed.size_bytes,
            object_key: completed.object_key ?? draft.object_key,
            user_hint: null,
          });
        }
      }

      const nextAssets = [...createSession.material_usage.assets, ...uploadedAssets];

      const session = mockEnabled
        ? sendMockCreateSessionEvent(selectedCreateSessionId, {
            type: "upload_assets",
            uploaded_assets: nextAssets,
            replace_existing_assets: true,
          })
        : await sendCreateSessionEvent(selectedCreateSessionId, {
            type: "upload_assets",
            uploaded_assets: nextAssets,
            replace_existing_assets: true,
          });

      setCreateSession(session);
      setSelectedCreateSessionId(session.session_id);
      logConsoleEvent("create", {
        requestPath: `/api/create-sessions/${selectedCreateSessionId}/events`,
        status: 200,
        businessStatus: mockEnabled ? "mock_create_upload_bound" : "create_upload_bound",
        event_type: "upload_assets",
        selected_create_session_id: session.session_id,
        asset_count: nextAssets.length,
        material_asset_count: session.material_usage.assets.length,
        files: uploadedAssets.map((asset) => ({
          filename: asset.filename,
          size_bytes: asset.size_bytes,
          mime_type: asset.mime_type,
          object_key: asset.object_key.split("/").slice(0, 2).join("/"),
        })),
      });
      return true;
    } catch (error) {
      const userError = createUserError("文件上传失败", error, "请稍后重试或重新选择文件。");
      setCreateSessionError(userError);
      alertCreateBackendError(userError);
      logConsoleEvent("create", {
        requestPath: `/api/create-sessions/${selectedCreateSessionId}/events`,
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "create_upload_failed",
        event_type: "upload_assets",
        error_code: error instanceof ApiError ? error.code : "unknown_error",
      });
      return false;
    } finally {
      setCreateSessionSending(false);
      setCreateSessionPendingEventType(null);
    }
  }

  async function handleRemoveBoundCreateFile(assetId: string): Promise<boolean> {
    if (!selectedCreateSessionId || !createSession) {
      return false;
    }

    if (
      isConversationLocked ||
      createSessionSending ||
      !["collecting", "ready_to_confirm"].includes(createSession.conversation_status)
    ) {
      return false;
    }

    const remainingAssets = createSession.material_usage.assets.filter(
      (asset) => asset.asset_id !== assetId,
    );

    setCreateSessionSending(true);
    setCreateSessionPendingEventType("upload_assets");
    setCreateSessionError(null);

    try {
      const session = mockEnabled
        ? sendMockCreateSessionEvent(selectedCreateSessionId, {
            type: "upload_assets",
            uploaded_assets: remainingAssets,
            replace_existing_assets: true,
          })
        : await sendCreateSessionEvent(selectedCreateSessionId, {
            type: "upload_assets",
            uploaded_assets: remainingAssets,
            replace_existing_assets: true,
          });

      setCreateSession(session);
      setSelectedCreateSessionId(session.session_id);
      logConsoleEvent("create", {
        requestPath: `/api/create-sessions/${selectedCreateSessionId}/events`,
        status: 200,
        businessStatus: mockEnabled ? "mock_create_upload_bound" : "create_upload_bound",
        event_type: "upload_assets",
        selected_create_session_id: session.session_id,
        asset_count: remainingAssets.length,
        material_asset_count: session.material_usage.assets.length,
      });
      return true;
    } catch (error) {
      const userError = createUserError("删除附件失败", error, "请稍后重试。");
      setCreateSessionError(userError);
      alertCreateBackendError(userError);
      logConsoleEvent("create", {
        requestPath: `/api/create-sessions/${selectedCreateSessionId}/events`,
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "create_upload_failed",
        event_type: "upload_assets",
        error_code: error instanceof ApiError ? error.code : "unknown_error",
      });
      return false;
    } finally {
      setCreateSessionSending(false);
      setCreateSessionPendingEventType(null);
    }
  }

  async function handleAuthSubmit() {
    const email = authEmail.trim().toLowerCase();
    const displayName = authDisplayName.trim();
    const password = authPassword;

    setAuthError(null);
    setAuthMessage(null);
    setAuthDialog(null);
    setAuthSuccessDialog(null);

    if (!email || !email.includes("@")) {
      presentAuthFailureDialog(
        authMode === "login" ? loginErrorTitle : registerErrorTitle,
        new Error("请输入有效的邮箱地址。"),
        "请填写正确的邮箱格式后重试。",
      );
      return;
    }

    if (password.length < 8) {
      presentAuthFailureDialog(
        authMode === "login" ? loginErrorTitle : registerErrorTitle,
        new Error("密码至少需要 8 位，且必须同时包含字母和数字。"),
        "请按密码规则修改后重试。",
      );
      return;
    }

    const hasLetter = /[A-Za-z]/.test(password);
    const hasDigit = /\d/.test(password);
    if (!hasLetter || !hasDigit) {
      presentAuthFailureDialog(
        authMode === "login" ? loginErrorTitle : registerErrorTitle,
        new Error("密码至少需要 8 位，且必须同时包含字母和数字。"),
        "请按密码规则修改后重试。",
      );
      return;
    }

    if (authMode === "register" && password !== confirmPassword) {
      presentAuthFailureDialog(
        registerErrorTitle,
        new Error("两次输入的密码不一致。"),
        "请确认两次密码保持一致。",
      );
      return;
    }

    if (authMode === "register" && !displayName) {
      presentAuthFailureDialog(
        registerErrorTitle,
        new Error("请输入昵称。"),
        "请填写昵称后重试。",
      );
      return;
    }

    setAuthSubmitting(true);
    try {
      const response = mockEnabled
        ? {
            user: {
              user_id: "mock-user",
              email,
              display_name: displayName || email.split("@", 1)[0],
              avatar_url: null,
            },
          }
        : authMode === "login"
          ? await loginWithEmail(email, password)
          : await registerWithEmail({
              email,
              password,
              display_name: displayName,
              avatar_url: null,
            });
      if (!response.user) {
        throw new Error("Auth response is missing user data.");
      }
      if (mockEnabled) {
        mockAuthStore.currentUser = response.user;
      }
      completeAuthenticatedFlow(response.user, authMode);
      if (authMode === "login") {
        console.info("[auth] login success");
      } else {
        console.info("[auth] register success");
      }
      logConsoleEvent("auth", {
        requestPath: authMode === "login" ? "/api/auth/login" : "/api/auth/register",
        status: authMode === "login" ? 200 : 201,
        businessStatus: authMode,
        user_id: response.user.user_id,
        nickname: response.user.display_name?.trim() || response.user.email || "unknown",
      });
    } catch (error) {
      const userError = presentAuthFailureDialog(
        authMode === "login" ? loginErrorTitle : registerErrorTitle,
        error,
        "请检查邮箱或密码后重试。",
      );
      logConsoleEvent("auth", {
        requestPath: authMode === "login" ? "/api/auth/login" : "/api/auth/register",
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "error",
        error_code: error instanceof ApiError ? error.code : "unknown_error",
        retry_hint: userError.retryHint,
      });
    } finally {
      setAuthSubmitting(false);
    }
  }

  async function handleLikeGame(gameId: string) {
    if (!isLoggedIn) {
      openAuthLoginModal();
      logConsoleEvent("home", {
        requestPath: `/api/games/${gameId}/like`,
        status: 401,
        businessStatus: "auth_required",
      });
      return;
    }

    try {
      const likedGame = mockEnabled ? likeMockGame(gameId) : null;
      const response = mockEnabled
        ? {
            game_id: gameId,
            like_count: likedGame?.likeCount ?? 0,
            liked_by_me: Boolean(likedGame?.likedByMe),
          }
        : await likePublishedGame(gameId);

      setGames((currentGames) =>
        currentGames.map((game) =>
          game.id === gameId
            ? patchLikedGame(game, response.like_count, response.liked_by_me)
            : game,
        ),
      );
      setAllGames((currentGames) =>
        currentGames.map((game) =>
          game.id === gameId
            ? patchLikedGame(game, response.like_count, response.liked_by_me)
            : game,
        ),
      );
      logConsoleEvent("home", {
        requestPath: `/api/games/${gameId}/like`,
        status: 200,
        businessStatus: "liked",
        game_id: response.game_id,
        like_count: response.like_count,
      });
    } catch (error) {
      const userError = createUserError("点赞失败", error, "请稍后重试。");
      setGamesError(userError);
      logConsoleEvent("home", {
        requestPath: `/api/games/${gameId}/like`,
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "error",
        error_code: error instanceof ApiError ? error.code : "unknown_error",
      });
    }
  }

  async function handlePublishCreateGame(task: CreateTaskItem): Promise<boolean> {
    if (!task.game_id) {
      const userError = createUserError(
        "发布失败",
        new Error("当前任务还没有可发布的 draft 游戏。"),
        "请等待生成成功后再发布。",
      );
      setCreateDialogError(userError);
      return false;
    }

    if (publishingGameId === task.game_id) {
      return false;
    }

    setPublishingGameId(task.game_id);
    setCreateDialogError(null);

    try {
      let publishedGame: Game;
      if (mockEnabled) {
        const mockGame = getMockGameDetail(task.game_id);
        if (!mockGame) {
          throw new Error("未找到 mock draft 游戏。");
        }
        publishedGame = { ...mockGame, status: "published" };
      } else {
        publishedGame = await publishGame(task.game_id);
      }

      const patchPublishedGame = (currentGames: Game[]) => {
        const withoutDuplicate = currentGames.filter((game) => game.id !== publishedGame.id);
        return [publishedGame, ...withoutDuplicate];
      };
      setGames(patchPublishedGame);
      setAllGames(patchPublishedGame);
      await handleLoadGames({ sort: "latest", q: "", tag: "" });
      console.info("Publish 成功", {
        game_id: publishedGame.id,
        job_id: task.job_id,
      });
      logConsoleEvent("create", {
        requestPath: `/api/games/${task.game_id}/publish`,
        status: 200,
        businessStatus: mockEnabled ? "mock_publish_succeeded" : "publish_succeeded",
        game_id: publishedGame.id,
        job_id: task.job_id,
      });
      navigate("/");
      window.scrollTo({ top: 0 });
      return true;
    } catch (error) {
      const userError = createUserError("发布失败", error, "请稍后重试或重新生成游戏。");
      setCreateDialogError(userError);
      logConsoleEvent("create", {
        requestPath: `/api/games/${task.game_id}/publish`,
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "publish_failed",
        game_id: task.game_id,
        job_id: task.job_id,
        error_code: error instanceof ApiError ? error.code : "unknown_error",
      });
      return false;
    } finally {
      setPublishingGameId(null);
    }
  }

  async function handleLogout() {
    setAuthError(null);
    setAuthMessage(null);
    setAuthDialog(null);
    setAuthSuccessDialog(null);
    try {
      if (!mockEnabled) {
        await logoutRequest();
      }
      mockAuthStore.currentUser = null;
      setCurrentUser(null);
      setIsLoggedIn(false);
      setCreateTasks([]);
      setCreateTasksError(null);
      setSelectedAgentLogs([]);
      setSelectedJobPollingError(null);
      setAuthRedirectPath(null);
      console.info("[auth] logout success");
      logConsoleEvent("auth", {
        requestPath: "/api/auth/logout",
        status: 204,
        businessStatus: "logged_out",
      });
      navigate("/");
      window.scrollTo({ top: 0 });
    } catch (error) {
      presentAuthFailureDialog(logoutErrorTitle, error, "请稍后重试或刷新页面。");
    }
  }

  async function handleGoogleLogin() {
    setAuthError(null);
    setAuthMessage(null);
    setAuthDialog(null);
    setAuthSuccessDialog(null);
    setAuthSubmitting(true);
    try {
      if (mockEnabled) {
        throw new ApiError(
          503,
          "mock_oauth_disabled",
          "Mock 模式下不触发真实 Google 登录。",
          "请关闭 mock 后再试。",
        );
      }
      const response = await startGoogleOAuth();
      console.info("[auth] google oauth start");
      logConsoleEvent("auth", {
        requestPath: "/api/auth/oauth/google/start",
        status: 200,
        businessStatus: "redirecting",
        provider: "google",
      });
      window.location.assign(response.authorization_url);
    } catch (error) {
      const userError = presentAuthFailureDialog(
        googleErrorTitle,
        error,
        "请稍后重试，或先使用邮箱登录。",
      );
      logConsoleEvent("auth", {
        requestPath: "/api/auth/oauth/google/start",
        status: error instanceof ApiError ? error.status : 500,
        businessStatus: "error",
        retry_hint: userError.retryHint,
      });
    } finally {
      setAuthSubmitting(false);
    }
  }

  useEffect(() => {
    if (authBootstrapStatus !== "ready") {
      return;
    }

    if (location.pathname !== "/create") {
      return;
    }

    if (!isLoggedIn) {
      setCreateTasks([]);
      setCreateTasksError(null);
      setCreateTasksLoading(false);
      return;
    }

    void handleLoadCreateTasks();
  }, [authBootstrapStatus, isLoggedIn, location.pathname, mockEnabled]);

  function openPlay(game: Game) {
    logConsoleEvent("play", {
      requestPath: `/play/${game.id}`,
      status: 200,
      businessStatus: "preview",
      game_id: game.id,
    });
    navigate(`/play/${game.id}`);
    window.scrollTo({ top: 0 });
  }

  return (
    <div className={showTopNav ? "app-shell" : "play-shell"}>
      {showTopNav ? (
        <TopNav
          isLoggedIn={isLoggedIn}
          currentUser={currentUser}
          currentPath={location.pathname}
          onHome={() => navigate("/")}
          onCreate={openCreate}
          onLogin={openAuthLoginModal}
          onLogout={handleLogout}
        />
      ) : null}

      {authBootstrapStatus === "loading" ? <div className="sr-only">正在恢复登录状态</div> : null}
      {authMessage ? <div className="sr-only">{authMessage}</div> : null}
      {authSuccessDialog ? (
        <ErrorDialog
          error={authSuccessDialog}
          variant="success"
          onClose={() => setAuthSuccessDialog(null)}
        />
      ) : null}
      {authDialog ? <ErrorDialog error={authDialog} onClose={() => setAuthDialog(null)} /> : null}
      {gamesError ? <ErrorDialog error={gamesError} onClose={() => setGamesError(null)} /> : null}
      {createDialogError ? (
        <ErrorDialog error={createDialogError} onClose={() => setCreateDialogError(null)} />
      ) : null}
      {createLoginPromptOpen ? (
        <ErrorDialog
          error={{
            title: createLoginPromptTitle,
            message: "请先登录账号再继续。",
            retryHint: null,
            nextStep: "",
          }}
          confirmLabel="去登录"
          onClose={() => setCreateLoginPromptOpen(false)}
          onConfirm={openCreateLoginModal}
        />
      ) : null}

      <Routes>
        <Route
          path="/"
          element={
            <HomePage
              featuredGame={featuredGame}
              games={games}
              isLoading={gamesLoading}
              isLoggedIn={isLoggedIn}
              onLikeGame={handleLikeGame}
              onLoadGames={handleLoadGames}
              onOpenPlay={openPlay}
              onRequireLogin={openAuthLoginModal}
            />
          }
        />
        <Route
          path="/create"
          element={
            <CreatePage
              tasks={createTasks}
              tasksLoading={createTasksLoading}
              tasksError={createTasksError}
              deletingTaskId={deletingCreateTaskId}
              selectedTaskId={selectedTaskId}
              selectedCreateSessionId={selectedCreateSessionId}
              currentJobStatus={currentJobStatus}
              agentLogs={selectedAgentLogs}
              agentLogsError={selectedJobPollingError}
              isConversationLocked={isConversationLocked}
              createSession={createSession}
              createSessionLoading={createSessionLoading}
              createSessionError={createSessionError}
              createSessionSending={createSessionSending}
              createSessionPendingEventType={createSessionPendingEventType}
              currentUser={currentUser}
              publishingGameId={publishingGameId}
              revisionPromptMessage={CREATE_SUCCESS_REVISION_PROMPT}
              onRetryTasks={handleLoadCreateTasks}
              onCreateNewSession={handleCreateNewSession}
              onSelectTask={handleSelectCreateTask}
              onDeleteTask={handleDeleteCreateTask}
              onPublishGame={handlePublishCreateGame}
              onConfirmCard={handleConfirmCreateCard}
              onRegenerateCard={handleRegenerateCreateCard}
              onSendMessage={handleSendCreateMessage}
              onUploadFiles={handleUploadCreateFiles}
              onRemoveBoundFile={handleRemoveBoundCreateFile}
            />
          }
        />
        <Route
          path="/play/:gameId"
          element={
            <PlayRoute
              games={allGames}
              mockEnabled={mockEnabled}
              onHome={() => navigate("/")}
              onLikeGame={handleLikeGame}
              onOpenGame={openPlay}
              onRequireLogin={openAuthLoginModal}
            />
          }
        />
      </Routes>

      {authOpen ? (
        <AuthModal
          mode={authMode}
          onModeChange={setAuthMode}
          authEmail={authEmail}
          authPassword={authPassword}
          confirmPassword={confirmPassword}
          authError={authError}
          authMessage={authMessage}
          authSubmitting={authSubmitting}
          authDisplayName={authDisplayName}
          githubFeedbackVisible={githubFeedbackVisible}
          onEmailChange={setAuthEmail}
          onDisplayNameChange={setAuthDisplayName}
          onPasswordChange={setAuthPassword}
          onConfirmPasswordChange={setConfirmPassword}
          onClose={() => {
            setAuthOpen(false);
            resetAuthForm();
          }}
          onSubmit={handleAuthSubmit}
          onGoogleLogin={handleGoogleLogin}
        />
      ) : null}
    </div>
  );
}

function PlayRoute({
  games,
  mockEnabled,
  onHome,
  onOpenGame,
  onLikeGame,
  onRequireLogin,
}: {
  games: Game[];
  mockEnabled: boolean;
  onHome: () => void;
  onOpenGame: (game: Game) => void;
  onLikeGame: (gameId: string) => Promise<void>;
  onRequireLogin: () => void;
}) {
  const { gameId } = useParams();
  const [loadedGame, setLoadedGame] = useState<Game | null>(null);
  const [loadingGame, setLoadingGame] = useState(false);
  const [gameError, setGameError] = useState<UserFacingError | null>(null);
  const liveGame = games.find((item) => item.id === gameId) ?? null;
  const fallbackPreview = liveGame ?? loadedGame;
  const game =
    loadedGame && liveGame
      ? {
          ...loadedGame,
          likedByMe: liveGame.likedByMe,
          likeCount: liveGame.likeCount,
          likes: liveGame.likes,
          playCount: liveGame.playCount,
          plays: liveGame.plays,
        }
      : loadedGame ?? liveGame;

  useEffect(() => {
    if (!gameId) {
      setLoadedGame(null);
      setGameError(null);
      return;
    }

    let active = true;
    setLoadingGame(true);
    setGameError(null);

    void (async () => {
      try {
        const nextGame = mockEnabled ? getMockGameDetail(gameId) : await getGameDetail(gameId);

        if (!active) {
          return;
        }

        if (!nextGame) {
          throw new Error("未找到对应游戏。");
        }

        setLoadedGame(nextGame);
      } catch (error) {
        if (!active) {
          return;
        }
        setGameError(createUserError("游戏加载失败", error, "请返回主页后重新进入。"));
      } finally {
        if (active) {
          setLoadingGame(false);
        }
      }
    })();

    return () => {
      active = false;
    };
  }, [gameId, mockEnabled]);

  if (gameError) {
    return (
      <main className="play-page play-fallback-page">
        <section className="play-fallback-card" role="alert">
          <h1>{gameError.title}</h1>
          <p>{gameError.message}</p>
          <p>{gameError.retryHint ?? gameError.nextStep}</p>
          <div className="play-fallback-actions">
            <button className="primary-pill" onClick={onHome} type="button">
              返回主页
            </button>
          </div>
        </section>
      </main>
    );
  }

  if (!game || loadingGame) {
    return (
      <main className="play-page play-fallback-page">
        <section className="play-fallback-card">
          <h1>{fallbackPreview?.title ?? "正在载入游戏"}</h1>
          <p>正在获取游戏信息，请稍候。</p>
        </section>
      </main>
    );
  }

  return (
    <PlayPage
      game={game}
      games={games.length > 0 ? games : loadedGame ? [loadedGame] : []}
      onHome={onHome}
      onLikeGame={onLikeGame}
      onOpenGame={onOpenGame}
      onRequireLogin={onRequireLogin}
    />
  );
}

function ErrorDialog({
  error,
  variant = "error",
  confirmLabel = "知道了",
  onClose,
  onConfirm,
}: {
  error: UserFacingError;
  variant?: "error" | "success";
  confirmLabel?: string;
  onClose: () => void;
  onConfirm?: () => void;
}) {
  return (
    <div className="error-dialog-backdrop">
      <div
        className={`error-dialog ${variant === "success" ? "success" : "error"}`}
        role="alertdialog"
        aria-modal="true"
      >
        <button aria-label="关闭提示" className="dialog-close" onClick={onClose} type="button">
          ×
        </button>
        <h2>{error.title}</h2>
        <p>{error.message}</p>
        <p>{error.retryHint ?? error.nextStep}</p>
        {error.details ? <pre className="error-dialog-details">{error.details}</pre> : null}
        <button className="primary-pill" onClick={onConfirm ?? onClose} type="button">
          {confirmLabel}
        </button>
      </div>
    </div>
  );
}
