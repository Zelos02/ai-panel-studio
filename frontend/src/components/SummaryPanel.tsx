export function SummaryPanel({ text }: { text: string }) {
  return (
    <section className="summary-panel" aria-labelledby="summary-heading">
      <div className="summary-panel__heading"><span className="section-kicker">SESSION BRIEF</span><h2 id="summary-heading">本场讨论总结</h2><small>内容较长时可独立滚动</small></div>
      <div className="summary-panel__scroll"><p>{text}</p></div>
    </section>
  );
}
