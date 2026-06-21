import { useEffect, useRef, useState } from "react";

import type { AuthUser } from "../api/auth";

type TopNavProps = {
  isLoggedIn: boolean;
  currentUser: AuthUser | null;
  currentPath: string;
  onHome: () => void;
  onCreate: () => void;
  onLogin: () => void;
  onLogout: () => void;
};

const USER_MENU_CLOSE_DELAY_MS = 180;

function getUserAvatarInitial(user: AuthUser | null): string {
  const displayName = user?.display_name?.trim();
  const emailPrefix = user?.email?.split("@", 1)[0]?.trim();
  const label = displayName || emailPrefix || "我";
  return label.slice(0, 1).toUpperCase();
}

export function TopNav({
  isLoggedIn,
  currentUser,
  currentPath,
  onHome,
  onCreate,
  onLogin,
  onLogout,
}: TopNavProps) {
  const isHomeActive = currentPath === "/" || currentPath.startsWith("/play/");
  const isCreateActive = currentPath === "/create";
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const closeTimerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (closeTimerRef.current !== null) {
        window.clearTimeout(closeTimerRef.current);
      }
    };
  }, []);

  function clearCloseUserMenuTimer() {
    if (closeTimerRef.current !== null) {
      window.clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  }

  function handleOpenUserMenu() {
    clearCloseUserMenuTimer();
    setUserMenuOpen(true);
  }

  function scheduleCloseUserMenu() {
    clearCloseUserMenuTimer();
    closeTimerRef.current = window.setTimeout(() => {
      setUserMenuOpen(false);
      closeTimerRef.current = null;
    }, USER_MENU_CLOSE_DELAY_MS);
  }

  return (
    <nav className="top-nav">
      <button className="brand-button" onClick={onHome}>
        Yahaha_Play
      </button>
      <div className="nav-actions">
        <div className="nav-tabs">
          <button className={isHomeActive ? "active" : ""} onClick={onHome}>
            主页
          </button>
          <button className={isCreateActive ? "active" : ""} onClick={onCreate}>
            创建游戏
          </button>
        </div>
        {isLoggedIn ? (
          <div
            className={`user-area logged-in ${userMenuOpen ? "menu-open" : ""}`}
            onMouseEnter={handleOpenUserMenu}
            onMouseLeave={scheduleCloseUserMenu}
            onFocus={handleOpenUserMenu}
            onBlur={scheduleCloseUserMenu}
          >
            <button
              className="avatar-button"
              aria-label={`${currentUser?.display_name ?? "当前用户"} 用户菜单`}
              aria-expanded={userMenuOpen}
              aria-haspopup="menu"
              type="button"
            >
              {currentUser?.avatar_url ? (
                <img
                  className="avatar-image"
                  src={currentUser.avatar_url}
                  alt=""
                  aria-hidden="true"
                />
              ) : (
                <span className="avatar" aria-hidden="true">
                  {getUserAvatarInitial(currentUser)}
                </span>
              )}
            </button>
            <span className="user-label">
              {currentUser?.display_name ?? currentUser?.email ?? "已登录用户"}
            </span>
            <div className="user-menu" role="menu">
              <span>{currentUser?.display_name ?? currentUser?.email ?? "已登录用户"}</span>
              <button onClick={onLogout} role="menuitem" type="button">
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
