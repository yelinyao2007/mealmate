"""
Procurement Agent - Generates optimized procurement lists from meal plans.
Consolidates ingredients, estimates quantities and costs.
NOW ALSO: avoids allergens, filters disease-restricted ingredients, adjusts quantities by user goal.
"""
import json
from typing import Any, Dict

from app.agents.base import BaseAgent, AgentResult


class ProcurementAgent(BaseAgent):
    name = "ProcurementAgent"
    description = "采购清单智能体 - 从菜单自动生成优化采购清单，控制成本减少浪费，严格避开过敏源与疾病禁忌食材"

    SYSTEM_PROMPT = """你是社区食堂的AI采购专家，负责根据一周菜单生成采购清单。

你需要：
1. 将菜单中所有菜品的食材进行汇总合并
2. 根据用餐人数及用户健康目标计算合理的采购量（增肌加量，减脂控量）
3. 严格避开用户的过敏源食材（食品安全红线）
4. 严格避开与用户疾病冲突的食材（如糖尿病患者避开高GI主食、高血压患者避开高钠食材）
5. 估算每种食材的采购价格（参考上海市场批发价）
6. 按食材类别分类（肉类、蔬菜、调料等）
7. 标注保质期短需优先使用的食材
8. 计算总采购预算

回复必须是有效的JSON格式：
{
  "procurement_list": {
    "肉类": [
      {"name": "猪瘦肉", "quantity": "25kg", "unit_price": 28.0, "total_price": 700.0, "shelf_life_days": 3, "priority": "high"}
    ],
    "蔬菜": [...],
    "主食/粮油": [...],
    "调味料": [...],
    "豆制品/蛋类": [...],
    "其他": [...]
  },
  "excluded_ingredients": [{"ingredient": "花生", "reason": "用户过敏"}],
  "goal_adjustments": "因用户目标为增肌，蛋白质食材采购量上浮20%...",
  "total_budget": 12500.0,
  "budget_per_person_per_day": 25.0,
  "perishable_items": ["..."],
  "storage_notes": "...",
  "suggested_suppliers": "建议联系社区定点供应商，优先采购本地时令蔬菜",
  "waste_reduction_tips": ["..."],
  "safety_warnings": ["严格排除花生（过敏源）", "高血压患者需用低钠酱油替代普通酱油"]
}"""

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        menu_data = input_data.get("weekly_menu", {})
        num_people = input_data.get("num_people", 100)
        existing_inventory = input_data.get("existing_inventory", [])
        user_profile = input_data.get("user_profile", {})

        menu_text = json.dumps(menu_data, ensure_ascii=False, indent=2)

        inventory_note = ""
        if existing_inventory:
            inventory_note = f"\n已有库存食材（无需重复采购）：{', '.join(existing_inventory)}"

        profile_note = self._build_profile_note(user_profile)

        user_message = f"""请根据以下一周菜单生成采购清单：

{menu_text}

用餐人数：{num_people}人/餐
{inventory_note}
{profile_note}

请计算所需食材总量，估算采购成本，并按类别整理。务必排除禁忌食材并在结果中说明原因。"""

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

        parts = ["\n【用户画像 — 采购决策依据】"]

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
            parts.append(f"身体数据：身高{height}cm，体重{weight}kg，BMI {bmi}")

        if age:
            parts.append(f"年龄：{age}岁")

        goal_labels = {
            "lose_fat": "减脂",
            "gain_muscle": "增肌",
            "sugar_control": "控糖",
            "general": "一般健康",
        }
        if goal:
            goal_name = goal_labels.get(goal, goal)
            parts.append(f"健康目标：{goal_name}")

            if goal == "gain_muscle":
                parts.append("【采购调整】蛋白质食材（肉类/鱼虾/豆制品/蛋类）采购量上浮15-20%，优先采购鸡胸肉、牛肉、鱼虾、鸡蛋、豆腐等高蛋白食材")
            elif goal == "lose_fat":
                parts.append("【采购调整】油脂类食材采购量下浮15%，增加高纤维蔬菜比例，优先采购鸡胸肉、鱼虾等低脂高蛋白食材")
            elif goal == "sugar_control":
                parts.append("【采购调整】精制碳水（白米/白面/白糖）采购量下浮30%，替代为糙米/燕麦/荞麦等低GI主食，增加高纤维蔬菜")

        if target_calories:
            parts.append(f"每日目标热量：{target_calories}kcal")

        if health_conditions:
            parts.append(f"健康状况：{', '.join(health_conditions)}")
            for hc in health_conditions:
                if "diabetes" in hc or "糖尿病" in hc:
                    parts.append("【疾病禁忌—控糖】避开高GI食材：白米/白面/白糖/含糖调味料，替代为糙米/荞麦/燕麦；避开蜜饯/甜点/含糖饮料原料")
                if "hypertension" in hc or "高血压" in hc:
                    parts.append("【疾病禁忌—高血压】避开高钠食材：腌制食品/加工肉类/咸鱼/腊肉/腐乳；避开高脂食材：肥肉/猪油/黄油；优先采购芹菜/菠菜/香蕉等高钾食材")

        if allergies:
            parts.append(f"【食品安全红线—过敏源】严格排除以下食材及其衍生物：{', '.join(allergies)}")
            parts.append("任何含有上述过敏源的食材、调味料、添加剂均不得采购！这是硬性约束！")

        if dietary:
            for d in dietary:
                if "vegetarian" in d.lower() or "素食" in d:
                    parts.append("【饮食偏好—素食】排除所有肉类/鱼虾，增加豆制品/菌菇/坚果类蛋白质来源")
                elif "vegan" in d.lower():
                    parts.append("【饮食偏好—严格素食】排除所有动物性食品（肉/鱼虾/蛋/奶/蜂蜜），植物蛋白替代")

        return "\n".join(parts) + "\n"
