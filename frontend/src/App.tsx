import { useEffect, useState } from "react";
import type { CSSProperties } from "react";

import { BranchPanel } from "./components/BranchPanel";
import { Brand } from "./components/Brand";
import { ExpertRail } from "./components/ExpertRail";
import { NewTopicPanel } from "./components/NewTopicPanel";
import { PanelAdmission } from "./components/PanelAdmission";
import { TopicCard } from "./components/TopicCard";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { useSessionEvents } from "./hooks/useSessionEvents";
import { experts as heroExperts } from "./mockData";
import { ApiError, api } from "./services/api";
import type { BranchPreview, ExpertPreview, NewTopicInput, PanelResource, SessionEvent, SessionResource, TopicPreview, TopicResource, TranscriptPreview, TranscriptResource } from "./types";

type View = "home" | "admission" | "studio";

function toTopicPreview(topic: TopicResource): TopicPreview {
  const progress = { draft: 8, ready: 18, running: 62, completed: 100, failed: 0 }[topic.status];
  const accent = { draft: "#8093A8", ready: "#F6C177", running: "#69E4CE", completed: "#8DA8FF", failed: "#FF8B9C" }[topic.status];
  return { id: topic.id, title: topic.title, background: topic.background || topic.goal || "等待专家从不同视角拆解这个问题", status: topic.status, expertCount: topic.requestedExpertCount, updatedAt: new Intl.DateTimeFormat("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(topic.updatedAt)), progress, accent };
}

function toExpertPreview(expert: PanelResource["host"]): ExpertPreview {
  return { id: expert.id, name: expert.name, title: `${expert.title}${expert.kind === "host" ? " · 主持人" : ""}`, stance: expert.stance, color: expert.color, initials: expert.name.slice(0, 1), state: "waiting", publicFocus: expert.publicProfile, kind: expert.kind };
}

function connectionLabel(value: string) {
  return { idle: "等待连接", connecting: "正在连接", connected: "实时同步", reconnecting: "正在重连", error: "连接异常" }[value] ?? value;
}

export default function App() {
  const [view, setView] = useState<View>("home");
  const [composerOpen, setComposerOpen] = useState(false);
  const [topics, setTopics] = useState<TopicResource[]>([]);
  const [activeTopic, setActiveTopic] = useState<TopicResource | null>(null);
  const [activePanel, setActivePanel] = useState<PanelResource | null>(null);
  const [activeSession, setActiveSession] = useState<SessionResource | null>(null);
  const [liveExperts, setLiveExperts] = useState<ExpertPreview[]>([]);
  const [liveTranscript, setLiveTranscript] = useState<TranscriptPreview[]>([]);
  const [liveBranches, setLiveBranches] = useState<BranchPreview[]>([]);
  const [streamEnabled, setStreamEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);

  useEffect(() => {
    void loadTopics();
    function closeOnEscape(event: KeyboardEvent) { if (event.key === "Escape") setComposerOpen(false); }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  function handleSessionEvent(event: SessionEvent) {
    if (!activeSession || event.sessionId !== activeSession.id) return;
    if (event.eventType === "session.state") {
      const status = String(event.payload.status);
      setActiveSession((current) => current ? { ...current, status } : current);
      if (["completed", "failed"].includes(status)) setStreamEnabled(false);
    } else if (event.eventType === "expert.status") {
      const expertId = String(event.payload.expertId);
      setLiveExperts((current) => current.map((expert) => expert.id === expertId ? { ...expert, state: String(event.payload.state) as ExpertPreview["state"], publicFocus: String(event.payload.publicFocus || expert.publicFocus) } : expert));
    } else if (event.eventType === "transcript.append") {
      const message = event.payload.message as TranscriptResource;
      setLiveTranscript((current) => current.some((item) => item.id === message.id) ? current : [...current, { id: message.id, speakerId: message.speaker.id, content: message.content, time: new Intl.DateTimeFormat("zh-CN", { hour: "2-digit", minute: "2-digit" }).format(new Date(message.createdAt)) }]);
      setActiveSession((current) => current && message.speaker.role === "expert" ? { ...current, turnCount: Math.max(current.turnCount, message.sequence - 1) } : current);
    } else if (event.eventType === "branch.created") {
      const branch = event.payload.branch as BranchPreview;
      setLiveBranches((current) => current.some((item) => item.id === branch.id) ? current : [...current, branch]);
    } else if (event.eventType === "stream.error") {
      setPageError(String(event.payload.message || "讨论流暂时中断。"));
    }
  }

  const streamActive = streamEnabled && !["completed", "failed"].includes(activeSession?.status ?? "");
  const { connectionState } = useSessionEvents(activeSession?.id ?? null, streamActive, handleSessionEvent);

  async function loadTopics() {
    setLoading(true); setPageError(null);
    try { setTopics(await api.listTopics()); }
    catch (reason) { setPageError(reason instanceof Error ? reason.message : "无法读取讨论话题。"); }
    finally { setLoading(false); }
  }

  async function createTopic(data: NewTopicInput) {
    const topic = await api.createTopic(data);
    const panel = await api.generatePanel(topic.id);
    setTopics((current) => [topic, ...current]);
    setActiveTopic(topic); setActivePanel(panel); setComposerOpen(false); setView("admission");
  }

  async function openTopic(preview: TopicPreview) {
    const topic = topics.find((item) => item.id === preview.id);
    if (!topic) return;
    setBusy(true); setPageError(null);
    try {
      let panel: PanelResource;
      try { panel = await api.getPanel(topic.id); }
      catch (reason) { if (reason instanceof ApiError && reason.status === 404) panel = await api.generatePanel(topic.id); else throw reason; }
      setActiveTopic(topic); setActivePanel(panel); setView("admission");
    } catch (reason) { setPageError(reason instanceof Error ? reason.message : "无法打开这个话题。"); }
    finally { setBusy(false); }
  }

  async function regeneratePanel() {
    if (!activeTopic) return;
    setBusy(true); setPageError(null);
    try { setActivePanel(await api.generatePanel(activeTopic.id)); }
    catch (reason) { setPageError(reason instanceof Error ? reason.message : "重新生成失败。"); }
    finally { setBusy(false); }
  }

  async function admitPanel() {
    if (!activeTopic || !activePanel) return;
    setBusy(true); setPageError(null);
    try {
      const admitted = await api.admitPanel(activeTopic.id, activePanel.generation);
      const session = await api.createSession(activeTopic.id);
      setActivePanel(admitted); setActiveSession(session); setLiveExperts([admitted.host, ...admitted.experts].map(toExpertPreview)); setLiveTranscript([]); setLiveBranches([]); setView("studio");
      await loadTopics();
    } catch (reason) { setPageError(reason instanceof Error ? reason.message : "确认阵容失败。"); }
    finally { setBusy(false); }
  }

  async function startDiscussion() {
    if (!activeSession) return;
    setBusy(true); setPageError(null); setStreamEnabled(true);
    try { setActiveSession(await api.startSession(activeSession.id)); }
    catch (reason) { setStreamEnabled(false); setPageError(reason instanceof Error ? reason.message : "启动讨论失败。"); }
    finally { setBusy(false); }
  }

  function leaveStudio() { setStreamEnabled(false); setView("home"); void loadTopics(); }

  if (view === "admission" && activeTopic && activePanel) {
    return <PanelAdmission topic={activeTopic} panel={activePanel} busy={busy} error={pageError} onBack={() => { setView("home"); setPageError(null); }} onRegenerate={() => void regeneratePanel()} onAdmit={() => void admitPanel()} />;
  }

  if (view === "studio" && activeTopic && activePanel && activeSession) {
    const running = activeSession.status === "running";
    const progress = Math.min(100, Math.round(activeSession.turnCount / activeSession.maxTurns * 100));
    return (
      <div className="studio-shell">
        <header className="topbar">
          <button className="brand-button" type="button" onClick={leaveStudio}><Brand /></button>
          <div className="topic-titlebar"><span>{running ? "讨论进行中" : activeSession.status === "completed" ? "讨论已结束" : "等待开场"} · {activeSession.status}</span><strong>{activeTopic.title}</strong></div>
          <div className="topbar-actions"><span className={`connection-pill connection-pill--${connectionState}`}><i /> {connectionLabel(connectionState)}</span>{activeSession.status === "admitted" && <button className="primary-button" type="button" disabled={busy} onClick={() => void startDiscussion()}>{busy ? "正在启动…" : "启动讨论"}</button>}</div>
        </header>
        {pageError && <div className="studio-error error-banner" role="alert">{pageError}</div>}
        <main className="studio-grid"><ExpertRail experts={liveExperts} /><TranscriptPanel experts={liveExperts} transcript={liveTranscript} isRunning={running} /><BranchPanel branches={liveBranches} /></main>
        <footer className="studio-footer"><span>ROUND {String(activeSession.turnCount).padStart(2, "0")} / {activeSession.maxTurns}</span><div className="round-progress"><i style={{ width: `${progress}%` }} /></div><span>{running ? "专家正在自主判断发言时机" : activeSession.status === "completed" ? "讨论完成" : "等待主持人开场"}</span></footer>
      </div>
    );
  }

  const previews = topics.map(toTopicPreview);
  return (
    <div className="home-shell">
      <header className="home-header"><Brand /><nav aria-label="主导航"><a href="#sessions">讨论现场</a><a href="#method">工作方式</a></nav><button className="primary-button" type="button" onClick={() => setComposerOpen(true)}><span aria-hidden="true">＋</span> 发起新讨论</button></header>
      <main>
        <section className="hero" aria-labelledby="hero-title"><div className="hero-copy"><span className="hero-badge"><i /> AI 圆桌演播厅 · 本地 MVP</span><h1 id="hero-title">别只要答案。<em>看见观点如何形成。</em></h1><p>邀请一组立场鲜明的虚拟专家，在主持人的追问中自主举手、补充与反驳。每一次分歧，都成为下一条知识路径。</p><div className="hero-actions"><button className="primary-button primary-button--large" type="button" onClick={() => setComposerOpen(true)}>召集一场圆桌 <span aria-hidden="true">→</span></button><a className="ghost-button" href="#sessions"><span className="play-icon" aria-hidden="true">↓</span> 查看讨论记录</a></div></div><div className="hero-orbit" aria-label="四位虚拟专家围绕议题协作的示意图"><div className="orbit-glow" /><div className="orbit-center"><span>LIVE</span><strong>观点正在<br />交汇</strong><small>4 EXPERTS</small></div>{heroExperts.slice(1).map((expert, index) => <div className={`orbit-person orbit-person--${index + 1}`} key={expert.id} style={{ "--expert-color": expert.color } as CSSProperties}><span>{expert.initials}</span><small>{expert.name}</small></div>)}<svg className="orbit-lines" viewBox="0 0 520 420" aria-hidden="true"><path d="M260 210 L105 90 M260 210 L415 90 M260 210 L105 330 M260 210 L415 330" /></svg></div></section>
        <section className="session-section" id="sessions" aria-labelledby="session-heading"><div className="section-heading-row"><div><span className="section-kicker">RECENT SESSIONS</span><h2 id="session-heading">继续你的讨论</h2></div><span className="session-total">{String(topics.length).padStart(2, "0")} 场记录</span></div>{pageError && <div className="error-banner" role="alert">{pageError} <button className="text-button" type="button" onClick={() => void loadTopics()}>重试</button></div>}{loading ? <div className="loading-state">正在读取讨论记录…</div> : <div className="topic-grid">{previews.map((topic) => <TopicCard key={topic.id} topic={topic} onOpen={(item) => void openTopic(item)} />)}<button className="new-topic-card" type="button" onClick={() => setComposerOpen(true)}><span aria-hidden="true">＋</span><strong>开启一个新议题</strong><small>{busy ? "正在准备…" : "输入主题，系统会召集不同视角的专家"}</small></button></div>}</section>
        <section className="method-strip" id="method" aria-label="产品工作方式"><span><b>01</b> 生成多元阵容</span><i>→</i><span><b>02</b> 自主观点交锋</span><i>→</i><span><b>03</b> 捕捉知识分岔</span><i>→</i><span><b>04</b> 沉淀决策摘要</span></section>
      </main>
      <footer className="home-footer"><span>AI PANEL STUDIO / 2026</span><span>让复杂问题拥有不止一个声音</span></footer>
      {composerOpen && <NewTopicPanel onClose={() => setComposerOpen(false)} onSubmit={createTopic} />}
    </div>
  );
}
