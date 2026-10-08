import type { CSSProperties } from "react";
import type { PanelResource, TopicResource } from "../types";
import { Brand } from "./Brand";

interface PanelAdmissionProps {
  topic: TopicResource;
  panel: PanelResource;
  busy: boolean;
  error: string | null;
  onBack: () => void;
  onRegenerate: () => void;
  onAdmit: () => void;
}

export function PanelAdmission({ topic, panel, busy, error, onBack, onRegenerate, onAdmit }: PanelAdmissionProps) {
  const members = [panel.host, ...panel.experts];
  return (
    <div className="admission-shell">
      <header className="admission-header">
        <button className="brand-button" type="button" onClick={onBack}><Brand /></button>
        <span>阵容版本 #{String(panel.generation).padStart(2, "0")}</span>
      </header>
      <main className="admission-main">
        <div className="admission-copy">
          <span className="section-kicker">CASTING ROOM</span>
          <h1>嘉宾已经就位。<br /><em>确认谁将坐上圆桌。</em></h1>
          <p>{topic.title}</p>
        </div>
        {error && <div className="error-banner" role="alert">{error}</div>}
        <section className="cast-grid" aria-label="待确认专家阵容">
          {members.map((member) => (
            <article className={`cast-card ${member.kind === "host" ? "cast-card--host" : ""}`} key={member.id} style={{ "--expert-color": member.color } as CSSProperties}>
              <div className="cast-card__top"><span>{member.kind === "host" ? "HOST" : `SEAT ${String(member.displayOrder).padStart(2, "0")}`}</span><i /></div>
              <div className="cast-avatar">{member.name.slice(0, 1)}</div>
              <h2>{member.name}</h2><small>{member.title}</small>
              <p>{member.stance}</p>
              <div className="cast-focus"><span>关注领域</span>{member.publicProfile}</div>
            </article>
          ))}
        </section>
        <div className="admission-actions">
          <button className="secondary-button" type="button" disabled={busy} onClick={onRegenerate}>重新生成阵容</button>
          <button className="primary-button primary-button--large" type="button" disabled={busy} onClick={onAdmit}>{busy ? "正在处理…" : "确认入场并创建演播厅"} <span aria-hidden="true">→</span></button>
        </div>
      </main>
    </div>
  );
}
