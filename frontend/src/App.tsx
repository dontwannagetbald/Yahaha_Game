import { Layout, Typography } from "antd";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function App() {
  return (
    <Layout className="app-shell">
      <Typography.Title level={1}>Yahaha Game</Typography.Title>
      <Typography.Text>Frontend is running. API: {apiBaseUrl}</Typography.Text>
    </Layout>
  );
}
