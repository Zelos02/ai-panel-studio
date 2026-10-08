import hashlib
from typing import Any


class FakeLLMProvider:
    """Deterministic provider used by local development and automated tests."""

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
    ) -> dict[str, Any]:
        digest = hashlib.sha256(
            f"{schema_name}\n{system_prompt}\n{user_prompt}".encode("utf-8")
        ).hexdigest()[:12]
        if schema_name == "PanelGenerationResult":
            colors = ["#B49CFF", "#F6C177", "#FF8B9C", "#67B7FF", "#74D99F", "#F0A6CA", "#8EC5FC", "#F9D976"]
            people = [
                ("林澈", "组织心理学研究员", "反对把最终决定完全自动化", "关注公平性、偏差与候选人体验"),
                ("许珂", "HR 科技产品负责人", "支持人在回路中的辅助决策", "关注流程效率、证据一致性与落地成本"),
                ("陈弈", "算法审计律师", "主张先建立责任和申诉机制", "关注合规、解释权与责任归属"),
                ("乔安", "人才战略顾问", "强调岗位差异和业务场景", "关注组织能力、岗位风险与人才潜力"),
                ("唐宁", "数据治理负责人", "要求数据来源可审计", "关注数据质量、漂移与治理边界"),
                ("顾遥", "劳动经济学者", "从劳动力市场结构审视影响", "关注机会分配与长期激励"),
                ("苏禾", "候选人体验设计师", "主张把尊严和反馈纳入指标", "关注沟通透明度与申诉体验"),
                ("沈括", "企业风险负责人", "支持按风险分级采用自动化", "关注可逆性、损害半径与控制措施"),
            ]
            try:
                count = max(2, min(8, int(user_prompt.rsplit("专家人数：", 1)[1].splitlines()[0])))
            except (IndexError, ValueError):
                count = 4
            return {
                "host": {
                    "name": "周岚",
                    "title": "科技与社会议题主持人",
                    "stance": "保持中立并持续检验论据",
                    "publicProfile": "擅长澄清定义、追问证据并推动分歧收敛",
                    "color": "#69E4CE",
                },
                "experts": [
                    {
                        "name": name,
                        "title": title,
                        "stance": stance,
                        "publicProfile": profile,
                        "color": colors[index],
                    }
                    for index, (name, title, stance, profile) in enumerate(people[:count])
                ],
            }
        return {"schema": schema_name, "fixtureId": digest}
