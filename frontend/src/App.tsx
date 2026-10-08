import { useEffect, useState } from "react";
import type { CSSProperties } from "react";

import { BranchPanel } from "./components/BranchPanel";
import { Brand } from "./components/Brand";
import { ExpertRail } from "./components/ExpertRail";
import { NewTopicPanel } from "./components/NewTopicPanel";
import { TopicCard } from "./components/TopicCard";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { branches, experts, topics, transcript } from "./mockData";
import type { TopicPreview } from "./types";

type View = "home" | "studio";

export default function App() {
  const [view, setView] = useState<View>("home");
  const [composerOpen, setComposerOpen] = useState(false);
  const [activeTopic, setActiveTopic] = useState<TopicPreview>(topics[0]);

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setComposerOpen(false);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  function openTopic(topic: TopicPreview) {
    setActiveTopic(topic);
    setView("studio");
  }

  if (view === "studio") {
    return (
      <div className="studio-shell">
        <header className="topbar">
          <button className="brand-button" type="button" onClick={() => setView("home")}><Brand /></button>
          <div className="topic-titlebar"><span>正在讨论</span><strong>{activeTopic.title}</strong></div>
          <div className="topbar-actions">
            <span className="connection-pill"><i /> 实时同步</span>
            <button className="secondary-button" type="button">暂停讨论</button>
            <button className="danger-button" type="button">结束并总结</button>
          </div>
        </header>
        <main className="studio-grid">
          <ExpertRail experts={experts} />
          <TranscriptPanel experts={experts} transcript={transcript} />
          <BranchPanel branches={branches} />
        </main>
        <footer className="studio-footer"><span>ROUND 06 / 18</span><div className="round-progress"><i /></div><span>已讨论 08:42</span></footer>
      </div>
    );
  }

  return (
    <div className="home-shell">
      <header className="home-header">
        <Brand />
        <nav aria-label="主导航"><a href="#sessions">讨论现场</a><a href="#method">工作方式</a></nav>
        <button className="primary-button" type="button" onClick={() => setComposerOpen(true)}><span aria-hidden="true">＋</span> 发起新讨论</button>
      </header>
      <main>
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy">
            <span className="hero-badge"><i /> AI 圆桌演播厅 · 本地 MVP</span>
            <h1 id="hero-title">别只要答案。<em>看见观点如何形成。</em></h1>
            <p>邀请一组立场鲜明的虚拟专家，在主持人的追问中自主举手、补充与反驳。每一次分歧，都成为下一条知识路径。</p>
            <div className="hero-actions">
              <button className="primary-button primary-button--large" type="button" onClick={() => setComposerOpen(true)}>召集一场圆桌 <span aria-hidden="true">→</span></button>
              <button className="ghost-button" type="button" onClick={() => openTopic(topics[0])}><span className="play-icon" aria-hidden="true">▶</span> 查看演播厅示例</button>
            </div>
          </div>
          <div className="hero-orbit" aria-label="四位虚拟专家围绕议题协作的示意图">
            <div className="orbit-glow" />
            <div className="orbit-center"><span>LIVE</span><strong>观点正在<br />交汇</strong><small>4 EXPERTS</small></div>
            {experts.slice(1).map((expert, index) => (
              <div className={`orbit-person orbit-person--${index + 1}`} key={expert.id} style={{ "--expert-color": expert.color } as CSSProperties}>
                <span>{expert.initials}</span><small>{expert.name}</small>
              </div>
            ))}
            <svg className="orbit-lines" viewBox="0 0 520 420" aria-hidden="true"><path d="M260 210 L105 90 M260 210 L415 90 M260 210 L105 330 M260 210 L415 330" /></svg>
          </div>
        </section>

        <section className="session-section" id="sessions" aria-labelledby="session-heading">
          <div className="section-heading-row"><div><span className="section-kicker">RECENT SESSIONS</span><h2 id="session-heading">继续你的讨论</h2></div><span className="session-total">03 场记录</span></div>
          <div className="topic-grid">
            {topics.map((topic) => <TopicCard key={topic.id} topic={topic} onOpen={openTopic} />)}
            <button className="new-topic-card" type="button" onClick={() => setComposerOpen(true)}><span aria-hidden="true">＋</span><strong>开启一个新议题</strong><small>输入主题，系统会召集不同视角的专家</small></button>
          </div>
        </section>

        <section className="method-strip" id="method" aria-label="产品工作方式">
          <span><b>01</b> 生成多元阵容</span><i>→</i><span><b>02</b> 自主观点交锋</span><i>→</i><span><b>03</b> 捕捉知识分岔</span><i>→</i><span><b>04</b> 沉淀决策摘要</span>
        </section>
      </main>
      <footer className="home-footer"><span>AI PANEL STUDIO / 2026</span><span>让复杂问题拥有不止一个声音</span></footer>
      {composerOpen && <NewTopicPanel onClose={() => setComposerOpen(false)} onPreview={() => { setComposerOpen(false); openTopic(topics[0]); }} />}
    </div>
  );
}
