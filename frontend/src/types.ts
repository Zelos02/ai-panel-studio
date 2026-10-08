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
