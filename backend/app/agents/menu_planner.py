"""
Menu Planner Agent - Generates weekly menus for community canteens.
Considers nutrition balance, budget constraints, seasonal ingredients, and dietary needs.
"""
import json
from typing import Any, Dict

from app.agents.base import BaseAgent, AgentResult


class MenuPlannerAgent(BaseAgent):
    name = "MenuPlannerAgent"
    description = "社区食堂周菜单智能规划 - 根据预算、营养、季节等因素自动生成一周菜单"

    SYSTEM_PROMPT = """你是"智膳大厨"——面向青年群体的AI菜单规划专家。
你的任务是为不同需求的年轻人生成科学合理的一周菜单。

你必须遵守以下规则：
1. 营养均衡：每日膳食须包含主食、蛋白质、蔬菜、水果的合理搭配
2. 成本控制：严格控制在每人每餐的预算范围内
3. 季节食材：优先使用当季新鲜食材
4. 品种多样：一周内菜品不重复，兼顾不同口味
5. 面向青年：考虑健身/素食/加班/学生/美食博主等不同群体的需求
6. 快手健康：优先推荐快手、健康的菜品

回复必须是有效的JSON格式，结构如下：
{
  "weekly_menu": {
    "周一": {
      "午餐": {
        "主食": ["..."],
        "荤菜": ["..."],
        "素菜": ["..."],
        "汤品": "...",
        "estimated_cost_per_person": 15.0
      },
      "晚餐": { ... }
    },
    "周二": { ... },
    ...
  },
  "total_weekly_cost_per_person": 210.0,
  "nutrition_summary": "...",
  "seasonal_highlights": ["..."],
  "special_notes": "..."
}"""

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        budget_per_meal = input_data.get("budget_per_meal", 15)
        num_people = input_data.get("num_people", 100)
        dietary_requirements = input_data.get("dietary_requirements", [])
        season = input_data.get("season", "春季")
        available_ingredients = input_data.get("available_ingredients", [])
        special_requirements = input_data.get("special_requirements", "")

        constraints = []
        constraints.append(f"每人每餐预算: {budget_per_meal}元")
        constraints.append(f"用餐人数: {num_people}人")
        constraints.append(f"当前季节: {season}")
        if dietary_requirements:
            constraints.append(f"特殊饮食需求: {', '.join(dietary_requirements)}")
        if available_ingredients:
            constraints.append(f"已有食材: {', '.join(available_ingredients)}")
        if special_requirements:
            constraints.append(f"其他要求: {special_requirements}")

        user_message = f"""请为青年人群生成一周菜单（周一至周五，午餐和晚餐）。

约束条件：
{chr(10).join('- ' + c for c in constraints)}

请确保菜品丰富多样、营养均衡、快手健康，适合年轻白领、健身人士、学生等青年群体。"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        data = self._call_llm_json(messages, temperature=0.8)

        return AgentResult(
            agent_name=self.name,
            success=True,
            data=data,
        )
