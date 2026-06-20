import { useEffect, useMemo, useState } from "react";
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
import { getGameDetail, likePublishedGame, listPublishedGames } from "./api/games";
import { AuthModal } from "./components/AuthModal";
import { patchLikedGame } from "./lib/games";
import { logConsoleEvent } from "./lib/console";
import { createUserError, type UserFacingError } from "./lib/errors";
import {
  getMockGameDetail,
  isMockEnabled,
  likeMockGame,
  listMockGames,
  mockAuthStore,
  mockRuntime,
} from "./mock/runtime";
import { CreatePage } from "./pages/CreatePage";
import { HomePage } from "./pages/HomePage";
import { PlayPage } from "./pages/PlayPage";
import type { AuthMode, Game, GameSortParam } from "./types/ui";
import { TopNav } from "./components/TopNav";

const registerErrorTitle = "注册失败";
const loginErrorTitle = "登录失败";
const registerSuccessTitle = "注册成功";
const loginSuccessTitle = "登录成功";
const logoutErrorTitle = "退出登录失败";
const googleErrorTitle = "Google 登录失败";
const createLoginPromptTitle = "创建游戏需要先登录";

export function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const mockEnabled = isMockEnabled();
  const tasks = useMemo(() => mockRuntime.tasks, []);
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
        <Route path="/create" element={<CreatePage tasks={tasks} />} />
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
        <button className="primary-pill" onClick={onConfirm ?? onClose} type="button">
          {confirmLabel}
        </button>
      </div>
    </div>
  );
}
