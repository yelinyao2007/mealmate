"""
Meal Customizer Agent - Creates personalized meal plans for special populations.
Handles elderly, diabetic, children, and other dietary restriction needs.
NOW ALSO: considers user profile for disease-based and allergy-based customizations.
"""
import json
from typing import Any, Dict

from app.agents.base import BaseAgent, AgentResult


class MealCustomizerAgent(BaseAgent):
    name = "MealCustomizerAgent"
    description = "青年群体膳食定制Agent - 为不同目标群体及个人健康画像定制个性化餐食方案"

    SYSTEM_PROMPT = """你是面向青年群体的AI膳食定制专家。

你的任务是根据标准菜单，为不同需求的青年群体定制个性化的餐食方案。

定制原则：
1. 健身爱好者：高蛋白、复合碳水、优质脂肪、训练前后营养搭配
2. 素食主义者：植物蛋白替代、B12/铁/锌补充、豆类+谷物搭配
3. 加班族：快手餐 (<20min)、批量预制、高能量密度、护胃食材
4. 学生党：极致性价比、耐储存食材、一锅出快手菜、补脑食材
5. 美食博主：高颜值摆盘、色彩搭配、融合创意、社交媒体出片
6. 疾病特需：糖尿病患者控GI、高血压患者低钠、结合用户实际健康状况
7. 过敏源红线：严格排除用户过敏食材及其交叉污染风险

回复必须是有效的JSON格式：
{
  "customized_plans": [
    {
      "target_group": "健身爱好者",
      "modifications": "...",
      "daily_plans": {
        "周一": {
          "午餐": {
            "主食": "...",
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
  "safety_reminders": ["严格排除花生（过敏源）", "高血压患者餐食标注'限盐'标识"],
  "profile_based_recommendations": "基于用户个人画像的额外建议"
}"""

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        menu_data = input_data.get("weekly_menu", {})
        target_groups = input_data.get("target_groups", ["健身爱好者"])
        health_conditions = input_data.get("health_conditions", [])
        individual_preferences = input_data.get("individual_preferences", "")
        user_profile = input_data.get("user_profile", {})

        menu_text = json.dumps(menu_data, ensure_ascii=False, indent=2)

        groups_text = "、".join(target_groups)
        conditions_text = ""
        if health_conditions:
            conditions_text = f"\n需要注意的健康状况：{', '.join(health_conditions)}"

        prefs_text = ""
        if individual_preferences:
            prefs_text = f"\n个人偏好或禁忌：{individual_preferences}"

        profile_note = self._build_profile_note(user_profile)

        user_message = f"""请基于以下标准菜单，为不同青年群体定制个性化餐食方案：

标准菜单：
{menu_text}

目标人群：{groups_text}
{conditions_text}{prefs_text}

{profile_note}

请针对每个目标人群，说明需要哪些调整，并生成完整的定制餐食方案。同时根据用户画像给出个人层面的额外建议。"""

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

    def _build_profile_note(self, user_profile: Dict[str, Any]) -> str:
        if not user_profile:
            return ""

        parts = ["【该用户个人画像 — 定制时必须遵守】"]

        height = user_profile.get("height", 0)
        weight = user_profile.get("weight", 0)
        age = user_profile.get("age", 0)
        goal = user_profile.get("goal", "")
        target_calories = user_profile.get("target_calories", 0)
        health_conditions = user_profile.get("health_conditions", [])
        allergies = user_profile.get("allergies", [])
        dietary = user_profile.get("dietary", [])

        if height and weight:
            bmi = round(weight / ((height / 100) ** 2), 1)
            parts.append(f"身体数据：身高{height}cm，体重{weight}kg，年龄{age}岁，BMI {bmi}")

        goal_labels = {
            "lose_fat": "减脂",
            "gain_muscle": "增肌",
            "sugar_control": "控糖",
            "general": "一般健康",
        }
        if goal and goal in goal_labels:
            parts.append(f"个人健康目标：{goal_labels[goal]}（请在定制方案中体现）")

        if target_calories:
            parts.append(f"日目标热量：{target_calories}kcal")

        if health_conditions:
            parts.append(f"个人健康状况：{', '.join(health_conditions)}")
            for hc in health_conditions:
                if "diabetes" in hc or "糖尿病" in hc:
                    parts.append("【定制要求】所有定制餐食必须控糖：替换精制碳水为糙米/燕麦/荞麦，去除含糖调料，每餐碳水≤50g")
                if "hypertension" in hc or "高血压" in hc:
                    parts.append("【定制要求】所有定制餐食必须低钠：盐<3g/餐，用醋/柠檬/香草替代盐调味，去除腌制食品")

        if allergies:
            parts.append(f"【过敏源—绝对排除】{', '.join(allergies)}及其衍生物不能出现在任何定制方案中！")

        if dietary:
            parts.append(f"饮食偏好：{', '.join(dietary)}")

        return "\n".join(parts) + "\n"
