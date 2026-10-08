import type { BranchPreview } from "../types";

const branchLabels: Record<BranchPreview["type"], string> = {
  concept: "新概念", assumption: "待检验假设", conflict: "观点冲突", question: "开放问题", direction: "延伸方向",
};

export function BranchPanel({ branches, completed = false, onOpenSource }: { branches: BranchPreview[]; completed?: boolean; onOpenSource?: () => void }) {
  const conflictCount = branches.filter((branch) => branch.type === "conflict").length;
  const openCount = branches.filter((branch) => branch.type === "assumption" || branch.type === "question").length;
  const signalText = branches.length === 0
    ? "等待形成可追踪的知识分岔"
    : completed
      ? `本场共沉淀 ${branches.length} 条知识分岔`
      : conflictCount + openCount > 0
        ? `${conflictCount + openCount} 个分歧或问题仍待推进`
        : "观点正在扩展并形成延伸方向";

  return (
    <aside className="studio-panel branch-panel" aria-labelledby="branch-heading">
      <div className="panel-heading">
        <div><span className="section-kicker">KNOWLEDGE MAP</span><h2 id="branch-heading">知识分岔</h2></div>
        <span className="count-badge">{branches.length}</span>
      </div>
      <div className="branch-list">
        {branches.length === 0 && <p className="branch-empty">发言后，新概念、冲突、问题和延伸方向会在这里实时出现。</p>}
        {branches.map((branch, index) => (
          <a className="branch-card" href={`#message-${branch.sourceMessageId}`} key={branch.id} onClick={onOpenSource}>
            <span className="branch-index">0{index + 1}</span>
            <div><small>{branchLabels[branch.type]}</small><h3>{branch.title}</h3><p>{branch.summary}</p><span className="source-link">定位来源发言 →</span></div>
          </a>
        ))}
      </div>
      <div className="signal-card" aria-live="polite">
        <span className="signal-card__icon" aria-hidden="true">⌁</span>
        <div><small>讨论结构 · 实时统计</small><strong>{signalText}</strong><span className="signal-breakdown">{conflictCount} 个观点冲突 · {openCount} 个待验证问题</span></div>
        <span className="signal-score"><b>{branches.length}</b><small>分岔</small></span>
      </div>
    </aside>
  );
}
