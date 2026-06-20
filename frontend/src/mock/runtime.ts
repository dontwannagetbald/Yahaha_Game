import type { AuthUser } from "../api/auth";
import { patchLikedGame, toUiGame, type RawGame } from "../lib/games";
import type { Game, GameSortParam } from "../types/ui";

export type MockTask = {
  name: string;
  status: string;
  summary: string;
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
    { name: "星际躲避", status: "running", summary: "正在生成游戏面板与素材。" },
    { name: "森林冒险", status: "succeeded", summary: "draft game ready。" },
    { name: "像素竞速", status: "pending", summary: "等待执行。" },
  ] satisfies MockTask[],
};

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
