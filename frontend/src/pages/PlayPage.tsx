import { useEffect, useRef, useState } from "react";

import { createPlayEvent, loadPlayManifest, resolveIframeSrc, type PlayManifest } from "../api/play";
import { formatCompactCount } from "../lib/games";
import { logConsoleEvent } from "../lib/console";
import type { Game } from "../types/ui";
import "./play.css";

type PlayState = "loading_meta" | "loading_manifest" | "loading_iframe" | "ready" | "error" | "timeout";

type PlayPageProps = {
  game: Game;
  games: Game[];
  onHome: () => void;
  onOpenGame: (game: Game) => void;
  onLikeGame: (gameId: string) => Promise<void>;
  onRequireLogin: () => void;
};

const PLAY_TIMEOUT_MS = 12000;

function getLoadingCopy(playState: PlayState): string {
  if (playState === "loading_meta") {
    return "正在读取游戏信息...";
  }

  if (playState === "loading_manifest") {
    return "正在加载中...";
  }

  if (playState === "loading_iframe") {
    return "正在启动游戏沙盒...";
  }

  if (playState === "timeout") {
    return "加载超时，请重新加载。";
  }

  return "资源加载失败，请重新加载。";
}

export function PlayPage({
  game,
  games,
  onHome,
  onOpenGame,
  onLikeGame,
  onRequireLogin,
}: PlayPageProps) {
  const [playState, setPlayState] = useState<PlayState>("loading_meta");
  const [manifestError, setManifestError] = useState<string | null>(null);
  const [iframeSrc, setIframeSrc] = useState("");
  const [runtimeManifest, setRuntimeManifest] = useState<PlayManifest | null>(null);
  const [loadProgress, setLoadProgress] = useState(0);
  const [retryKey, setRetryKey] = useState(0);
  const relatedGames = games.filter(
    (candidate) => candidate.tag === game.tag && candidate.id !== game.id,
  );
  const displayLikes = formatCompactCount(game.likeCount);
  const controlHints = runtimeManifest?.controls ?? [];
  const startedEventRef = useRef(false);
  const exitPostedRef = useRef(false);
  const loadStartedAtRef = useRef(0);

  useEffect(() => {
    let active = true;
    const abortController = new AbortController();
    let metaTimer = 0;
    let manifestTimer = 0;
    let timeoutTimer = 0;

    startedEventRef.current = false;
    exitPostedRef.current = false;
    loadStartedAtRef.current = performance.now();
    setPlayState("loading_meta");
    setManifestError(null);
    setIframeSrc("");
    setRuntimeManifest(null);
    setLoadProgress(8);

    timeoutTimer = window.setTimeout(() => {
      if (!active || startedEventRef.current) {
        return;
      }

      setPlayState("timeout");
      setManifestError("当前游戏加载超时，请重新加载后再试。");
      setLoadProgress(100);
      void createPlayEvent(game.id, "timeout", {
        stage: playState,
        elapsed_ms: Math.round(performance.now() - loadStartedAtRef.current),
      }).catch(() => {
        logConsoleEvent("play", {
          requestPath: "/api/play-events",
          status: 500,
          businessStatus: "error",
          event_type: "timeout",
          game_id: game.id,
        });
      });
    }, PLAY_TIMEOUT_MS);

    void createPlayEvent(game.id, "view", {
      manifest_url: game.manifestUrl,
    }).catch(() => {
      logConsoleEvent("play", {
        requestPath: "/api/play-events",
        status: 500,
        businessStatus: "error",
        event_type: "view",
        game_id: game.id,
      });
    });

    void (async () => {
      metaTimer = window.setTimeout(() => {
        if (!active) {
          return;
        }
        setPlayState("loading_manifest");
        setLoadProgress(28);
      }, 140);

      try {
        if (!game.manifestUrl) {
          throw new Error("当前游戏缺少 manifest 地址。");
        }

        const manifest = await loadPlayManifest(game.manifestUrl, abortController.signal);
        if (!active) {
          return;
        }

        manifestTimer = window.setTimeout(() => {
          if (!active) {
            return;
          }
          setRuntimeManifest(manifest);
          setLoadProgress(64);
          setPlayState("loading_iframe");
        }, 120);

        const nextIframeSrc = resolveIframeSrc(
          manifest,
          game.artifactBaseUrl,
          game.manifestUrl,
        );

        setRuntimeManifest(manifest);
        setIframeSrc(nextIframeSrc);
        setLoadProgress(82);
        setPlayState("loading_iframe");

        await createPlayEvent(game.id, "manifest_loaded", {
          manifest_url: game.manifestUrl,
          entry: manifest.entry,
          runtime: manifest.runtime ?? "unknown",
          schema_version: manifest.schemaVersion ?? "unknown",
        });

        logConsoleEvent("play", {
          requestPath: game.manifestUrl,
          status: 200,
          businessStatus: "manifest_loaded",
          game_id: game.id,
          manifest_entry: manifest.entry,
          manifest_runtime: manifest.runtime ?? "unknown",
        });
      } catch (error) {
        if (!active) {
          return;
        }

        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        const message = error instanceof Error ? error.message : "游戏资源加载失败。";
        setManifestError(message);
        setPlayState("error");
        setLoadProgress(0);

        await createPlayEvent(game.id, "failed", {
          stage: "manifest",
          error_message: message,
          manifest_url: game.manifestUrl,
        }).catch(() => {
          logConsoleEvent("play", {
            requestPath: "/api/play-events",
            status: 500,
            businessStatus: "error",
            event_type: "failed",
            game_id: game.id,
          });
        });

        logConsoleEvent("play", {
          requestPath: game.manifestUrl ?? `/api/games/${game.id}`,
          status: 500,
          businessStatus: "error",
          game_id: game.id,
          error_code: "manifest_failed",
        });
      }
    })();

    return () => {
      active = false;
      abortController.abort();
      window.clearTimeout(metaTimer);
      window.clearTimeout(manifestTimer);
      window.clearTimeout(timeoutTimer);

      if (!exitPostedRef.current) {
        exitPostedRef.current = true;
        void createPlayEvent(game.id, "exited", {
          elapsed_ms: Math.round(performance.now() - loadStartedAtRef.current),
          started: startedEventRef.current,
        }).catch(() => {
          logConsoleEvent("play", {
            requestPath: "/api/play-events",
            status: 500,
            businessStatus: "error",
            event_type: "exited",
            game_id: game.id,
          });
        });
      }
    };
  }, [game.artifactBaseUrl, game.id, game.manifestUrl, retryKey]);

  const showOverlay = playState !== "ready";

  return (
    <main className="play-page play-layout">
      <aside className="play-sidebar">
        <div className="play-sidebar-main">
          <button className="back-link" onClick={onHome}>
            <span className="back-link-icon">‹</span>
            <span>返回主页</span>
          </button>
          <h1>{game.title}</h1>
          <p className="play-meta">
            {game.author} · {game.publishedAt}
          </p>
          <div className="stat-row">
            <button
              aria-label={game.likedByMe ? "已点赞" : "点赞游戏"}
              className={`like-button ${game.likedByMe ? "active" : ""}`}
              onClick={() => {
                void onLikeGame(game.id).catch(() => {
                  onRequireLogin();
                });
              }}
              type="button"
            >
              <span aria-hidden="true" className="like-icon">
                ♥
              </span>
              <span className="stat-value">{displayLikes}</span>
            </button>
            <span className="stat-value">{game.plays}</span>
          </div>
          <section className="play-description-section" aria-label="游戏简介">
            <h2>游戏简介</h2>
            <p className="play-description">{game.description}</p>
          </section>
          {runtimeManifest?.controls?.length ? (
            <section className="play-controls-section" aria-label="玩法说明">
              <h2>玩法说明</h2>
              <ul className="play-controls-list">
                {controlHints.map((control) => (
                  <li key={control}>{control}</li>
                ))}
              </ul>
            </section>
          ) : null}
          <div className="tag-row">
            <span className="tag">{game.tag}</span>
          </div>
        </div>

        <section className="more-games-section" aria-label="更多同类游戏">
          <div className="more-games-head">
            <h2>猜你喜欢</h2>
          </div>
          <div className="more-games-grid">
            {relatedGames.map((relatedGame) => (
              <button
                className="more-game-card"
                key={relatedGame.id}
                onClick={() => onOpenGame(relatedGame)}
                type="button"
              >
                <span
                  className="more-game-cover"
                  style={{ backgroundImage: `url("${relatedGame.cover}")` }}
                />
                <span className="more-game-copy">
                  <strong>{relatedGame.title}</strong>
                  <span>
                    {relatedGame.author} · {relatedGame.publishedAt}
                  </span>
                  <span>
                    {relatedGame.plays} · {relatedGame.likes}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </section>
      </aside>

      <section className="play-stage-wrap">
        <div className="play-stage" data-testid="play-stage">
          {iframeSrc ? (
            <iframe
              className="play-iframe"
              onError={() => {
                setManifestError("游戏画面加载失败，请重新加载。");
                setPlayState("error");
                void createPlayEvent(game.id, "failed", {
                  stage: "iframe",
                  entry_url: iframeSrc,
                }).catch(() => {
                  logConsoleEvent("play", {
                    requestPath: "/api/play-events",
                    status: 500,
                    businessStatus: "error",
                    event_type: "failed",
                    game_id: game.id,
                  });
                });
              }}
              onLoad={() => {
                startedEventRef.current = true;
                setPlayState("ready");
                setLoadProgress(100);
                void createPlayEvent(game.id, "started", {
                  entry_url: iframeSrc,
                  elapsed_ms: Math.round(performance.now() - loadStartedAtRef.current),
                }).catch(() => {
                  logConsoleEvent("play", {
                    requestPath: "/api/play-events",
                    status: 500,
                    businessStatus: "error",
                    event_type: "started",
                    game_id: game.id,
                  });
                });
                logConsoleEvent("play", {
                  requestPath: iframeSrc,
                  status: 200,
                  businessStatus: "iframe_ready",
                  game_id: game.id,
                });
              }}
              sandbox="allow-scripts"
              src={iframeSrc}
              title={game.title}
            />
          ) : null}

          {showOverlay ? (
            <div className="loading-overlay" role="status" aria-live="polite">
              <div
                className="loading-cover"
                style={{ backgroundImage: `url("${game.cover}")` }}
              />
              <div className="loading-scrim" />
              <div className="loading-panel">
                <p className="loading-kicker">
                  {playState === "timeout" ? "Load timeout" : playState === "error" ? "Load failed" : "Loading world"}
                </p>
                <strong>{game.title}</strong>
                <span className="loading-copy">{getLoadingCopy(playState)}</span>
                {playState === "error" || playState === "timeout" ? (
                  <>
                    <span className="loading-error-text">{manifestError}</span>
                    <button
                      className="stage-retry-button"
                      onClick={() => setRetryKey((current) => current + 1)}
                      type="button"
                    >
                      重新加载
                    </button>
                  </>
                ) : (
                  <>
                    <span className="loading-progress-value">{loadProgress}%</span>
                    <div className="loading-progress-track" aria-hidden="true">
                      <div
                        className="loading-progress-fill"
                        style={{ width: `${loadProgress}%` }}
                      />
                    </div>
                  </>
                )}
              </div>
            </div>
          ) : null}

          <div className="game-hud">
            <span>{runtimeManifest?.schemaVersion ? `manifest ${runtimeManifest.schemaVersion}` : "manifest pending"}</span>
            <span>{runtimeManifest?.runtime ?? "iframe booting"}</span>
          </div>
        </div>
      </section>
    </main>
  );
}
