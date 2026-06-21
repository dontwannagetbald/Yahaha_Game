import { useEffect, useMemo, useState } from "react";

import { formatCompactCount } from "../lib/games";
import type { Game, GameSortParam, SortMode } from "../types/ui";
import "./home.css";

const filterOptions = ["全部类型", "冒险", "动作", "策略", "解谜", "街机", "生存", "模拟", "竞速", "节奏", "角色扮演", "休闲", "教育"];

type HomePageProps = {
  games: Game[];
  featuredGame: Game | null;
  isLoggedIn: boolean;
  isLoading: boolean;
  onOpenPlay: (game: Game) => void;
  onLoadGames: (params: { sort: GameSortParam; q: string; tag: string }) => Promise<void>;
  onLikeGame: (gameId: string) => Promise<void>;
  onRequireLogin: () => void;
};

export function HomePage({
  games,
  featuredGame,
  isLoggedIn,
  isLoading,
  onOpenPlay,
  onLoadGames,
  onLikeGame,
  onRequireLogin,
}: HomePageProps) {
  const [sortMode, setSortMode] = useState<SortMode>("plays");
  const [filterMenuOpen, setFilterMenuOpen] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState("全部类型");
  const [searchDraft, setSearchDraft] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const normalizedQuery = searchQuery.trim().toLowerCase();

  function applySearchQuery() {
    setSearchQuery(searchDraft);
  }

  useEffect(() => {
    void onLoadGames({
      sort: sortMode === "plays" ? "play_count" : sortMode === "likes" ? "like_count" : "latest",
      q: normalizedQuery,
      tag: selectedFilter === "全部类型" ? "" : selectedFilter,
    });
  }, [isLoggedIn, normalizedQuery, selectedFilter, sortMode]);

  const activeFeaturedGame = useMemo(() => featuredGame ?? games[0] ?? null, [featuredGame, games]);

  return (
    <main className="home-page">
      <header className="home-hero">
        <div className="hero-copy">
          <span className="hero-kicker">Yahaha Featured Worlds</span>
          <h1>Play worlds made by creators.</h1>
          <p>
            浏览发布作品、筛选类型、直接进入 Play。未登录用户也可以试玩，创建和发布时再登录。
          </p>
        </div>
        {activeFeaturedGame ? (
          <aside className="hero-spotlight" aria-label="精选游戏">
            <div
              className="hero-spotlight-cover"
              style={{ backgroundImage: `url("${activeFeaturedGame.cover}")` }}
            >
              <span className="tag">{activeFeaturedGame.tag}</span>
            </div>
            <div className="hero-spotlight-body">
              <p className="hero-spotlight-label">精选推荐</p>
              <h2>{activeFeaturedGame.title}</h2>
              <p className="hero-spotlight-meta">
                @{activeFeaturedGame.author} · {activeFeaturedGame.publishedAt}
              </p>
              <p className="hero-spotlight-description">{activeFeaturedGame.description}</p>
              <div className="hero-spotlight-stats">
                <button
                  aria-label={activeFeaturedGame.likedByMe ? "已点赞" : "点赞游戏"}
                  className={`hero-like-button ${activeFeaturedGame.likedByMe ? "active" : ""}`}
                  onClick={() => {
                    if (!isLoggedIn) {
                      onRequireLogin();
                      return;
                    }
                    void onLikeGame(activeFeaturedGame.id);
                  }}
                  type="button"
                >
                  <span aria-hidden="true">♥</span>
                  <span>{formatCompactCount(activeFeaturedGame.likeCount)}</span>
                </button>
                <span>{activeFeaturedGame.plays}</span>
              </div>
              <button className="primary-pill compact-pill" onClick={() => onOpenPlay(activeFeaturedGame)}>
                立即试玩
              </button>
            </div>
          </aside>
        ) : null}
      </header>

      <section className="browse-panel">
        <div className="browse-panel-head">
          <div>
            <span className="panel-kicker">Discover</span>
            <h2>浏览热门游戏</h2>
          </div>
        </div>

        <section className="filters" aria-label="游戏筛选">
          <div className="filter-tabs">
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
          </div>
          <div className="filter-tools">
            <label className="search">
              <button
                aria-label="执行搜索"
                className="search-trigger"
                onClick={applySearchQuery}
                type="button"
              >
                <span aria-hidden="true" className="search-icon">
                  ⌕
                </span>
              </button>
              <input
                aria-label="搜索游戏"
                onBlur={applySearchQuery}
                onChange={(event) => setSearchDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    applySearchQuery();
                  }
                }}
                placeholder="搜索游戏名称或作者"
                value={searchDraft}
              />
            </label>
            <div className="filter-select">
              <button
                aria-expanded={filterMenuOpen}
                aria-haspopup="listbox"
                className={`filter-dropdown ${filterMenuOpen ? "open" : ""}`}
                onClick={() => setFilterMenuOpen((open) => !open)}
                type="button"
              >
                {selectedFilter === "全部类型" ? "更多筛选" : selectedFilter}
              </button>
              {filterMenuOpen ? (
                <div className="filter-menu" data-testid="filter-menu" role="listbox">
                  {filterOptions.map((option) => (
                    <button
                      aria-selected={selectedFilter === option}
                      className={selectedFilter === option ? "selected" : ""}
                      key={option}
                      onClick={() => {
                        setSelectedFilter(option);
                        setFilterMenuOpen(false);
                      }}
                      role="option"
                      type="button"
                    >
                      {option}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        </section>

        <section className="catalog-grid" aria-label="游戏列表">
          {isLoading ? (
            <article className="catalog-empty">
              <p>正在加载游戏列表...</p>
            </article>
          ) : games.length > 0 ? (
            games.map((game) => (
              <article className="game-card" key={game.id}>
                <div className="game-card-shell">
                  <div
                    className="game-card-button"
                    onClick={() => onOpenPlay(game)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        onOpenPlay(game);
                      }
                    }}
                    role="button"
                    tabIndex={0}
                  >
                    <div className="cover" style={{ backgroundImage: `url("${game.cover}")` }}>
                      <div className="cover-overlay">
                        <div className="cover-tags">
                          <span className="tag">{game.tag}</span>
                        </div>
                        <div className="cover-stats">
                          <button
                            aria-label={game.likedByMe ? "已点赞" : "点赞游戏"}
                            className={`card-like-button ${game.likedByMe ? "active" : ""}`}
                            onClick={(event) => {
                              event.stopPropagation();
                              if (!isLoggedIn) {
                                onRequireLogin();
                                return;
                              }
                              void onLikeGame(game.id);
                            }}
                            onKeyDown={(event) => {
                              event.stopPropagation();
                            }}
                            type="button"
                          >
                            <span aria-hidden="true">♥</span>
                            <span>{formatCompactCount(game.likeCount)}</span>
                          </button>
                          <span className="card-play-count">{game.plays}</span>
                        </div>
                      </div>
                    </div>
                    <div className="hover-note">{game.description}</div>
                    <div className="card-info">
                      <h3>{game.title}</h3>
                      <p>
                        @ {game.author} · {game.publishedAt}
                      </p>
                    </div>
                  </div>
                </div>
              </article>
            ))
          ) : (
            <article className="catalog-empty">
              <p>没有找到符合当前筛选条件的游戏，试试换个关键词或筛选条件。</p>
            </article>
          )}
        </section>
      </section>
    </main>
  );
}
