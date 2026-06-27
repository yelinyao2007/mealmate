"""
Menu Planner Agent - Generates weekly menus for community canteens.
Considers nutrition balance, budget constraints, seasonal ingredients, dietary needs.
NOW ALSO: personalizes menu based on user profile (goal, allergies, health conditions).
"""
import json
from typing import Any, Dict

from app.agents.base import BaseAgent, AgentResult


class MenuPlannerAgent(BaseAgent):
    name = "MenuPlannerAgent"
    description = "社区食堂周菜单智能规划 - 根据预算、营养、季节及用户画像一键生成个性化周菜单"

    SYSTEM_PROMPT = """你是"智膳大厨"——面向青年群体的AI菜单规划专家。
你的任务是为不同需求的年轻人生成科学合理的一周菜单。

你必须遵守以下规则：
1. 营养均衡：每日膳食须包含主食、蛋白质、蔬菜、水果的合理搭配
2. 成本控制：严格控制在每人每餐的预算范围内
3. 季节食材：优先使用当季新鲜食材
4. 品种多样：一周内菜品不重复，兼顾不同口味
5. 个性化：根据用户画像（健康目标/疾病/过敏源）调整菜单，严格避开禁忌食材
6. 快手健康：优先推荐快手、健康的菜品
7. 食品安全红线：绝不推荐含有用户过敏源或与疾病冲突的菜品

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
    ...
  },
  "total_weekly_cost_per_person": 210.0,
  "nutrition_summary": "...",
  "seasonal_highlights": ["..."],
  "special_notes": "...",
  "profile_adaptations": "针对用户画像做的菜单调整说明"
}"""

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        budget_per_meal = input_data.get("budget_per_meal", 15)
        num_people = input_data.get("num_people", 100)
        dietary_requirements = input_data.get("dietary_requirements", [])
        season = input_data.get("season", "春季")
        available_ingredients = input_data.get("available_ingredients", [])
        special_requirements = input_data.get("special_requirements", "")
        user_profile = input_data.get("user_profile", {})

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

        profile_note = self._build_profile_note(user_profile)

        user_message = f"""请为青年人群生成一周菜单（周一至周五，午餐和晚餐）。

约束条件：
{chr(10).join('- ' + c for c in constraints)}

{profile_note}

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

    def _build_profile_note(self, user_profile: Dict[str, Any]) -> str:
        if not user_profile:
            return ""

        parts = ["【用户画像约束 — 必须遵守】"]

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
            parts.append(f"健康目标：{goal_labels[goal]}")

        if target_calories:
            parts.append(f"每餐目标热量约{target_calories // 3}kcal（全日{target_calories}kcal）")
            if goal == "lose_fat":
                parts.append("菜单原则：低热量高蛋白，每餐蛋白质不低于25g，控制碳水，多蔬菜少油，避免油炸和肥肉")
            elif goal == "gain_muscle":
                parts.append("菜单原则：高热量高蛋白，每餐蛋白质不低于35g，搭配复合碳水（全麦/糙米/燕麦），优质脂肪（坚果/牛油果）")
            elif goal == "sugar_control":
                parts.append("菜单原则：低GI食材为主，碳水每餐控制在40-50g，选用糙米/荞麦/燕麦/全麦替代精制主食，避免含糖调味")

        if health_conditions:
            for hc in health_conditions:
                if "diabetes" in hc or "糖尿病" in hc:
                    parts.append("【禁忌】禁止安排高GI食材（白米/白面/白糖/甜点/含糖饮料），主食必须为低GI粗粮")
                if "hypertension" in hc or "高血压" in hc:
                    parts.append("【禁忌】禁止安排高钠菜品（腌制食品/加工肉类/咸鱼腊肉/腐乳），每日盐<5g，优先安排高钾蔬菜（芹菜/菠菜/西兰花）")

        if allergies:
            parts.append(f"【禁忌—过敏源红线】以下食材及其衍生物绝对不得出现在任何菜品中：{', '.join(allergies)}")

        if dietary:
            for d in dietary:
                if "vegetarian" in d.lower() or "素食" in d:
                    parts.append("【饮食偏好】全菜单素食，用豆制品/菌菇/坚果替代肉类")
                elif "vegan" in d.lower():
                    parts.append("【饮食偏好】严格素食，排除所有动物性食品（肉/蛋/奶/蜂蜜）")

        if goal == "gain_muscle":
            parts.append("【加分项】每天至少安排2道高蛋白菜品（鸡胸肉/牛肉/鱼虾/豆腐/鸡蛋），训练后加蛋白补充窗口")

        return "\n".join(parts) + "\n"
