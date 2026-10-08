import type { CSSProperties } from "react";
import type { ExpertPreview, TranscriptPreview } from "../types";

export function TranscriptPanel({ experts, transcript }: { experts: ExpertPreview[]; transcript: TranscriptPreview[] }) {
  const people = new Map(experts.map((expert) => [expert.id, expert]));
  return (
    <section className="studio-panel transcript-panel" aria-labelledby="transcript-heading">
      <div className="panel-heading transcript-heading">
        <div><span className="section-kicker">LIVE TRANSCRIPT</span><h2 id="transcript-heading">观点现场</h2></div>
        <div className="live-indicator" aria-label="直播进行中"><span />LIVE</div>
      </div>
      <div className="transcript-scroll" aria-live="polite">
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
        <div className="composing-row" aria-label="林澈正在发言">
          <span className="mini-wave" aria-hidden="true"><i /><i /><i /><i /></span>林澈正在组织观点…
        </div>
      </div>
    </section>
  );
}
