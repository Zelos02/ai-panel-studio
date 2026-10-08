import type { BranchResource, NewTopicInput, PanelResource, PanelUpdateInput, SessionResource, SummaryResource, TopicResource, TranscriptResource } from "../types";

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
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function editableMember(member: PanelResource["host"]) {
  return {
    id: member.id,
    name: member.name,
    title: member.title,
    stance: member.stance,
    publicProfile: member.publicProfile,
    color: member.color,
  };
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
  updatePanel(topicId: string, panel: PanelUpdateInput): Promise<PanelResource> {
    return request(`/topics/${topicId}/panel`, {
      method: "PUT",
      body: JSON.stringify({
        generation: panel.generation,
        host: editableMember(panel.host),
        experts: panel.experts.map(editableMember),
      }),
    });
  },
  deleteTopic(topicId: string): Promise<void> {
    return request(`/topics/${topicId}`, { method: "DELETE" });
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
  startSession(sessionId: string): Promise<SessionResource> {
    return request(`/sessions/${sessionId}:start`, { method: "POST", body: "{}" });
  },
  stopSession(sessionId: string): Promise<SessionResource> {
    return request(`/sessions/${sessionId}:stop`, { method: "POST", body: "{}" });
  },
  async listSessions(topicId: string): Promise<SessionResource[]> {
    const response = await request<{ items: SessionResource[] }>(`/topics/${topicId}/sessions`);
    return response.items;
  },
  async getTranscript(sessionId: string): Promise<TranscriptResource[]> {
    const response = await request<{ items: TranscriptResource[] }>(`/sessions/${sessionId}/transcript`);
    return response.items;
  },
  async getBranches(sessionId: string): Promise<BranchResource[]> {
    const response = await request<{ items: BranchResource[] }>(`/sessions/${sessionId}/branches`);
    return response.items;
  },
  getSummary(sessionId: string): Promise<SummaryResource> {
    return request(`/sessions/${sessionId}/summary`);
  },
};
