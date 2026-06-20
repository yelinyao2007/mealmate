"""
Meal Customizer Agent - Creates personalized meal plans for special populations.
Handles elderly, diabetic, children, and other dietary restriction needs.
"""
import json
from typing import Any, Dict

from app.agents.base import BaseAgent, AgentResult


class MealCustomizerAgent(BaseAgent):
    name = "MealCustomizerAgent"
    description = "青年群体膳食定制Agent - 为健身、素食、加班族、学生、美食博主等定制个性化餐食方案"

    SYSTEM_PROMPT = """你是面向青年群体的AI膳食定制专家。

你的任务是根据标准菜单，为不同需求的青年群体定制个性化的餐食方案。

定制原则：
1. 健身爱好者：高蛋白、复合碳水、优质脂肪、训练前后营养搭配
2. 素食主义者：植物蛋白替代、B12/铁/锌补充、豆类+谷物搭配
3. 加班族：快手餐 (<20min)、批量预制、高能量密度、护胃食材
4. 学生党：极致性价比、耐储存食材、一锅出快手菜、补脑食材
5. 美食博主：高颜值摆盘、色彩搭配、融合创意、社交媒体出片

回复必须是有效的JSON格式：
{
  "customized_plans": [
    {
      "target_group": "健身爱好者",
      "modifications": "...",
      "daily_plans": {
        "周一": {
          "午餐": {
            "主食": "软烂米饭",
            "菜品": ["..."],
            "注意事项": "..."
          },
          "晚餐": { ... }
        },
        ...
      },
      "nutrition_notes": "...",
      "preparation_tips": "..."
    }
  ],
  "delivery_suggestions": "...",
  "safety_reminders": ["..."]
}"""

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        menu_data = input_data.get("weekly_menu", {})
        target_groups = input_data.get("target_groups", ["健身爱好者"])
        health_conditions = input_data.get("health_conditions", [])
        individual_preferences = input_data.get("individual_preferences", "")

        menu_text = json.dumps(menu_data, ensure_ascii=False, indent=2)

        groups_text = "、".join(target_groups)
        conditions_text = ""
        if health_conditions:
            conditions_text = f"\n需要注意的健康状况：{', '.join(health_conditions)}"

        prefs_text = ""
        if individual_preferences:
            prefs_text = f"\n个人偏好或禁忌：{individual_preferences}"

        user_message = f"""请基于以下标准菜单，为不同青年群体定制个性化餐食方案：

标准菜单：
{menu_text}

目标人群：{groups_text}
{conditions_text}{prefs_text}

请针对每个目标人群，说明需要哪些调整，并生成完整的定制餐食方案。"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        data = self._call_llm_json(messages, temperature=0.6)

        return AgentResult(
            agent_name=self.name,
            success=True,
            data=data,
        )
