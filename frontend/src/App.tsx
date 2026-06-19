import { useState } from "react";

type Page = "home" | "create" | "play";
type AuthMode = "login" | "register";
type SortMode = "plays" | "likes" | "latest";

type Game = {
  id: string;
  title: string;
  author: string;
  publishedAt: string;
  tag: string;
  likes: string;
  plays: string;
  description: string;
  cover: string;
};

const games: Game[] = [
  {
    id: "neon-maze",
    title: "回到那年早读，抱抱当年的自己！再抱抱即将上考场的你们：加油啊！",
    author: "发癫吧，后浪！",
    publishedAt: "5月31日",
    tag: "冒险",
    likes: "♡ 14.0万",
    plays: "46:31",
    description: "穿越霓虹迷宫，收集能量并避开巡逻机器人。",
    cover:
      "https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: "sky-runner",
    title: "Sky Runner",
    author: "Cloud Studio",
    publishedAt: "5月31日",
    tag: "竞速",
    likes: "♡ 8.2万",
    plays: "12.4万次",
    description: "在天空赛道上冲刺，躲避风暴并刷新最快纪录。",
    cover:
      "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: "pixel-raid",
    title: "Pixel Raid",
    author: "Retro Lab",
    publishedAt: "5月30日",
    tag: "射击",
    likes: "♡ 4.9万",
    plays: "7.8万次",
    description: "像素地牢射击挑战，清理一波又一波的敌人。",
    cover:
      "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: "orbital-lab",
    title: "Orbital Lab",
    author: "Space Forge",
    publishedAt: "5月30日",
    tag: "解谜",
    likes: "♡ 2.1万",
    plays: "4.6万次",
    description: "调整轨道、连接能源节点，修复失控空间站。",
    cover:
      "https://images.unsplash.com/photo-1560253023-3ec5d502959f?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: "coop-quest",
    title: "Co-op Quest",
    author: "Team Mode",
    publishedAt: "5月31日",
    tag: "合作",
    likes: "♡ 9.6万",
    plays: "18.3万次",
    description: "双人协作解锁机关，找到出口前不能落下队友。",
    cover:
      "https://images.unsplash.com/photo-1493711662062-fa541adb3fc8?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: "arcade-drift",
    title: "Arcade Drift",
    author: "Speed Lab",
    publishedAt: "5月29日",
    tag: "竞速",
    likes: "♡ 5.7万",
    plays: "9.2万次",
    description: "高速漂移、收集增压道具，在霓虹赛道中冲线。",
    cover:
      "https://images.unsplash.com/photo-1600861194942-f883de0dfe96?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: "mini-builder",
    title: "Mini Builder",
    author: "Creator Bot",
    publishedAt: "5月28日",
    tag: "创造",
    likes: "♡ 3.8万",
    plays: "6.1万次",
    description: "在小型沙盒里摆放零件，搭出会动的机关地图。",
    cover:
      "https://images.unsplash.com/photo-1542751110-97427bbecf20?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: "boss-rush",
    title: "Boss Rush",
    author: "Raid Room",
    publishedAt: "5月26日",
    tag: "动作",
    likes: "♡ 7.4万",
    plays: "11.8万次",
    description: "连续挑战 Boss，观察攻击节奏并抓住反击窗口。",
    cover:
      "https://images.unsplash.com/photo-1511882150382-421056c89033?auto=format&fit=crop&w=1200&q=80",
  },
];

const tasks = [
  { name: "星际躲避", status: "running", summary: "正在生成游戏面板与素材。" },
  { name: "森林冒险", status: "succeeded", summary: "draft game ready。" },
  { name: "像素竞速", status: "pending", summary: "等待执行。" },
];

export function App() {
  const [page, setPage] = useState<Page>("home");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [selectedGame, setSelectedGame] = useState(games[0]);

  function openCreate() {
    if (!isLoggedIn) {
      setAuthMode("login");
      setAuthOpen(true);
      return;
    }
    setPage("create");
    window.scrollTo({ top: 0 });
  }

  function simulateLogin() {
    setIsLoggedIn(true);
    setAuthOpen(false);
    setPage("home");
    window.scrollTo({ top: 0 });
  }

  function logout() {
    setIsLoggedIn(false);
    setPage("home");
    window.scrollTo({ top: 0 });
  }

  function openPlay(game: Game) {
    setSelectedGame(game);
    setPage("play");
    window.scrollTo({ top: 0 });
  }

  return (
    <div className="app-shell">
      <TopNav
        isLoggedIn={isLoggedIn}
        currentPage={page}
        onHome={() => setPage("home")}
        onCreate={openCreate}
        onLogin={() => {
          setAuthMode("login");
          setAuthOpen(true);
        }}
        onLogout={logout}
      />

      {page === "home" ? <HomePage games={games} onOpenPlay={openPlay} /> : null}
      {page === "create" ? <CreatePage /> : null}
      {page === "play" ? (
        <PlayPage game={selectedGame} onHome={() => setPage("home")} />
      ) : null}

      {authOpen ? (
        <AuthModal
          mode={authMode}
          onModeChange={setAuthMode}
          onClose={() => setAuthOpen(false)}
          onLogin={simulateLogin}
        />
      ) : null}
    </div>
  );
}

function TopNav({
  isLoggedIn,
  currentPage,
  onHome,
  onCreate,
  onLogin,
  onLogout,
}: {
  isLoggedIn: boolean;
  currentPage: Page;
  onHome: () => void;
  onCreate: () => void;
  onLogin: () => void;
  onLogout: () => void;
}) {
  return (
    <nav className="top-nav">
      <button className="brand-button" onClick={onHome}>
        Yahaha_Play
      </button>
      <div className="nav-actions">
        <div className="nav-tabs">
          <button
            className={currentPage === "home" || currentPage === "play" ? "active" : ""}
            onClick={onHome}
          >
            主页
          </button>
          <button className={currentPage === "create" ? "active" : ""} onClick={onCreate}>
            创建游戏
          </button>
        </div>
        {isLoggedIn ? (
          <div className="user-area logged-in">
            <button className="avatar-button" aria-label="Bella Q 用户菜单">
              <span className="avatar" aria-hidden="true" />
            </button>
            <div className="user-menu">
              <span>Bella Q</span>
              <button onClick={onLogout}>
                退出登录
              </button>
            </div>
          </div>
        ) : (
          <button className="primary-pill" onClick={onLogin}>
            登录
          </button>
        )}
      </div>
    </nav>
  );
}

function HomePage({
  games,
  onOpenPlay,
}: {
  games: Game[];
  onOpenPlay: (game: Game) => void;
}) {
  const [sortMode, setSortMode] = useState<SortMode>("plays");

  return (
    <main>
      <header className="home-hero">
        <h1>Play worlds made by creators.</h1>
        <p>浏览发布作品、筛选类型、直接进入 Play。未登录用户也可以试玩，创建和发布时再登录。</p>
      </header>

      <section className="filters" aria-label="游戏筛选">
        <button
          className={`filter-tab ${sortMode === "plays" ? "active" : ""}`}
          onClick={() => setSortMode("plays")}
        >
          最多游玩
        </button>
        <button
          className={`filter-tab ${sortMode === "likes" ? "active" : ""}`}
          onClick={() => setSortMode("likes")}
        >
          最多点赞
        </button>
        <button
          className={`filter-tab ${sortMode === "latest" ? "active" : ""}`}
          onClick={() => setSortMode("latest")}
        >
          最新发布
        </button>
        <label className="search">
          <span>⌕</span>
          <input aria-label="搜索游戏" placeholder="搜索框" />
        </label>
        <button className="filter-dropdown">更多筛选</button>
      </section>

      <section className="catalog-grid" aria-label="游戏列表">
        {games.map((game) => (
          <article className="game-card" key={game.id}>
            <button className="game-card-button" onClick={() => onOpenPlay(game)}>
              <div
                className="cover"
                style={{ backgroundImage: `url("${game.cover}")` }}
              >
                <div className="cover-tags">
                  <span className="tag">{game.tag}</span>
                </div>
                <div className="cover-stats">
                  <span>{game.likes}</span>
                  <span>{game.plays}</span>
                </div>
              </div>
              <div className="hover-note">{game.description}</div>
              <div className="card-info">
                <h2>{game.title}</h2>
                <p>
                  @ {game.author} · {game.publishedAt}
                </p>
              </div>
            </button>
          </article>
        ))}
      </section>
    </main>
  );
}

function AuthModal({
  mode,
  onModeChange,
  onClose,
  onLogin,
}: {
  mode: AuthMode;
  onModeChange: (mode: AuthMode) => void;
  onClose: () => void;
  onLogin: () => void;
}) {
  const isLogin = mode === "login";
  return (
    <div className="auth-modal" data-testid="auth-modal" role="dialog" aria-modal="true">
      <div className="auth-panel">
        <button className="auth-close" onClick={onClose}>
          取消
        </button>
        <h2>{isLogin ? "登录" : "注册"}</h2>
        <label className="field">
          邮箱
          <input type="email" />
        </label>
        <label className="field">
          密码
          <input type="password" />
        </label>
        {!isLogin ? (
          <label className="field">
            确认密码
            <input type="password" />
          </label>
        ) : null}
        <button className="primary-pill full-width" onClick={onLogin}>
          {isLogin ? "登录" : "注册"}
        </button>
        <div className="oauth-row">
          <button className="secondary-pill">google</button>
          <button className="secondary-pill" disabled>
            github
          </button>
        </div>
        <p className="auth-foot">
          {isLogin ? "尚无账号？" : "已有账号？"}
          <button onClick={() => onModeChange(isLogin ? "register" : "login")}>
            {isLogin ? "注册" : "返回登录"}
          </button>
        </p>
      </div>
    </div>
  );
}

function CreatePage() {
  return (
    <main className="create-layout" data-testid="create-workspace">
      <aside className="task-sidebar">
        <div className="sidebar-title">任务列表</div>
        <div className="task-list">
          {tasks.map((task) => (
            <article className="task-item" key={task.name}>
              <div className="task-head">
                <strong>{task.name}</strong>
                <span className={`badge ${task.status}`}>{task.status}</span>
              </div>
              <p>{task.summary}</p>
            </article>
          ))}
          <button className="secondary-pill full-width">+ 新建任务</button>
        </div>
        <div className="composer">
          <textarea placeholder="placeholder：创建 agent 给的随机游戏描述建议" />
          <div className="composer-actions">
            <button className="icon-button" aria-label="附件">
              ↥
            </button>
            <button className="primary-pill">发送</button>
          </div>
        </div>
      </aside>

      <section className="workspace">
        <div className="chat-panel">
          <h1>对话记录</h1>
          <div className="message agent">您好，今天想创建个什么样的游戏？</div>
          <div className="message user">试试和 AI 聊聊今天想要创建什么游戏吧～</div>
          <div className="confirm-card">
            <h2>最终确认卡片</h2>
            <ul>
              <li>游戏类型：策略类</li>
              <li>核心玩法：射击类关卡挑战</li>
              <li>成长目标：经营类资源升级</li>
            </ul>
          </div>
        </div>

        <div className="generate-panel">
          <h1>生成游戏显示面板</h1>
          <div className="preview-frame">
            <span>Playable Preview</span>
          </div>
          <div className="progress-row">
            <span>生成过程中</span>
            <div className="progress-track">
              <div className="progress-fill" />
            </div>
            <span>74%</span>
          </div>
          <div className="agent-log">
            <div>
              <span>分析创意</span>
              <span className="badge succeeded">done</span>
            </div>
            <div>
              <span>生成游戏文件</span>
              <span className="badge running">running</span>
            </div>
            <div>
              <span>上传产物</span>
              <span className="badge">pending</span>
            </div>
          </div>
          <div className="action-row">
            <button className="primary-pill">Publish</button>
            <button className="secondary-pill">Retry</button>
          </div>
        </div>
      </section>
    </main>
  );
}

function PlayPage({ game, onHome }: { game: Game; onHome: () => void }) {
  return (
    <main className="play-layout">
      <aside className="play-sidebar">
        <button className="back-link" onClick={onHome}>
          ‹ 返回主页
        </button>
        <h1>{game.title}</h1>
        <p>
          {game.author} · {game.publishedAt}
        </p>
        <div className="stat-row">
          <span>{game.plays}</span>
          <span>{game.likes}</span>
        </div>
        <div className="tag-row">
          <span className="tag">{game.tag}</span>
        </div>
        <p>{game.description}</p>
      </aside>

      <section className="play-stage-wrap">
        <div className="play-stage" data-testid="play-stage">
          <div className="game-hud">
            <span>manifest loaded</span>
            <span>score 1280</span>
          </div>
          <div className="orbit" />
          <div className="player-dot" />
          <div className="game-title">游戏</div>
        </div>
      </section>
    </main>
  );
}
