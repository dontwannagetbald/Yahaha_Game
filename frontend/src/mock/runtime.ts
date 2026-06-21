import type { AuthUser } from "../api/auth";
import type { CreateSessionEventRequest, CreateSessionState } from "../api/create-sessions";
import { patchLikedGame, toUiGame, type RawGame } from "../lib/games";
import type { Game, GameSortParam } from "../types/ui";

export type MockTask = {
  job_id: string;
  session_id: string | null;
  parent_job_id: string | null;
  title: string;
  status: "pending" | "running" | "succeeded" | "failed";
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  game_id: string | null;
  result_summary: string | null;
  error_message: string | null;
  validation_report: Record<string, unknown> | null;
};

export type MockAgentLog = {
  step: string;
  level: "info" | "warning" | "error";
  message: string;
  created_at: string;
};

export type MockAuthStore = {
  currentUser: AuthUser | null;
};

export const mockAuthStore: MockAuthStore = {
  currentUser: null,
};

const mockGameSeed = [
  {
    id: "neon-maze",
    title: "回到那年早读，抱抱当年的自己！再抱抱即将上考场的你们：加油啊！",
    description: "穿越霓虹迷宫，收集能量并避开巡逻机器人。",
    cover_url:
      "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=1200&q=80",
    author: { display_name: "发癫吧，后浪！" },
    tags: ["冒险"],
    published_at: "2026-05-31T10:00:00.000Z",
    play_count: 46500,
    like_count: 140000,
    liked_by_me: false,
    status: "published",
    manifest_url: "/mock/worlds/neon-maze/manifest.json",
    artifact_base_url: "/mock/worlds/neon-maze",
  },
  {
    id: "sky-runner",
    title: "Sky Runner",
    description: "在天空赛道上冲刺，躲避风暴并刷新最快纪录。",
    cover_url:
      "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1200&q=80",
    author: { display_name: "Cloud Studio" },
    tags: ["竞速"],
    published_at: "2026-05-31T12:00:00.000Z",
    play_count: 124000,
    like_count: 82000,
    liked_by_me: false,
    status: "published",
    manifest_url: "/mock/worlds/sky-runner/manifest.json",
    artifact_base_url: "/mock/worlds/sky-runner",
  },
  {
    id: "pixel-raid",
    title: "Pixel Raid",
    description: "像素地牢射击挑战，清理一波又一波的敌人。",
    cover_url:
      "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?auto=format&fit=crop&w=1200&q=80",
    author: { display_name: "Retro Lab" },
    tags: ["射击"],
    published_at: "2026-05-30T12:00:00.000Z",
    play_count: 78000,
    like_count: 49000,
    liked_by_me: false,
    status: "published",
    manifest_url: "/mock/worlds/pixel-raid/manifest.json",
    artifact_base_url: "/mock/worlds/pixel-raid",
  },
  {
    id: "orbital-lab",
    title: "Orbital Lab",
    description: "调整轨道、连接能源节点，修复失控空间站。",
    cover_url:
      "https://images.unsplash.com/photo-1560253023-3ec5d502959f?auto=format&fit=crop&w=1200&q=80",
    author: { display_name: "Space Forge" },
    tags: ["解谜"],
    published_at: "2026-05-30T15:00:00.000Z",
    play_count: 46000,
    like_count: 21000,
    liked_by_me: false,
    status: "published",
    manifest_url: "/mock/worlds/orbital-lab/manifest.json",
    artifact_base_url: "/mock/worlds/orbital-lab",
  },
  {
    id: "coop-quest",
    title: "Co-op Quest",
    description: "双人协作解锁机关，找到出口前不能落下队友。",
    cover_url:
      "https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?auto=format&fit=crop&w=1200&q=80",
    author: { display_name: "Team Mode" },
    tags: ["合作"],
    published_at: "2026-05-31T08:00:00.000Z",
    play_count: 183000,
    like_count: 96000,
    liked_by_me: false,
    status: "published",
    manifest_url: "/mock/worlds/coop-quest/manifest.json",
    artifact_base_url: "/mock/worlds/coop-quest",
  },
  {
    id: "arcade-drift",
    title: "Arcade Drift",
    description: "高速漂移、收集增压道具，在霓虹赛道中冲线。",
    cover_url:
      "https://images.unsplash.com/photo-1600861194942-f883de0dfe96?auto=format&fit=crop&w=1200&q=80",
    author: { display_name: "Speed Lab" },
    tags: ["竞速"],
    published_at: "2026-05-29T11:00:00.000Z",
    play_count: 92000,
    like_count: 57000,
    liked_by_me: false,
    status: "published",
    manifest_url: "/mock/worlds/arcade-drift/manifest.json",
    artifact_base_url: "/mock/worlds/arcade-drift",
  },
  {
    id: "mini-builder",
    title: "Mini Builder",
    description: "在小型沙盒里摆放零件，搭出会动的机关地图。",
    cover_url:
      "https://images.unsplash.com/photo-1542751110-97427bbecf20?auto=format&fit=crop&w=1200&q=80",
    author: { display_name: "Creator Bot" },
    tags: ["创造"],
    published_at: "2026-05-28T10:00:00.000Z",
    play_count: 61000,
    like_count: 38000,
    liked_by_me: false,
    status: "published",
    manifest_url: "/mock/worlds/mini-builder/manifest.json",
    artifact_base_url: "/mock/worlds/mini-builder",
  },
  {
    id: "boss-rush",
    title: "Boss Rush",
    description: "连续挑战 Boss，观察攻击节奏并抓住反击窗口。",
    cover_url:
      "https://images.unsplash.com/photo-1511882150382-421056c89033?auto=format&fit=crop&w=1200&q=80",
    author: { display_name: "Raid Room" },
    tags: ["动作"],
    published_at: "2026-05-26T09:00:00.000Z",
    play_count: 118000,
    like_count: 74000,
    liked_by_me: false,
    status: "published",
    manifest_url: "/mock/worlds/boss-rush/manifest.json",
    artifact_base_url: "/mock/worlds/boss-rush",
  },
] satisfies RawGame[];

let mockGameStore = mockGameSeed.map(toUiGame);

export const mockCreateSessions: Record<string, CreateSessionState> = {
  "mock-session-1": {
    session_id: "mock-session-1",
    conversation_status: "confirmed",
    user_requirements: {
      intent_summary: "做一个星际躲避游戏",
      must_have: ["躲避陨石", "收集星尘"],
    },
    game_plan: {
      plan_id: "mock-plan-1",
      title: "星际躲避",
      introduction: "驾驶飞船穿过陨石带，收集星尘并坚持到终点。",
      tags: ["街机", "动作"],
    },
    material_usage: { assets: [] },
    assistant_response: {
      message: "方案已确认，正在生成游戏。",
      suggestions: [],
      card: {
        plan_id: "mock-plan-1",
        title: "星际躲避",
        introduction: "驾驶飞船穿过陨石带，收集星尘并坚持到终点。",
        tags: ["街机", "动作"],
      },
      actions: ["generate"],
    },
    messages: [
      {
        id: "mock-message-1",
        role: "user",
        content: "我想做一个星际躲避游戏",
        payload: null,
        created_at: "2026-06-20T07:58:00.000Z",
      },
      {
        id: "mock-message-2",
        role: "assistant",
        content: "我整理成一版星际躲避方案，可以直接生成。",
        payload: {
          suggestions: [],
        },
        created_at: "2026-06-20T07:59:00.000Z",
      },
    ],
    created_at: "2026-06-20T07:58:00.000Z",
    updated_at: "2026-06-20T08:00:00.000Z",
  },
  "mock-session-2": {
    session_id: "mock-session-2",
    conversation_status: "confirmed",
    user_requirements: {
      intent_summary: "做一个森林冒险游戏",
      must_have: ["探索森林", "寻找出口"],
    },
    game_plan: {
      plan_id: "mock-plan-2",
      title: "森林冒险",
      introduction: "在森林里探索路径，避开陷阱并找到发光出口。",
      tags: ["冒险", "解谜"],
    },
    material_usage: { assets: [] },
    assistant_response: {
      message: "这版森林冒险已经生成，可以继续修改。",
      suggestions: [],
      card: {
        plan_id: "mock-plan-2",
        title: "森林冒险",
        introduction: "在森林里探索路径，避开陷阱并找到发光出口。",
        tags: ["冒险", "解谜"],
      },
      actions: ["revise"],
    },
    messages: [
      {
        id: "mock-message-3",
        role: "user",
        content: "做一个森林冒险",
        payload: null,
        created_at: "2026-06-19T17:58:00.000Z",
      },
      {
        id: "mock-message-4",
        role: "assistant",
        content: "森林冒险已经生成好了，你可以继续说想怎么改。",
        payload: {
          suggestions: [],
        },
        created_at: "2026-06-19T18:03:00.000Z",
      },
    ],
    created_at: "2026-06-19T17:58:00.000Z",
    updated_at: "2026-06-19T18:03:00.000Z",
  },
};

function createMockIframeDocument(title: string, description: string): string {
  const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${title}</title>
    <style>
      html, body {
        margin: 0;
        min-height: 100%;
        background: radial-gradient(circle at top, #263444 0%, #0f1112 60%, #090a0b 100%);
        color: #ffffff;
        font-family: Arial, sans-serif;
      }

      body {
        display: grid;
        place-items: center;
      }

      main {
        width: min(92vw, 760px);
        padding: 40px;
        border-radius: 24px;
        background: rgba(12, 14, 16, 0.82);
        box-shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
      }

      button {
        margin-top: 16px;
        border: 0;
        border-radius: 999px;
        padding: 12px 22px;
        background: #ffc200;
        color: #0f1112;
        font-weight: 700;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>${title}</h1>
      <p>${description}</p>
      <button id="action">Jump In</button>
    </main>
    <script>
      const button = document.getElementById("action");
      if (button) {
        button.addEventListener("click", () => {
          button.textContent = "Running";
        });
      }
    </script>
  </body>
</html>`;

  return `data:text/html;charset=utf-8,${encodeURIComponent(html)}`;
}

export const mockRuntime = {
  games: mockGameStore,
  tasks: [
    {
      job_id: "mock-job-1",
      session_id: "mock-session-1",
      parent_job_id: null,
      title: "星际躲避",
      status: "running",
      created_at: "2026-06-20T08:00:00.000Z",
      started_at: "2026-06-20T08:01:00.000Z",
      finished_at: null,
      game_id: null,
      result_summary: "正在生成游戏面板与素材。",
      error_message: null,
      validation_report: null,
    },
    {
      job_id: "mock-job-2",
      session_id: "mock-session-2",
      parent_job_id: null,
      title: "森林冒险",
      status: "succeeded",
      created_at: "2026-06-19T18:00:00.000Z",
      started_at: "2026-06-19T18:01:00.000Z",
      finished_at: "2026-06-19T18:03:00.000Z",
      game_id: "mock-draft-1",
      result_summary: "draft game ready。",
      error_message: null,
      validation_report: null,
    },
    {
      job_id: "mock-job-3",
      session_id: null,
      parent_job_id: null,
      title: "像素竞速",
      status: "pending",
      created_at: "2026-06-20T09:15:00.000Z",
      started_at: null,
      finished_at: null,
      game_id: null,
      result_summary: "等待执行。",
      error_message: null,
      validation_report: null,
    },
  ] satisfies MockTask[],
};

export function listMockJobs(): { jobs: MockTask[] } {
  return {
    jobs: [...mockRuntime.tasks].sort(
      (taskA, taskB) =>
        new Date(taskB.created_at).getTime() - new Date(taskA.created_at).getTime(),
    ),
  };
}

export function getMockJob(jobId: string): MockTask | null {
  return mockRuntime.tasks.find((task) => task.job_id === jobId) ?? null;
}

export function getMockJobLogs(jobId: string): { logs: MockAgentLog[] } {
  const task = getMockJob(jobId);
  if (!task) {
    return { logs: [] };
  }

  const createdAt = new Date(task.created_at).getTime();
  const logs: MockAgentLog[] = [
    {
      step: "orchestrator",
      level: "info",
      message: "Orchestrator 正在分析游戏方案和素材需求。",
      created_at: new Date(createdAt + 1000).toISOString(),
    },
  ];

  if (task.status !== "pending") {
    logs.push({
      step: "coding_agent",
      level: "info",
      message: "Coding Agent 正在生成 HTML5 游戏文件。",
      created_at: new Date(createdAt + 2000).toISOString(),
    });
  }

  if (task.status === "succeeded") {
    logs.push({
      step: "validator_agent",
      level: "info",
      message: "Validator Agent 已通过 manifest 和资源引用检查。",
      created_at: new Date(createdAt + 3000).toISOString(),
    });
  }

  if (task.status === "failed") {
    logs.push({
      step: "agent_runner",
      level: "error",
      message: task.error_message ?? "Agent 生成失败。",
      created_at: new Date(createdAt + 3000).toISOString(),
    });
  }

  return { logs };
}

export function createMockCreateSession(): CreateSessionState {
  const now = new Date().toISOString();
  const sessionId = `mock-session-${Object.keys(mockCreateSessions).length + 1}`;
  const session: CreateSessionState = {
    session_id: sessionId,
    conversation_status: "collecting",
    user_requirements: {},
    game_plan: null,
    material_usage: { assets: [] },
    assistant_response: {
      message: "您好，今天想创建个什么样的游戏？",
      suggestions: [],
      card: null,
      actions: [],
    },
    messages: [
      {
        id: `${sessionId}-welcome`,
        role: "assistant",
        content: "您好，今天想创建个什么样的游戏？",
        payload: {
          suggestions: [],
        },
        created_at: now,
      },
    ],
    created_at: now,
    updated_at: now,
  };

  mockCreateSessions[sessionId] = session;
  return session;
}

export function getMockCreateSession(sessionId: string): CreateSessionState | null {
  return mockCreateSessions[sessionId] ?? null;
}

export function sendMockCreateSessionEvent(
  sessionId: string,
  event: CreateSessionEventRequest,
): CreateSessionState {
  const session = mockCreateSessions[sessionId];
  if (!session) {
    throw new Error("未找到当前 Create 会话。");
  }

  if (event.type === "chat" && !event.message?.trim()) {
    return session;
  }

  if (event.type === "upload_assets") {
    const now = new Date().toISOString();
    const uploadedAssets = event.uploaded_assets ?? [];
    const nextAssets = event.replace_existing_assets
      ? uploadedAssets
      : [...session.material_usage.assets, ...uploadedAssets];
    const nextSession: CreateSessionState = {
      ...session,
      material_usage: {
        assets: nextAssets,
      },
      assistant_response: {
        ...session.assistant_response,
        message:
          uploadedAssets.length > 0
            ? `已绑定 ${uploadedAssets.length} 个素材，我会把它们纳入游戏方案。`
            : "已更新素材列表。",
      },
      messages: [
        ...session.messages,
        {
          id: `${sessionId}-upload-${session.messages.length + 1}`,
          role: "system",
          content:
            uploadedAssets.length > 0
              ? `已上传素材：${uploadedAssets.map((asset) => asset.filename).join("、")}`
              : "已清空素材列表。",
          payload: {
            event_type: "upload_assets",
            assets: uploadedAssets.map((asset) => ({
              asset_id: asset.asset_id,
              filename: asset.filename,
              mime_type: asset.mime_type,
              size_bytes: asset.size_bytes,
            })),
            replace_existing_assets: event.replace_existing_assets ?? false,
          },
          created_at: now,
        },
      ],
      updated_at: now,
    };

    mockCreateSessions[sessionId] = nextSession;
    return nextSession;
  }

  if (event.type === "regenerate") {
    const now = new Date().toISOString();
    const currentCard =
      session.assistant_response.card ??
      ({
        plan_id: (session.game_plan as { plan_id?: string } | null)?.plan_id ?? "mock-plan",
        title: (session.game_plan as { title?: string } | null)?.title ?? "新方案",
        introduction:
          (session.game_plan as { introduction?: string } | null)?.introduction ??
          "换一版新的创意方向。",
        tags: ((session.game_plan as { tags?: string[] } | null)?.tags ?? []).slice(0, 3),
      } satisfies NonNullable<CreateSessionState["assistant_response"]["card"]>);
    const regenerateCount =
      session.messages.filter(
        (message) => message.payload?.event_type === "regenerate",
      ).length + 1;
    const variantLabel = `新编 ${regenerateCount}`;
    const nextCard = {
      ...currentCard,
      plan_id: `${currentCard.plan_id}-regen-${session.messages.length + 1}`,
      title: `${currentCard.title.replace(/\s+新编\s+\d+$/u, "")} ${variantLabel}`,
      introduction: `这次我保留核心玩法，但切成了第 ${regenerateCount} 版更轻快的节奏表达。`,
    };
    const assistantMessage = "我帮你换了一版方案，你看看这次是否更合适。";
    const nextSession: CreateSessionState = {
      ...session,
      conversation_status: "ready_to_confirm",
      game_plan: {
        ...(session.game_plan ?? {}),
        plan_id: nextCard.plan_id,
        title: nextCard.title,
        introduction: nextCard.introduction,
        tags: nextCard.tags,
      },
      assistant_response: {
        message: assistantMessage,
        suggestions: [],
        card: nextCard,
        actions: ["regenerate", "confirm"],
      },
      messages: [
        ...session.messages,
        {
          id: `${sessionId}-regenerate-${session.messages.length + 1}`,
          role: "assistant",
          content: assistantMessage,
          payload: {
            event_type: "regenerate",
            card: nextCard,
            suggestions: [],
          },
          created_at: now,
        },
      ],
      updated_at: now,
    };

    mockCreateSessions[sessionId] = nextSession;
    return nextSession;
  }

  if (event.type === "confirm") {
    const now = new Date().toISOString();
    const currentCard =
      session.assistant_response.card ??
      ({
        plan_id: (session.game_plan as { plan_id?: string } | null)?.plan_id ?? "mock-plan",
        title: (session.game_plan as { title?: string } | null)?.title ?? "新方案",
        introduction:
          (session.game_plan as { introduction?: string } | null)?.introduction ??
          "根据当前方向生成一版游戏方案。",
        tags: ((session.game_plan as { tags?: string[] } | null)?.tags ?? []).slice(0, 3),
      } satisfies NonNullable<CreateSessionState["assistant_response"]["card"]>);
    const assistantMessage = "方案已确认，正在为你创建生成任务。";
    const nextSession: CreateSessionState = {
      ...session,
      conversation_status: "confirmed",
      game_plan: {
        ...(session.game_plan ?? {}),
        plan_id: currentCard.plan_id,
        title: currentCard.title,
        introduction: currentCard.introduction,
        tags: currentCard.tags,
      },
      assistant_response: {
        message: assistantMessage,
        suggestions: [],
        card: currentCard,
        actions: ["generate"],
      },
      messages: [
        ...session.messages,
        {
          id: `${sessionId}-confirm-${session.messages.length + 1}`,
          role: "assistant",
          content: assistantMessage,
          payload: {
            event_type: "confirm",
            card: currentCard,
            suggestions: [],
          },
          created_at: now,
        },
      ],
      handoff_to_generation: true,
      updated_at: now,
    };

    mockCreateSessions[sessionId] = nextSession;
    return nextSession;
  }

  if (event.type !== "chat") {
    return session;
  }

  const now = new Date().toISOString();
  const normalizedMessage = event.message?.trim() ?? "";
  const assistantMessage = `收到：${normalizedMessage}。我会继续帮你收敛游戏方案。`;
  const nextSession: CreateSessionState = {
    ...session,
    assistant_response: {
      message: assistantMessage,
      suggestions: [],
      card: session.assistant_response.card,
      actions: session.assistant_response.actions,
    },
    messages: [
      ...session.messages,
      {
        id: `${sessionId}-user-${session.messages.length + 1}`,
        role: "user",
        content: normalizedMessage,
        payload: null,
        created_at: now,
      },
      {
        id: `${sessionId}-assistant-${session.messages.length + 2}`,
        role: "assistant",
        content: assistantMessage,
        payload: {
          suggestions: [],
        },
        created_at: now,
      },
    ],
    updated_at: now,
  };

  mockCreateSessions[sessionId] = nextSession;
  return nextSession;
}

export function isMockEnabled(): boolean {
  return (import.meta.env.VITE_ENABLE_MOCK_API ?? "false") === "true";
}

export function listMockGames(query: {
  sort: GameSortParam;
  q?: string;
  tag?: string;
}): { games: Game[]; total: number } {
  const normalizedQuery = query.q?.trim().toLowerCase() ?? "";
  const normalizedTag = query.tag?.trim().toLowerCase() ?? "";

  const filteredGames = mockGameStore.filter((game) => {
    const matchesQuery =
      !normalizedQuery ||
      game.title.toLowerCase().includes(normalizedQuery) ||
      game.author.toLowerCase().includes(normalizedQuery) ||
      game.description.toLowerCase().includes(normalizedQuery) ||
      game.tags.some((tag) => tag.toLowerCase().includes(normalizedQuery));

    const matchesTag =
      !normalizedTag || game.tags.some((tag) => tag.toLowerCase() === normalizedTag);

    return matchesQuery && matchesTag && game.status === "published";
  });

  filteredGames.sort((gameA, gameB) => {
    if (query.sort === "play_count") {
      return gameB.playCount - gameA.playCount;
    }

    if (query.sort === "like_count") {
      return gameB.likeCount - gameA.likeCount;
    }

    return (
      new Date(gameB.publishedAtIso ?? 0).getTime() - new Date(gameA.publishedAtIso ?? 0).getTime()
    );
  });

  return {
    games: filteredGames,
    total: filteredGames.length,
  };
}

export function getMockGameDetail(gameId: string): Game | null {
  return mockGameStore.find((game) => game.id === gameId) ?? null;
}

export function getMockManifestByUrl(manifestUrl: string): {
  schemaVersion: string;
  title: string;
  description: string;
  entry: string;
  runtime: string;
  generatedAt: string;
} | null {
  const matchedGame = mockGameStore.find((game) => game.manifestUrl === manifestUrl);
  if (!matchedGame) {
    return null;
  }

  return {
    schemaVersion: "1.0",
    title: matchedGame.title,
    description: matchedGame.description,
    entry: createMockIframeDocument(matchedGame.title, matchedGame.description),
    runtime: "html5-iframe",
    generatedAt: "2026-06-20T00:00:00Z",
  };
}

export function likeMockGame(gameId: string): Game | null {
  let likedGame: Game | null = null;

  mockGameStore = mockGameStore.map((game) => {
    if (game.id !== gameId) {
      return game;
    }

    if (game.likedByMe) {
      likedGame = patchLikedGame(game, Math.max(0, game.likeCount - 1), false);
      return likedGame;
    }

    likedGame = patchLikedGame(game, game.likeCount + 1, true);
    return likedGame;
  });

  mockRuntime.games = mockGameStore;
  return likedGame;
}
