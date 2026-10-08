export type TopicStatus = "draft" | "ready" | "running" | "completed" | "failed";
export type ExpertState = "waiting" | "preparing" | "speaking";

export interface TopicPreview {
  id: string;
  title: string;
  background: string;
  status: TopicStatus;
  expertCount: number;
  updatedAt: string;
  progress: number;
  accent: string;
}

export interface ExpertPreview {
  id: string;
  name: string;
  title: string;
  stance: string;
  color: string;
  initials: string;
  state: ExpertState;
  publicFocus: string;
  kind?: "host" | "expert";
}

export interface TranscriptPreview {
  id: string;
  speakerId: string;
  content: string;
  time: string;
}

export interface BranchPreview {
  id: string;
  type: "concept" | "assumption" | "conflict" | "question" | "direction";
  title: string;
  summary: string;
  sourceMessageId: string;
}

export interface TopicResource {
  id: string;
  title: string;
  background: string | null;
  goal: string | null;
  requestedExpertCount: number;
  panelGeneration: number;
  status: TopicStatus;
  createdAt: string;
  updatedAt: string;
}

export interface ExpertResource {
  id: string;
  topicId: string;
  kind: "host" | "expert";
  name: string;
  title: string;
  stance: string;
  publicProfile: string;
  color: string;
  displayOrder: number;
  admitted: boolean;
}

export interface PanelResource {
  topicId: string;
  generation: number;
  host: ExpertResource;
  experts: ExpertResource[];
}

export interface SessionResource {
  id: string;
  topicId: string;
  status: string;
  turnCount: number;
  maxTurns: number;
  lastEventSequence: number;
  createdAt: string;
  startedAt: string | null;
  endedAt: string | null;
}

export interface TranscriptResource {
  id: string;
  sequence: number;
  content: string;
  createdAt: string;
  speaker: {
    id: string;
    name: string;
    title: string;
    color: string;
    role: "host" | "expert";
  };
}

export type SessionEventType = "session.state" | "expert.status" | "transcript.append" | "branch.created" | "summary.ready" | "stream.error" | "heartbeat";

export interface SessionEvent<T = Record<string, unknown>> {
  eventId: number;
  topicId: string | null;
  sessionId: string;
  timestamp: string;
  eventType: SessionEventType;
  payload: T;
}

export interface NewTopicInput {
  title: string;
  background?: string;
  goal?: string;
  requestedExpertCount: number;
}
