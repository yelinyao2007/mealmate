"""
Nutrition Analyzer Agent - Analyzes the nutritional balance of meal plans.
Checks for deficiencies, provides improvement suggestions.
NOW ALSO: evaluates menu against user-specific health profile.
"""
import json
from typing import Any, Dict

from app.agents.base import BaseAgent, AgentResult


class NutritionAnalyzerAgent(BaseAgent):
    name = "NutritionAnalyzerAgent"
    description = "营养分析智能体 - 分析菜单营养均衡性，并根据用户画像提出个性化改进建议"

    SYSTEM_PROMPT = """你是一位专业的青年营养师，负责分析面向年轻人群体的菜单营养均衡性。

你需要：
1. 评估每日膳食的热量、蛋白质、脂肪、碳水化合物、维生素、矿物质等是否均衡
2. 检查是否满足中国居民膳食指南的推荐摄入量
3. 针对用户的个人健康目标（减脂/增肌/控糖）评估菜单匹配度
4. 根据用户健康状况（糖尿病/高血压）识别潜在风险菜品
5. 指出潜在的营养不足或过剩
6. 给出具体的改进建议

回复必须是有效的JSON格式：
{
  "overall_score": 85,
  "profile_fit_score": 80,
  "daily_analysis": {
    "周一": {
      "score": 88,
      "calories_estimate": "约1800kcal",
      "protein_adequate": true,
      "fiber_adequate": true,
      "protein_grams_estimate": 90,
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
  "profile_warnings": ["减脂期建议减少油炸类菜品", "高血压患者需注意XXX菜品含盐量偏高"]
}"""

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        menu_data = input_data.get("weekly_menu", {})
        target_population = input_data.get("target_population", "青年群体")
        user_profile = input_data.get("user_profile", {})

        menu_text = json.dumps(menu_data, ensure_ascii=False)

        profile_note = self._build_profile_note(user_profile)

        profile_note = self._build_profile_note(user_profile)

        user_message = f"""请分析以下社区食堂一周菜单的营养均衡性：

{menu_text}

目标人群：{target_population}

{profile_note}

请从热量、蛋白质、维生素、矿物质等多个维度进行全面分析，并根据用户画像评估菜单匹配度，给出评分和改进建议。"""

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

    def _build_profile_note(self, user_profile: Dict[str, Any]) -> str:
        if not user_profile:
            return ""

        parts = ["【用户画像 — 营养分析参照标准】"]

        height = user_profile.get("height", 0)
        weight = user_profile.get("weight", 0)
        goal = user_profile.get("goal", "")
        target_calories = user_profile.get("target_calories", 0)
        health_conditions = user_profile.get("health_conditions", [])
        allergies = user_profile.get("allergies", [])

        if height and weight:
            bmi = round(weight / ((height / 100) ** 2), 1)
            parts.append(f"用户BMI: {bmi}")

        goal_labels = {
            "lose_fat": "减脂",
            "gain_muscle": "增肌",
            "sugar_control": "控糖",
            "general": "一般健康",
        }
        if goal and goal in goal_labels:
            parts.append(f"健康目标: {goal_labels[goal]}")
            if goal == "lose_fat":
                parts.append("评估标准：每餐热量应偏低于维持量，蛋白质充足(≥25g/餐)，脂肪<20g/餐，高纤维")
            elif goal == "gain_muscle":
                parts.append("评估标准：每餐蛋白质应≥35g，热量充足，碳水为复合碳水")
            elif goal == "sugar_control":
                parts.append("评估标准：每餐碳水≤50g，优先低GI食材，避免血糖剧烈波动")

        if target_calories:
            parts.append(f"全日目标热量: {target_calories}kcal，每餐约{target_calories // 3}kcal")

        if health_conditions:
            for hc in health_conditions:
                if "diabetes" in hc or "糖尿病" in hc:
                    parts.append("注意：用户为糖尿病患者，高GI/高碳水菜品需标注风险")
                if "hypertension" in hc or "高血压" in hc:
                    parts.append("注意：用户为高血压患者，高钠菜品需标注风险，建议减盐替代方案")

        if allergies:
            parts.append(f"过敏源：{', '.join(allergies)} — 含过敏源的菜品需标注警告")

        return "\n".join(parts) + "\n"
