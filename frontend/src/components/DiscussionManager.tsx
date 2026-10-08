import { useEffect, useState } from "react";
import type { CSSProperties } from "react";

import type { ExpertResource, PanelResource, SessionResource, TopicResource } from "../types";

interface DiscussionManagerProps {
  topic: TopicResource;
  panel: PanelResource | null;
  sessions: SessionResource[];
  loading: boolean;
  busy: boolean;
  error: string | null;
  onClose: () => void;
  onSave: (panel: PanelResource) => void;
  onDelete: () => void;
}

type EditableField = "name" | "title" | "stance" | "publicProfile" | "color";

const topicStatusLabels: Record<TopicResource["status"], string> = {
  draft: "草稿",
  ready: "待开始",
  running: "讨论中",
  completed: "已完成",
  failed: "生成失败",
};

export function DiscussionManager({ topic, panel, sessions, loading, busy, error, onClose, onSave, onDelete }: DiscussionManagerProps) {
  const [draft, setDraft] = useState<PanelResource | null>(panel);
  const [confirmDelete, setConfirmDelete] = useState(false);
  useEffect(() => setDraft(panel), [panel]);

  const editable = Boolean(draft) && sessions.every(
    (session) => !session.startedAt && ["created", "admitted"].includes(session.status),
  );

  function updateMember(id: string, field: EditableField, value: string) {
    setDraft((current) => {
      if (!current) return current;
      const apply = (member: ExpertResource) => member.id === id ? { ...member, [field]: value } : member;
      return { ...current, host: apply(current.host), experts: current.experts.map(apply) };
    });
  }

  const members = draft ? [draft.host, ...draft.experts] : [];
  return (
    <div className="dialog-backdrop" role="presentation">
      <section className="discussion-manager" role="dialog" aria-modal="true" aria-labelledby="manager-heading">
        <button className="icon-button close-button" type="button" aria-label="关闭管理窗口" onClick={onClose}>×</button>
        <header className="manager-heading">
          <div><span className="section-kicker">DISCUSSION CONTROL</span><h2 id="manager-heading">管理讨论</h2></div>
          <span className={`status-pill status-pill--${topic.status}`}><span />{topicStatusLabels[topic.status]}</span>
        </header>
        <p className="manager-topic-title">{topic.title}</p>
        {error && <div className="error-banner" role="alert">{error}</div>}
        {loading ? <div className="loading-state">正在读取讨论配置…</div> : (
          <>
            <section className="manager-section" aria-labelledby="panel-editor-heading">
              <div className="manager-section__heading"><div><h3 id="panel-editor-heading">专家阵容</h3><p>{editable ? "场次尚未开始，可以修改身份、立场、关注点和颜色。" : "讨论已经开始或完成，阵容已锁定以保护历史记录。"}</p></div>{draft && <span>版本 #{draft.generation}</span>}</div>
              {!draft && <div className="manager-empty">这个话题还没有可编辑的专家阵容。</div>}
              {draft && <div className="manager-members">
                {members.map((member) => (
                  <article className="manager-member" key={member.id} style={{ "--expert-color": member.color } as CSSProperties}>
                    <div className="manager-member__title"><strong>{member.kind === "host" ? "主持人" : `专家 ${member.displayOrder}`}</strong><input type="color" aria-label={`${member.name}专属颜色`} disabled={!editable || busy} value={member.color} onChange={(event) => updateMember(member.id, "color", event.target.value)} /></div>
                    <div className="manager-member__grid">
                      <label>姓名<input disabled={!editable || busy} value={member.name} onChange={(event) => updateMember(member.id, "name", event.target.value)} /></label>
                      <label>职业 / Title<input disabled={!editable || busy} value={member.title} onChange={(event) => updateMember(member.id, "title", event.target.value)} /></label>
                    </div>
                    <label>立场<textarea rows={2} disabled={!editable || busy} value={member.stance} onChange={(event) => updateMember(member.id, "stance", event.target.value)} /></label>
                    <label>公开关注点<textarea rows={2} disabled={!editable || busy} value={member.publicProfile} onChange={(event) => updateMember(member.id, "publicProfile", event.target.value)} /></label>
                  </article>
                ))}
              </div>}
              {editable && draft && <div className="manager-save-row"><button className="primary-button" type="button" disabled={busy} onClick={() => onSave(draft)}>{busy ? "正在保存…" : "保存阵容修改"}</button></div>}
            </section>
            <section className="delete-zone" aria-labelledby="delete-heading">
              <div><h3 id="delete-heading">删除讨论</h3><p>将同时删除阵容、场次、发言、知识分岔与总结。此操作无法撤销。</p></div>
              {!confirmDelete ? <button className="danger-button" type="button" disabled={busy} onClick={() => setConfirmDelete(true)}>删除这场讨论</button> : <div className="delete-confirm"><span>请再次确认</span><button className="danger-button danger-button--solid" type="button" disabled={busy} onClick={onDelete}>{busy ? "正在删除…" : "确认永久删除"}</button><button className="secondary-button" type="button" disabled={busy} onClick={() => setConfirmDelete(false)}>取消</button></div>}
            </section>
          </>
        )}
      </section>
    </div>
  );
}
