import type { BranchPreview } from "../types";

const branchLabels: Record<BranchPreview["type"], string> = {
  concept: "新概念", assumption: "待检验假设", conflict: "观点冲突", question: "开放问题", direction: "延伸方向",
};

export function BranchPanel({ branches }: { branches: BranchPreview[] }) {
  return (
    <aside className="studio-panel branch-panel" aria-labelledby="branch-heading">
      <div className="panel-heading">
        <div><span className="section-kicker">KNOWLEDGE MAP</span><h2 id="branch-heading">知识分岔</h2></div>
        <span className="count-badge">{branches.length}</span>
      </div>
      <div className="branch-list">
        {branches.map((branch, index) => (
          <a className="branch-card" href={`#message-${branch.sourceMessageId}`} key={branch.id}>
            <span className="branch-index">0{index + 1}</span>
            <div><small>{branchLabels[branch.type]}</small><h3>{branch.title}</h3><p>{branch.summary}</p><span className="source-link">定位来源发言 →</span></div>
          </a>
        ))}
      </div>
      <div className="signal-card">
        <span className="signal-card__icon" aria-hidden="true">⌁</span>
        <div><small>讨论信号</small><strong>分歧正在收敛</strong></div><span className="signal-score">72</span>
      </div>
    </aside>
  );
}
