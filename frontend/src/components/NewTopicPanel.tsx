import { useState } from "react";
import type { FormEvent } from "react";
import type { NewTopicInput } from "../types";

export function NewTopicPanel({ onClose, onSubmit }: { onClose: () => void; onSubmit: (data: NewTopicInput) => Promise<void> }) {
  const [title, setTitle] = useState("AI 是否应该参与招聘终审？");
  const [background, setBackground] = useState("");
  const [goal, setGoal] = useState("");
  const [count, setCount] = useState(4);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) { setError("请输入讨论主题。"); return; }
    setBusy(true); setError(null);
    try {
      await onSubmit({ title: title.trim(), background: background.trim() || undefined, goal: goal.trim() || undefined, requestedExpertCount: count });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "创建失败，请稍后重试。");
      setBusy(false);
    }
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={() => !busy && onClose()}>
      <form aria-labelledby="new-topic-heading" aria-modal="true" className="new-topic-panel" role="dialog" onSubmit={submit} onMouseDown={(event) => event.stopPropagation()}>
        <button className="icon-button close-button" type="button" disabled={busy} onClick={onClose} aria-label="关闭">×</button>
        <span className="section-kicker">NEW SESSION</span>
        <h2 id="new-topic-heading">把一个难题带上圆桌</h2>
        <p>给系统足够的背景，它会为你邀请立场互补的虚拟专家。</p>
        {error && <div className="error-banner" role="alert">{error}</div>}
        <label>讨论主题<textarea value={title} onChange={(event) => setTitle(event.target.value)} rows={3} maxLength={200} /></label>
        <div className="form-grid">
          <label>专家人数<select value={count} onChange={(event) => setCount(Number(event.target.value))}><option value="2">2 位</option><option value="3">3 位</option><option value="4">4 位（推荐）</option><option value="5">5 位</option><option value="6">6 位</option></select></label>
          <label>讨论目标<input value={goal} onChange={(event) => setGoal(event.target.value)} placeholder="例如：形成可执行的决策建议" /></label>
        </div>
        <label>背景说明（可选）<textarea value={background} onChange={(event) => setBackground(event.target.value)} placeholder="补充业务背景、已知约束或争议来源…" rows={4} /></label>
        <div className="dialog-actions"><button className="secondary-button" type="button" disabled={busy} onClick={onClose}>暂时取消</button><button className="primary-button" type="submit" disabled={busy}>{busy ? "正在召集专家…" : "生成专家阵容"} <span aria-hidden="true">→</span></button></div>
      </form>
    </div>
  );
}
