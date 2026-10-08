import type { CSSProperties } from "react";
import type { ExpertPreview } from "../types";

const stateLabels: Record<ExpertPreview["state"], string> = {
  waiting: "倾听中", preparing: "准备发言", speaking: "正在发言",
};

export function ExpertRail({ experts }: { experts: ExpertPreview[] }) {
  return (
    <aside className="studio-panel expert-rail" aria-labelledby="expert-heading">
      <div className="panel-heading">
        <div><span className="section-kicker">PANEL</span><h2 id="expert-heading">圆桌成员</h2></div>
        <span className="count-badge">{experts.length}</span>
      </div>
      <div className="expert-list">
        {experts.map((expert) => (
          <article className={`expert-card expert-card--${expert.state}`} key={expert.id} style={{ "--expert-color": expert.color } as CSSProperties}>
            <div className="expert-card__identity">
              <span className="expert-avatar" aria-hidden="true">{expert.initials}</span>
              <span className="expert-card__name"><strong>{expert.name}</strong><small>{expert.title}</small></span>
              <span className="expert-state-dot" aria-label={stateLabels[expert.state]} />
            </div>
            <p className="expert-stance">{expert.stance}</p>
            <div className="focus-note"><span>{stateLabels[expert.state]}</span><p>{expert.publicFocus}</p></div>
          </article>
        ))}
      </div>
    </aside>
  );
}
