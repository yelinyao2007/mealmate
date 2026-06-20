"""
Nutrition Analyzer Agent - Analyzes the nutritional balance of meal plans.
Checks for deficiencies, provides improvement suggestions.
"""
import json
from typing import Any, Dict

from app.agents.base import BaseAgent, AgentResult


class NutritionAnalyzerAgent(BaseAgent):
    name = "NutritionAnalyzerAgent"
    description = "营养分析智能体 - 分析菜单营养均衡性，提出改进建议"

    SYSTEM_PROMPT = """你是一位专业的青年营养师，负责分析面向年轻人群体的菜单营养均衡性。

你需要：
1. 评估每日膳食的热量、蛋白质、脂肪、碳水化合物、维生素、矿物质等是否均衡
2. 检查是否满足中国居民膳食指南的推荐摄入量
3. 特别关注青年群体的营养需求（高蛋白、膳食纤维、维生素B族、优质脂肪）
4. 针对健身、素食、加班族等不同群体的特殊需求进行评估
5. 指出潜在的营养不足或过剩
6. 给出具体的改进建议

回复必须是有效的JSON格式：
{
  "overall_score": 85,
  "daily_analysis": {
    "周一": {
      "score": 88,
      "calories_estimate": "约1800kcal",
      "protein_adequate": true,
      "fiber_adequate": true,
      "issues": ["..."],
      "suggestions": ["..."]
    },
    ...
  },
  "weekly_summary": {
    "strengths": ["..."],
    "weaknesses": ["..."],
    "missing_nutrients": ["..."],
    "improvement_suggestions": ["..."]
  },
  "elderly_friendly_score": 82,
  "elderly_notes": "..."
}"""

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        menu_data = input_data.get("weekly_menu", {})
        target_population = input_data.get("target_population", "青年群体")

        menu_text = json.dumps(menu_data, ensure_ascii=False, indent=2)

        user_message = f"""请分析以下社区食堂一周菜单的营养均衡性：

{menu_text}

目标人群：{target_population}

请从热量、蛋白质、维生素、矿物质等多个维度进行全面分析，并给出评分和改进建议。"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        data = self._call_llm_json(messages, temperature=0.5)

        return AgentResult(
            agent_name=self.name,
            success=True,
            data=data,
        )
