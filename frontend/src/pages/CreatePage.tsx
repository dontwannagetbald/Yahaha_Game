import { useEffect, useRef, useState, type ChangeEvent } from "react";

import { logConsoleEvent } from "../lib/console";
import type { MockTask } from "../mock/runtime";
import "./create.css";

type CreatePageProps = {
  tasks: MockTask[];
};

export function CreatePage({ tasks }: CreatePageProps) {
  const [tasksExpanded, setTasksExpanded] = useState(true);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    logConsoleEvent("create", {
      requestPath: "/api/jobs",
      status: 200,
      businessStatus: "mock_jobs",
      count: tasks.length,
    });
  }, [tasks.length]);

  function handleFileSelect(event: ChangeEvent<HTMLInputElement>) {
    const nextFiles = Array.from(event.target.files ?? []).map((file) => file.name);
    setSelectedFiles((current) => {
      const merged = [...current];

      for (const fileName of nextFiles) {
        if (!merged.includes(fileName)) {
          merged.push(fileName);
        }
      }

      return merged;
    });
    event.target.value = "";
  }

  function handleRemoveFile(fileName: string) {
    setSelectedFiles((current) => current.filter((item) => item !== fileName));
  }

  return (
    <main className="create-page create-layout" data-testid="create-workspace">
      <aside className="create-side-panel">
        <div className={`tasks-shell ${tasksExpanded ? "tasks-expanded" : ""}`}>
          <button
            aria-expanded={tasksExpanded}
            className="tasks-toggle"
            onClick={() => setTasksExpanded((current) => !current)}
            type="button"
          >
            <span>
              <strong>任务列表</strong>
              <small>查看历史任务和当前进度</small>
            </span>
            <span aria-hidden="true" className="tasks-toggle-icon">
              {tasksExpanded ? "⌃" : "⌄"}
            </span>
          </button>
          {tasksExpanded ? (
            <div className="tasks-list">
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
          ) : null}
        </div>

        <section className="conversation-shell">
          <div className="conversation-head">
            <h1>和 Agent 一起定义你的游戏</h1>
            <p>先聊创意、玩法和目标，确认后再进入生成。</p>
          </div>

          <div className="message-stream">
            <article className="message-row agent">
              <span className="message-avatar">AI</span>
              <div className="message-bubble">
                您好，今天想创建个什么样的游戏？
              </div>
            </article>

            <article className="message-row suggestion-row">
              <button className="suggestion-chip" type="button">
                策略类
              </button>
              <button className="suggestion-chip" type="button">
                射击类
              </button>
              <button className="suggestion-chip" type="button">
                经营类
              </button>
            </article>

            <article className="message-row system-note">
              <p>
                agent 和用户聊天过程中会不断提问澄清需求，并在每一轮返回里给出建议，最后生成游戏介绍卡片供用户确认。
              </p>
            </article>

            <article className="message-row agent">
              <span className="message-avatar">AI</span>
              <div className="confirm-card">
                <h2>最终确认卡片</h2>
                <ul>
                  <li>游戏类型：策略类塔防</li>
                  <li>核心玩法：布置炮塔并抵挡成群敌人</li>
                  <li>胜利条件：守住基地并完成 5 波进攻</li>
                </ul>
              </div>
            </article>
          </div>

          <div className="composer-shell">
            {selectedFiles.length > 0 ? (
              <div className="selected-files">
                {selectedFiles.map((fileName) => (
                  <span className="selected-file-chip" key={fileName}>
                    <span className="selected-file-name">{fileName}</span>
                    <button
                      aria-label={`删除附件 ${fileName}`}
                      className="remove-file-button"
                      onClick={() => handleRemoveFile(fileName)}
                      type="button"
                    >
                      x
                    </button>
                  </span>
                ))}
              </div>
            ) : null}
            <div className="composer-input-wrap">
              <textarea placeholder="placeholder：创建 agent 给的随机游戏描述建议" />
              <input
                className="sr-only"
                onChange={handleFileSelect}
                ref={fileInputRef}
                type="file"
                multiple
              />
              <div className="composer-floating-actions">
                <button
                  className="icon-button"
                  aria-label="附件"
                  onClick={() => fileInputRef.current?.click()}
                  type="button"
                >
                  📎
                </button>
                <button className="primary-pill" type="button">
                  发送
                </button>
              </div>
            </div>
          </div>
        </section>
      </aside>

      <section className="workspace-stage">
        <div className="generate-panel">
          <div className="workspace-head">
            <h1>生成游戏显示面板</h1>
            <p>这里展示当前任务状态、预览结果和 Agent 执行进度。</p>
          </div>
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
