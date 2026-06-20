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
          <div className="user-area logged-in">
            <button
              className="avatar-button"
              aria-label={`${currentUser?.display_name ?? "当前用户"} 用户菜单`}
            >
              {currentUser?.avatar_url ? (
                <img
                  className="avatar-image"
                  src={currentUser.avatar_url}
                  alt=""
                  aria-hidden="true"
                />
              ) : (
                <span className="avatar" aria-hidden="true" />
              )}
            </button>
            <span className="user-label">
              {currentUser?.display_name ?? currentUser?.email ?? "已登录用户"}
            </span>
            <div className="user-menu">
              <span>{currentUser?.display_name ?? currentUser?.email ?? "已登录用户"}</span>
              <button onClick={onLogout}>退出登录</button>
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
