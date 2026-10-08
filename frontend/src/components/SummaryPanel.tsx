export function SummaryPanel({ text }: { text: string }) {
  return (
    <section className="summary-panel" aria-labelledby="summary-heading">
      <div><span className="section-kicker">SESSION BRIEF</span><h2 id="summary-heading">本场讨论总结</h2></div>
      <p>{text}</p>
    </section>
  );
}
