import type { NewTopicInput, PanelResource, SessionResource, TopicResource } from "../types";

interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
    requestId?: string;
    retryable?: boolean;
  };
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    let payload: ApiErrorPayload = {};
    try { payload = await response.json() as ApiErrorPayload; } catch { /* safe fallback */ }
    throw new ApiError(
      payload.error?.message ?? "服务暂时不可用，请稍后重试。",
      payload.error?.code ?? "UNKNOWN_ERROR",
      payload.error?.retryable ?? response.status >= 500,
      response.status,
    );
  }
  return response.json() as Promise<T>;
}

export const api = {
  async listTopics(): Promise<TopicResource[]> {
    const response = await request<{ items: TopicResource[] }>("/topics");
    return response.items;
  },
  createTopic(data: NewTopicInput): Promise<TopicResource> {
    return request("/topics", { method: "POST", body: JSON.stringify(data) });
  },
  generatePanel(topicId: string): Promise<PanelResource> {
    return request(`/topics/${topicId}/panel:generate`, { method: "POST", body: "{}" });
  },
  getPanel(topicId: string): Promise<PanelResource> {
    return request(`/topics/${topicId}/experts`);
  },
  admitPanel(topicId: string, generation: number): Promise<PanelResource> {
    return request(`/topics/${topicId}/panel:admit`, {
      method: "PUT",
      body: JSON.stringify({ generation }),
    });
  },
  createSession(topicId: string, maxTurns = 18): Promise<SessionResource> {
    return request(`/topics/${topicId}/sessions`, {
      method: "POST",
      body: JSON.stringify({ maxTurns }),
    });
  },
};
