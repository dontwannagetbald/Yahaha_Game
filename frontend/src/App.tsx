import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  Layout,
  Modal,
  Space,
  Typography,
} from "antd";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type User = {
  user_id: string;
  email: string | null;
  display_name: string | null;
  avatar_url: string | null;
};

type AuthMode = "login" | "register";

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const message = body?.error?.message ?? "Request failed";
    throw new Error(message);
  }
  return body as T;
}

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  async function refreshMe() {
    try {
      const response = await apiRequest<{ user: User }>("/api/auth/me");
      setUser(response.user);
    } catch {
      setUser(null);
    }
  }

  useEffect(() => {
    refreshMe();
  }, []);

  async function submitAuth(values: { email: string; password: string }) {
    setLoading(true);
    setError(null);
    try {
      const path = authMode === "login" ? "/api/auth/login" : "/api/auth/register";
      const response = await apiRequest<{ user: User }>(path, {
        method: "POST",
        body: JSON.stringify(values),
      });
      setUser(response.user);
      setAuthOpen(false);
      form.resetFields();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    await apiRequest("/api/auth/logout", { method: "POST" });
    setUser(null);
  }

  async function startGoogleLogin() {
    setLoading(true);
    setError(null);
    try {
      const response = await apiRequest<{ authorization_url: string }>(
        "/api/auth/oauth/google/start",
      );
      window.location.href = response.authorization_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google OAuth failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout className="app-shell">
      <header className="top-nav">
        <Typography.Title level={3} className="brand">
          Yahaha Game
        </Typography.Title>
        <Space>
          <Button type="link">Home</Button>
          <Button
            type="link"
            onClick={() => {
              if (!user) {
                setAuthMode("login");
                setAuthOpen(true);
              }
            }}
          >
            Create
          </Button>
          {user ? (
            <>
              <Typography.Text className="session-label">
                {user.email ?? user.display_name ?? user.user_id}
              </Typography.Text>
              <Button onClick={logout}>Logout</Button>
            </>
          ) : (
            <Button
              type="primary"
              shape="round"
              onClick={() => {
                setAuthMode("login");
                setAuthOpen(true);
              }}
            >
              Sign In
            </Button>
          )}
        </Space>
      </header>

      <main className="hero">
        <Card className="hero-card">
          <Typography.Title>Anyone can Yahaha.</Typography.Title>
          <Typography.Paragraph>
            Auth/OAuth foundation is ready. Visitors can browse and play; creators
            sign in from this modal before Create and Publish.
          </Typography.Paragraph>
          <Space>
            <Button
              type="primary"
              shape="round"
              size="large"
              onClick={() => {
                setAuthMode("register");
                setAuthOpen(true);
              }}
            >
              Create account
            </Button>
            <Button shape="round" size="large">
              Browse games
            </Button>
          </Space>
        </Card>
      </main>

      <Modal
        title={authMode === "login" ? "Sign in" : "Create account"}
        open={authOpen}
        onCancel={() => {
          setAuthOpen(false);
          setError(null);
        }}
        footer={null}
      >
        <Space direction="vertical" size="middle" className="auth-stack">
          {error ? <Alert type="error" message={error} showIcon /> : null}
          <Form form={form} layout="vertical" onFinish={submitAuth}>
            <Form.Item
              label="Email"
              name="email"
              rules={[{ required: true }, { type: "email" }]}
            >
              <Input autoComplete="email" />
            </Form.Item>
            <Form.Item
              label="Password"
              name="password"
              rules={[{ required: true }, { min: 8 }]}
            >
              <Input.Password autoComplete="current-password" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              {authMode === "login" ? "Sign in" : "Create account"}
            </Button>
          </Form>
          <Button block onClick={startGoogleLogin} loading={loading}>
            Continue with Google
          </Button>
          <Button block disabled>
            Continue with GitHub - coming later
          </Button>
          <Button
            type="link"
            block
            onClick={() => {
              setAuthMode(authMode === "login" ? "register" : "login");
              setError(null);
            }}
          >
            {authMode === "login"
              ? "Need an account? Register"
              : "Already have an account? Sign in"}
          </Button>
        </Space>
      </Modal>
    </Layout>
  );
}
