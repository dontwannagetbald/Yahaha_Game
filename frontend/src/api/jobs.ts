import { requestJson } from "./client";

export type JobStatus = "pending" | "running" | "succeeded" | "failed";

export type RawJob = {
  job_id: string;
  session_id: string | null;
  parent_job_id: string | null;
  title: string;
  status: JobStatus;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  game_id: string | null;
  cover_url?: string | null;
  result_summary: string | null;
  error_message: string | null;
  validation_report: Record<string, unknown> | null;
  artifact_prefix?: string | null;
  manifest_url?: string | null;
  artifact_base_url?: string | null;
  confirmation?: Record<string, unknown> | null;
  game_plan?: Record<string, unknown> | null;
  material_usage?: Record<string, unknown> | null;
  user_requirements?: Record<string, unknown> | null;
  prompt?: string | null;
};

export type RawAgentLog = {
  step: string;
  level: "info" | "warning" | "error";
  message: string;
  created_at: string;
};

type JobsResponse = {
  jobs: RawJob[];
};

type JobLogsResponse = {
  logs: RawAgentLog[];
};

type CreateJobRequest = {
  session_id: string;
  prompt?: string;
};

type CreateJobResponse = {
  job_id: string;
  session_id: string;
  status: JobStatus;
  created_at: string;
};

type CreateRevisionJobRequest = {
  message: string;
};

type CreateRevisionJobResponse = {
  job_id: string;
  session_id: string | null;
  parent_job_id: string | null;
  revision_intent: string | null;
  status: JobStatus;
  created_at: string;
};

function printCreateJobResponse(label: string, payload: unknown): void {
  console.info(`[create][api] ${label}`, payload);
}

export async function listJobs(): Promise<{ jobs: RawJob[] }> {
  const response = await requestJson<JobsResponse>("/api/jobs");
  printCreateJobResponse("GET /api/jobs raw response", response);

  return {
    jobs: response?.jobs ?? [],
  };
}

export async function getJob(jobId: string): Promise<RawJob> {
  const response = await requestJson<RawJob>(`/api/jobs/${jobId}`);
  printCreateJobResponse(`GET /api/jobs/${jobId} raw response`, response);

  if (!response?.job_id) {
    throw new Error("Job response is incomplete.");
  }

  return response;
}

export async function getJobLogs(jobId: string): Promise<{ logs: RawAgentLog[] }> {
  const response = await requestJson<JobLogsResponse>(`/api/jobs/${jobId}/logs`);
  printCreateJobResponse(`GET /api/jobs/${jobId}/logs raw response`, response);

  return {
    logs: response?.logs ?? [],
  };
}

export async function createJob(payload: CreateJobRequest): Promise<CreateJobResponse> {
  const response = await requestJson<CreateJobResponse>("/api/jobs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  printCreateJobResponse("POST /api/jobs raw response", response);

  if (!response?.job_id || !response.session_id) {
    throw new Error("Create job response is incomplete.");
  }

  return response;
}

export async function createRevisionJob(
  jobId: string,
  payload: CreateRevisionJobRequest,
): Promise<CreateRevisionJobResponse> {
  const response = await requestJson<CreateRevisionJobResponse>(`/api/jobs/${jobId}/revisions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  printCreateJobResponse(`POST /api/jobs/${jobId}/revisions raw response`, response);

  if (!response?.job_id) {
    throw new Error("Create revision job response is incomplete.");
  }

  return response;
}

export async function deleteJob(jobId: string): Promise<void> {
  await requestJson<void>(`/api/jobs/${jobId}`, {
    method: "DELETE",
  });
  printCreateJobResponse(`DELETE /api/jobs/${jobId} raw response`, { ok: true });
}
