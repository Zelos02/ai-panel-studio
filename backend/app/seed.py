from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings
from .database import create_database, init_database
from .domain import ExpertKind, TopicStatus
from .models import Expert, Topic


SEED_TOPICS = [
    {
        "title": "AI 是否应该参与招聘终审？",
        "background": "企业希望提高招聘效率，但候选人担心算法偏差和申诉困难。",
        "goal": "明确 AI 在高风险招聘决定中的权限、审计和责任边界。",
        "host": ("周岚", "科技与社会议题主持人", "保持中立并检验论据", "关注定义、证据与责任归属"),
        "experts": [
            ("林澈", "组织心理学研究员", "反对把最终决定完全自动化", "关注公平性、偏差与候选人体验"),
            ("许珂", "HR 科技产品负责人", "支持人在回路中的辅助决策", "关注流程效率和证据一致性"),
            ("陈弈", "算法审计律师", "主张先建立责任和申诉机制", "关注合规、解释权与责任归属"),
            ("乔安", "人才战略顾问", "强调岗位差异和业务场景", "关注关键岗位的潜力识别"),
        ],
    },
    {
        "title": "大学课堂还需要闭卷考试吗？",
        "background": "生成式 AI 和随时可得的知识正在改变学习与考核方式。",
        "goal": "设计既能验证理解、又不过度奖励记忆的评估组合。",
        "host": ("顾言", "教育议题主持人", "追问评估究竟服务于什么", "关注学习目标与评价方法的一致性"),
        "experts": [
            ("苏禾", "认知科学教授", "保留少量闭卷以观察知识内化", "关注提取练习和长期记忆"),
            ("陆川", "高校教务负责人", "主张按学科分层改革", "关注公平、成本和大规模执行"),
            ("沈星", "大学生学习倡导者", "反对高权重一次性闭卷", "关注焦虑、机会与反馈质量"),
            ("唐宁", "AI 教育产品设计师", "支持开放工具的过程性考核", "关注真实任务和 AI 素养"),
        ],
    },
    {
        "title": "开源模型会重塑软件商业模式吗？",
        "background": "基础模型能力扩散，企业需要重新判断产品差异化和护城河。",
        "goal": "识别开源生态中可持续的价值捕获方式。",
        "host": ("宋简", "科技商业记者", "要求区分技术扩散和商业结果", "关注价值链与长期激励"),
        "experts": [
            ("季航", "开源社区维护者", "相信开放协作会加速能力普及", "关注社区治理和贡献激励"),
            ("叶岑", "企业软件创始人", "护城河将转向工作流与服务", "关注客户迁移成本和交付能力"),
            ("袁启", "风险投资人", "商业价值仍会向规模平台集中", "关注资本效率和分发渠道"),
            ("莫然", "云基础设施架构师", "成本与可运维性决定最终选择", "关注算力、延迟和可靠性"),
        ],
    },
    {
        "title": "核心城区是否应该大幅限制私家车？",
        "background": "拥堵、空气质量、商业活力和出行公平之间长期冲突。",
        "goal": "形成包含过渡期、替代交通和弱势群体保障的政策框架。",
        "host": ("宁川", "城市公共议题主持人", "检验政策的受益者与成本承担者", "关注指标、配套和执行时序"),
        "experts": [
            ("罗霁", "城市交通规划师", "支持拥堵收费与路权重分配", "关注道路容量和公共交通效率"),
            ("何遥", "无障碍出行倡导者", "反对忽略特殊出行需求的一刀切", "关注老年人、残障者和照护者"),
            ("梁知", "中心城区商户代表", "担心限制政策影响小商业客流", "关注配送、消费和过渡成本"),
            ("顾青", "环境经济学者", "主张把外部成本显性计价", "关注空气质量、噪声和公平补偿"),
        ],
    },
    {
        "title": "AI 生成内容是否必须强制标识？",
        "background": "合成内容快速增长，透明度要求可能与创作自由、执行成本冲突。",
        "goal": "确定标识范围、责任主体和对低风险创作的合理豁免。",
        "host": ("叶澜", "数字治理主持人", "推动风险分级而非口号对立", "关注可执行性与误伤"),
        "experts": [
            ("温宁", "平台内容治理负责人", "支持机器可读与用户可见双重标识", "关注规模治理和检测误差"),
            ("傅声", "独立视觉创作者", "反对给所有辅助创作统一贴标签", "关注表达自由和创作者负担"),
            ("孟夏", "媒体真实性研究员", "高传播风险内容必须强制披露", "关注公共事件和证据链"),
            ("程野", "数字权利律师", "要求义务与潜在损害成比例", "关注责任主体、申诉和跨平台标准"),
        ],
    },
]

COLORS = ["#B49CFF", "#F6C177", "#FF8B9C", "#67B7FF"]


def seed_database(factory: sessionmaker[Session]) -> int:
    created = 0
    with factory() as db:
        for data in SEED_TOPICS:
            exists = db.scalar(select(Topic.id).where(Topic.title == data["title"]))
            if exists is not None:
                continue
            topic = Topic(
                title=data["title"],
                background=data["background"],
                goal=data["goal"],
                requested_expert_count=4,
                panel_generation=1,
                status=TopicStatus.READY.value,
            )
            db.add(topic)
            db.flush()
            host = data["host"]
            db.add(
                Expert(
                    topic_id=topic.id,
                    kind=ExpertKind.HOST.value,
                    name=host[0], title=host[1], stance=host[2], public_profile=host[3],
                    color="#69E4CE", display_order=0, admitted=True,
                )
            )
            for index, expert in enumerate(data["experts"], start=1):
                db.add(
                    Expert(
                        topic_id=topic.id,
                        kind=ExpertKind.EXPERT.value,
                        name=expert[0], title=expert[1], stance=expert[2], public_profile=expert[3],
                        color=COLORS[index - 1], display_order=index, admitted=True,
                    )
                )
            created += 1
        db.commit()
    return created


def main() -> None:
    settings = get_settings()
    engine, factory = create_database(settings.database_url)
    init_database(engine)
    created = seed_database(factory)
    engine.dispose()
    print(f"Seed complete: {created} topic(s) created, {len(SEED_TOPICS) - created} skipped.")


if __name__ == "__main__":
    main()
