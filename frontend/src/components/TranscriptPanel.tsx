import type { CSSProperties } from "react";
import type { ExpertPreview, TranscriptPreview } from "../types";

export function TranscriptPanel({ experts, transcript, isRunning = false, isCompleted = false }: { experts: ExpertPreview[]; transcript: TranscriptPreview[]; isRunning?: boolean; isCompleted?: boolean }) {
  const people = new Map(experts.map((expert) => [expert.id, expert]));
  return (
    <section className="studio-panel transcript-panel" aria-labelledby="transcript-heading">
      <div className="panel-heading transcript-heading">
        <div><span className="section-kicker">LIVE TRANSCRIPT</span><h2 id="transcript-heading">观点现场</h2></div>
        <div className={`live-indicator ${isRunning ? "" : "live-indicator--archive"}`} aria-label={isRunning ? "直播进行中" : "讨论记录"}><span />{isRunning ? "LIVE" : isCompleted ? "ARCHIVE" : "READY"}</div>
      </div>
      <div className="transcript-scroll" aria-live="polite">
        {transcript.length === 0 && (
          <div className="empty-stage"><span aria-hidden="true">◌</span><strong>阵容已经就位</strong><p>启动讨论后，主持人与专家的发言会在这里实时出现。</p></div>
        )}
        {transcript.map((message, index) => {
          const speaker = people.get(message.speakerId);
          if (!speaker) return null;
          return (
            <article className={`message ${speaker.kind === "host" ? "message--host" : ""}`} id={`message-${message.id}`} key={message.id} style={{ "--speaker-color": speaker.color } as CSSProperties}>
              <div className="message__rail"><span>{String(index + 1).padStart(2, "0")}</span><i /></div>
              <div className="message__content">
                <header>
                  <span className="message-avatar" aria-hidden="true">{speaker.initials}</span>
                  <span><strong>{speaker.name}</strong><small>{speaker.title}</small></span>
                  <time>{message.time}</time>
                </header>
                <p>{message.content}</p>
              </div>
            </article>
          );
        })}
        {isRunning && <div className="composing-row" aria-label="专家正在组织观点"><span className="mini-wave" aria-hidden="true"><i /><i /><i /><i /></span>专家正在组织观点…</div>}
      </div>
    </section>
  );
}
