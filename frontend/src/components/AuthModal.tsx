import { useEffect, useMemo, useState } from "react";

import type { AuthMode } from "../types/ui";
import "./auth-modal.css";

type AuthModalProps = {
  mode: AuthMode;
  authEmail: string;
  authDisplayName: string;
  authPassword: string;
  confirmPassword: string;
  authError: string | null;
  authMessage: string | null;
  authSubmitting: boolean;
  githubFeedbackVisible: boolean;
  onModeChange: (mode: AuthMode) => void;
  onEmailChange: (value: string) => void;
  onDisplayNameChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onConfirmPasswordChange: (value: string) => void;
  onClose: () => void;
  onSubmit: () => void;
  onGoogleLogin: () => void;
};

export function AuthModal({
  mode,
  authEmail,
  authDisplayName,
  authPassword,
  confirmPassword,
  authError,
  authMessage,
  authSubmitting,
  githubFeedbackVisible,
  onModeChange,
  onEmailChange,
  onDisplayNameChange,
  onPasswordChange,
  onConfirmPasswordChange,
  onClose,
  onSubmit,
  onGoogleLogin,
}: AuthModalProps) {
  const isLogin = mode === "login";
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setTouched({});
  }, [mode]);

  const registerValidation = useMemo(() => {
    if (isLogin) {
      return null;
    }

    const normalizedEmail = authEmail.trim();
    const normalizedDisplayName = authDisplayName.trim();
    const hasLetter = /[A-Za-z]/.test(authPassword);
    const hasDigit = /\d/.test(authPassword);
    const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail);

    return {
      displayName: {
        valid: normalizedDisplayName.length > 0,
        issue: normalizedDisplayName.length > 0 ? null : "昵称不能为空。",
      },
      email: {
        valid: emailValid,
        issue:
          normalizedEmail.length === 0
            ? "邮箱不能为空。"
            : emailValid
              ? null
              : "请输入正确的邮箱格式。",
      },
      password: {
        valid: authPassword.length >= 8 && hasLetter && hasDigit,
        issue:
          authPassword.length === 0
            ? "密码不能为空。"
            : authPassword.length < 8 || !hasLetter || !hasDigit
              ? "密码至少 8 位，且必须同时包含字母和数字。"
              : null,
      },
      confirmPassword: {
        valid: confirmPassword.length > 0 && confirmPassword === authPassword,
        issue:
          confirmPassword.length === 0
            ? "请再次输入密码。"
            : confirmPassword !== authPassword
              ? "两次输入的密码不一致。"
              : null,
      },
    };
  }, [authDisplayName, authEmail, authPassword, confirmPassword, isLogin]);

  function showIssue(key: string) {
    return Boolean(touched[key]);
  }

  function getFieldDescriptionId(key: string) {
    return `${key}-status-text`;
  }

  function renderFieldState(key: string, valid: boolean, issue: string | null) {
    if (!showIssue(key)) {
      return null;
    }
    if (valid) {
      return (
        <span className="field-state field-state-valid">
          <span
            aria-hidden="true"
            className="field-state-badge field-valid-mark"
            title="输入正确"
          >
            ✓
          </span>
          <span className="sr-only" id={getFieldDescriptionId(key)}>
            输入正确
          </span>
        </span>
      );
    }
    if (issue) {
      return (
        <span className="field-state field-state-error">
          <span
            aria-hidden="true"
            className="field-state-badge field-issue-mark"
            tabIndex={0}
            title={issue}
          >
            !
          </span>
          <span className="field-state-popover" role="status">
            {issue}
          </span>
          <span className="sr-only" id={getFieldDescriptionId(key)}>
            {issue}
          </span>
        </span>
      );
    }
    return null;
  }

  return (
    <div className="auth-modal" data-testid="auth-modal" role="dialog" aria-modal="true">
      <form
        className="auth-panel"
        onSubmit={(event) => {
          event.preventDefault();
          void onSubmit();
        }}
      >
        <button aria-label="关闭登录弹窗" className="auth-close" onClick={onClose} type="button">
          ×
        </button>
        <h2>{isLogin ? "登录" : "注册"}</h2>
        <p className="auth-subhead">
          {isLogin ? "还没有账号？" : "已有账号？"}
          <button
            onClick={() => onModeChange(isLogin ? "register" : "login")}
            type="button"
          >
            {isLogin ? "切换到注册" : "切换到登录"}
          </button>
        </p>
        {authMessage ? (
          <div className="auth-message" role="status">
            {authMessage}
          </div>
        ) : null}
        {authError ? (
          <div className="auth-error" role="alert">
            {authError}
          </div>
        ) : null}
        {!isLogin ? (
          <label className="field">
            昵称
            <div className="field-control">
              <input
                aria-describedby={getFieldDescriptionId("display_name")}
                aria-invalid={showIssue("display_name") && !(registerValidation?.displayName.valid ?? false)}
                maxLength={120}
                type="text"
                value={authDisplayName}
                onBlur={() => setTouched((current) => ({ ...current, display_name: true }))}
                onChange={(event) => onDisplayNameChange(event.target.value)}
              />
              {renderFieldState(
                "display_name",
                registerValidation?.displayName.valid ?? false,
                registerValidation?.displayName.issue ?? null,
              )}
            </div>
          </label>
        ) : null}
        <label className="field">
          邮箱
          <div className="field-control">
            <input
              aria-describedby={!isLogin ? getFieldDescriptionId("email") : undefined}
              aria-invalid={!isLogin && showIssue("email") && !(registerValidation?.email.valid ?? false)}
              autoComplete="email"
              type="email"
              value={authEmail}
              onBlur={() => setTouched((current) => ({ ...current, email: true }))}
              onChange={(event) => onEmailChange(event.target.value)}
            />
            {!isLogin
              ? renderFieldState(
                  "email",
                  registerValidation?.email.valid ?? false,
                  registerValidation?.email.issue ?? null,
                )
              : null}
          </div>
        </label>
        <label className="field">
          密码
          <div className="field-control">
            {isLogin ? (
              <input
                autoComplete="current-password"
                type="password"
                value={authPassword}
                onChange={(event) => onPasswordChange(event.target.value)}
              />
            ) : (
              <input
                aria-describedby={getFieldDescriptionId("password")}
                aria-invalid={showIssue("password") && !(registerValidation?.password.valid ?? false)}
                autoComplete="new-password"
                type="password"
                value={authPassword}
                onBlur={() => setTouched((current) => ({ ...current, password: true }))}
                onChange={(event) => onPasswordChange(event.target.value)}
              />
            )}
            {!isLogin
              ? renderFieldState(
                  "password",
                  registerValidation?.password.valid ?? false,
                  registerValidation?.password.issue ?? null,
                )
              : null}
          </div>
        </label>
        {!isLogin ? (
          <p className="password-hint">密码至少 8 位，且必须同时包含字母和数字。</p>
        ) : null}
        {!isLogin ? (
          <label className="field">
            确认密码
            <div className="field-control">
              <input
                aria-describedby={getFieldDescriptionId("confirm_password")}
                aria-invalid={
                  showIssue("confirm_password") && !(registerValidation?.confirmPassword.valid ?? false)
                }
                autoComplete="new-password"
                type="password"
                value={confirmPassword}
                onBlur={() => setTouched((current) => ({ ...current, confirm_password: true }))}
                onChange={(event) => onConfirmPasswordChange(event.target.value)}
              />
              {renderFieldState(
                "confirm_password",
                registerValidation?.confirmPassword.valid ?? false,
                registerValidation?.confirmPassword.issue ?? null,
              )}
            </div>
          </label>
        ) : null}
        <button className="primary-pill full-width" disabled={authSubmitting} type="submit">
          {authSubmitting ? "提交中..." : isLogin ? "登录" : "注册"}
        </button>
        <div className="oauth-row">
          <button
            className="secondary-pill"
            disabled={authSubmitting}
            onClick={() => {
              void onGoogleLogin();
            }}
            type="button"
          >
            Google
          </button>
          <button
            aria-describedby="github-feedback"
            className="secondary-pill"
            disabled={githubFeedbackVisible}
            title="GitHub 登录暂未启用"
            type="button"
          >
            github
          </button>
        </div>
      </form>
    </div>
  );
}
