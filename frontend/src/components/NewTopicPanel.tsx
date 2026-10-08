export function NewTopicPanel({ onClose, onPreview }: { onClose: () => void; onPreview: () => void }) {
  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={onClose}>
      <section aria-labelledby="new-topic-heading" aria-modal="true" className="new-topic-panel" role="dialog" onMouseDown={(event) => event.stopPropagation()}>
        <button className="icon-button close-button" type="button" onClick={onClose} aria-label="关闭">×</button>
        <span className="section-kicker">NEW SESSION</span>
        <h2 id="new-topic-heading">把一个难题带上圆桌</h2>
        <p>给系统足够的背景，它会为你邀请立场互补的虚拟专家。</p>
        <label>讨论主题<textarea defaultValue="AI 是否应该参与招聘终审？" rows={3} /></label>
        <div className="form-grid">
          <label>专家人数<select defaultValue="4"><option value="2">2 位</option><option value="3">3 位</option><option value="4">4 位（推荐）</option><option value="5">5 位</option><option value="6">6 位</option></select></label>
          <label>讨论节奏<select defaultValue="focused"><option value="focused">聚焦 · 约 10 分钟</option><option value="deep">深入 · 约 20 分钟</option></select></label>
        </div>
        <label>背景与目标（可选）<textarea placeholder="补充业务背景、已知约束或最希望回答的问题…" rows={4} /></label>
        <div className="dialog-actions">
          <button className="secondary-button" type="button" onClick={onClose}>暂时取消</button>
          <button className="primary-button" type="button" onClick={onPreview}>生成专家阵容 <span aria-hidden="true">→</span></button>
        </div>
      </section>
    </div>
  );
}
