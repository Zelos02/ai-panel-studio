import type { CSSProperties } from "react";
import type { TopicPreview } from "../types";

const statusLabels: Record<TopicPreview["status"], string> = {
  draft: "草稿", ready: "等待开场", running: "直播中", completed: "已完成", failed: "需要处理",
};

export function TopicCard({ topic, onOpen, onManage }: { topic: TopicPreview; onOpen: (topic: TopicPreview) => void; onManage: (topic: TopicPreview) => void }) {
  return (
    <article className="topic-card" style={{ "--topic-accent": topic.accent } as CSSProperties}>
      <div className="topic-card__topline">
        <span className={`status-pill status-pill--${topic.status}`}><span aria-hidden="true" />{statusLabels[topic.status]}</span>
        <span className="topic-card__time">{topic.updatedAt}</span>
      </div>
      <div><h3>{topic.title}</h3><p>{topic.background}</p></div>
      <div className="topic-card__meta"><span>{topic.expertCount} 位专家</span><span>{topic.progress}% 进程</span></div>
      <div className="progress-track" aria-label={`讨论进度 ${topic.progress}%`}><span style={{ width: `${topic.progress}%` }} /></div>
      <div className="topic-card__actions">
        <button className="text-button" type="button" onClick={() => onOpen(topic)}>
          {topic.status === "completed" ? "查看复盘" : "进入演播厅"}<span aria-hidden="true">↗</span>
        </button>
        <button className="manage-button" type="button" aria-label={`管理讨论：${topic.title}`} onClick={() => onManage(topic)}>管理</button>
      </div>
    </article>
  );
}
