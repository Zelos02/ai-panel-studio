import type { BranchPreview, ExpertPreview, TopicPreview, TranscriptPreview } from "./types";

export const topics: TopicPreview[] = [
  {
    id: "topic-ai-hiring",
    title: "AI 是否应该参与招聘终审？",
    background: "效率、公平性与责任边界的正面交锋",
    status: "running",
    expertCount: 4,
    updatedAt: "刚刚更新",
    progress: 62,
    accent: "#69e4ce",
  },
  {
    id: "topic-education",
    title: "大学课堂还需要闭卷考试吗？",
    background: "当知识随手可得，评估究竟应该测什么",
    status: "ready",
    expertCount: 5,
    updatedAt: "18 分钟前",
    progress: 18,
    accent: "#f6c177",
  },
  {
    id: "topic-open-source",
    title: "开源模型会重塑软件商业模式吗？",
    background: "从开发者生态到企业护城河",
    status: "completed",
    expertCount: 4,
    updatedAt: "昨天 21:40",
    progress: 100,
    accent: "#8da8ff",
  },
];

export const experts: ExpertPreview[] = [
  {
    id: "host",
    name: "周岚",
    title: "科技记者 · 主持人",
    stance: "保持中立，持续检验论据",
    color: "#69e4ce",
    initials: "周",
    state: "waiting",
    publicFocus: "正在梳理争议双方对“公平”的定义",
    kind: "host",
  },
  {
    id: "lin-che",
    name: "林澈",
    title: "组织心理学研究员",
    stance: "反对把最终决定完全自动化",
    color: "#b49cff",
    initials: "林",
    state: "speaking",
    publicFocus: "关注历史数据如何复制组织偏见",
  },
  {
    id: "xu-ke",
    name: "许珂",
    title: "HR 科技产品负责人",
    stance: "支持人在回路中的辅助决策",
    color: "#f6c177",
    initials: "许",
    state: "preparing",
    publicFocus: "准备回应效率和可解释性的权衡",
  },
  {
    id: "chen-yi",
    name: "陈弈",
    title: "算法审计律师",
    stance: "主张先建立责任和申诉机制",
    color: "#ff8b9c",
    initials: "陈",
    state: "waiting",
    publicFocus: "追踪错误决定最终由谁承担责任",
  },
  {
    id: "qiao-an",
    name: "乔安",
    title: "人才战略顾问",
    stance: "强调业务场景和岗位差异",
    color: "#67b7ff",
    initials: "乔",
    state: "waiting",
    publicFocus: "比较高频招聘与关键岗位的不同风险",
  },
];

export const transcript: TranscriptPreview[] = [
  {
    id: "m1",
    speakerId: "host",
    time: "10:02",
    content: "今天我们不讨论 AI 能不能筛简历，而是把问题推到最后一步：它是否应该参与录用终审？请先界定你们最担心失去的东西。",
  },
  {
    id: "m2",
    speakerId: "xu-ke",
    time: "10:03",
    content: "我最担心企业因为害怕风险而放弃一致的评估标准。AI 不该替人签字，但可以让每位候选人面对同一套证据要求。",
  },
  {
    id: "m3",
    speakerId: "chen-yi",
    time: "10:04",
    content: "一致不等于公平，因为同一标准也可能系统性排除某些群体。只要候选人无法知道决定依据，所谓一致性就难以被问责。",
  },
  {
    id: "m4",
    speakerId: "qiao-an",
    time: "10:05",
    content: "我会区分批量岗位和关键岗位：前者需要稳定，后者常常需要识别履历之外的潜力。把两者放进同一条自动化流水线，本身就是错误的问题定义。",
  },
  {
    id: "m5",
    speakerId: "lin-che",
    time: "10:06",
    content: "历史数据记录的不是纯粹能力，而是过去组织偏好过谁。效率提升不应掩盖偏差放大的风险，企业首先要证明评估标准本身可信。",
  },
];

export const branches: BranchPreview[] = [
  {
    id: "b1",
    type: "conflict",
    title: "一致性是否等于公平",
    summary: "统一标准可能减少随意性，也可能稳定地复制同一种偏差。",
    sourceMessageId: "m3",
  },
  {
    id: "b2",
    type: "assumption",
    title: "历史绩效可以代表能力",
    summary: "模型训练数据是否包含组织选择偏好，而不只是员工真实表现？",
    sourceMessageId: "m5",
  },
  {
    id: "b3",
    type: "direction",
    title: "按岗位风险分级",
    summary: "自动化权限可以随岗位规模、可逆性和潜在损害动态变化。",
    sourceMessageId: "m4",
  },
];
