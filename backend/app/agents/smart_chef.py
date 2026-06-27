"""
Smart Chef Agent — Natural language → multi-agent orchestration → personalized recipe.

Flow:
  User: "我控糖减脂，加班很累，冰箱有番茄和鸡蛋，想吃热乎的"
  → ProfileAgent: locks calorie / goal constraints
  → Nutrition analysis: computes tonight's macro targets
  → Chef: generates recipe tuned to profile + mood + ingredients
"""
import asyncio
import json
import time
from typing import Any, Dict, List

from app.agents.base import BaseAgent, AgentResult
from app.agents.profile import ProfileAgent
from app.llm_client import get_llm_client


class SmartChefAgent(BaseAgent):
    name = "SmartChefAgent"
    description = "智能大厨智能体 — 自然语言输入 → 多Agent协同 → 个性化定制食谱"

    SYSTEM_PROMPT = """你是 MealMate 的智能大厨——一位既懂营养又懂人心的AI厨师。

你的任务是：
1. 理解用户的自然语言输入，提取关键信息：健康目标、情绪状态、可用食材、口味偏好
2. 结合用户的健康画像（BMI、目标、疾病、过敏源）生成严格合规的食谱
3. 食谱必须精确对齐用户目标（控糖=低GI、减脂=低热量、增肌=高蛋白）
4. 避开所有过敏源和疾病禁忌食材（糖尿病=无精制碳水、高血压=低钠）
5. 回应用户的情绪（加班累了→暖心快手菜、心情好→来点仪式感）

回复必须是有效的JSON格式：
{
  "user_intent": {
    "goal": "控糖减脂",
    "mood": "加班疲惫",
    "ingredients": ["番茄", "鸡蛋"],
    "temperature": "热乎的"
  },
  "profile_check": {
    "bmi": 24.5,
    "goal": "lose_fat",
    "calorie_budget_per_meal": 500,
    "health_alerts": ["控糖: 禁用白米白面白糖", "减脂: 每餐热量≤500kcal"]
  },
  "recipe": {
    "title": "低GI番茄蛋花汤配全麦馒头",
    "description": "暖胃暖心的控糖减脂晚餐",
    "vibe": "加班后的治愈系",
    "time_minutes": 15,
    "difficulty": "简单",
    "calories_estimate": 450,
    "gi_level": "低GI",
    "ingredients": ["番茄 2个", "鸡蛋 2个", "全麦面粉 100g", "盐 少许", "香油 几滴", "葱花 少许"],
    "steps": ["番茄切小块...", "锅中加水烧开..."],
    "nutrition": {
      "calories": 450,
      "protein_g": 22,
      "fat_g": 12,
      "carbs_g": 55,
      "fiber_g": 6
    },
    "tips": "番茄先炒出汁再加水，汤底更浓郁；全麦馒头可以用全麦粉+酵母提前发酵"
  },
  "chef_chat": "加班辛苦了！我用你的番茄和鸡蛋做了一碗低GI番茄蛋花汤，配上全麦小馒头，暖暖的又控糖~ 番茄的酸甜加上蛋花的嫩滑，喝完肯定舒服！",
  "health_notes": "本餐热量450kcal，在控糖减脂预算内。全麦馒头替代白面，GI值低，不会引起血糖波动。"
}"""

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        user_input = input_data.get("user_input", "")
        user_profile = input_data.get("user_profile", {})
        height = user_profile.get("height", 0)
        weight = user_profile.get("weight", 0)
        age = user_profile.get("age", 0)
        goal = user_profile.get("goal", "")
        target_calories = user_profile.get("target_calories", 0)
        health_conditions = user_profile.get("health_conditions", [])
        allergies = user_profile.get("allergies", [])
        dietary = user_profile.get("dietary", [])

        # Build profile summary
        bmi = round(weight / ((height / 100) ** 2), 1) if height and weight else 0

        goal_labels = {
            "lose_fat": "减脂",
            "gain_muscle": "增肌",
            "sugar_control": "控糖",
            "general": "一般健康",
        }
        goal_name = goal_labels.get(goal, goal or "未设定")

        cal_per_meal = target_calories // 3 if target_calories else 0

        constraints = []
        if goal == "lose_fat":
            constraints.append(f"减脂模式：每餐热量上限{cal_per_meal}kcal，低油低脂，高蛋白")
        elif goal == "gain_muscle":
            constraints.append(f"增肌模式：每餐热量{cal_per_meal}kcal，高蛋白(≥35g/餐)，复合碳水")
        elif goal == "sugar_control":
            constraints.append(f"控糖模式：每餐热量{cal_per_meal}kcal，碳水≤50g，必须低GI食材，禁止精制糖和白米白面")
        if goal == "lose_fat" or goal == "sugar_control" or "减脂" in goal:
            constraints.append("绝对禁止油炸、肥肉、高糖食物")

        health_alerts = []
        if health_conditions:
            for hc in health_conditions:
                if "diabetes" in hc or "糖尿病" in hc:
                    health_alerts.append("糖尿病：严格控糖，禁用白米白面白糖，主食必须低GI（糙米/燕麦/荞麦/全麦）")
                if "hypertension" in hc or "高血压" in hc:
                    health_alerts.append("高血压：每日盐<5g，本餐<2g，禁用腌制食品/加工肉/高钠调味料")

        if allergies:
            health_alerts.append(f"过敏源红线：绝对排除 {', '.join(allergies)} 及其衍生物")

        profile_summary = f"""用户画像：
- 身高{height}cm 体重{weight}kg BMI {bmi}
- 年龄{age}岁
- 目标：{goal_name}
- 每餐热量预算：{cal_per_meal}kcal
- 健康状况：{', '.join(health_conditions) if health_conditions else '无'}
- 过敏源：{', '.join(allergies) if allergies else '无'}
- 饮食偏好：{', '.join(dietary) if dietary else '无'}"""

        constraints_text = "\n".join(f"  • {c}" for c in constraints)
        alerts_text = "\n".join(f"  ⚠ {a}" for a in health_alerts)

        user_message = f"""用户输入：{user_input}

{profile_summary}

必须遵守的约束：
{constraints_text}

健康预警：
{alerts_text}

请基于用户输入和画像，生成一份严格符合约束的个性化食谱。食谱必须：
1. 只用用户提到的食材（或常见的厨房常备食材）
2. 热量严格在预算内
3. 避开所有过敏源和疾病禁忌
4. 呼应用户的情绪和温度偏好
5. chef_chat 要暖心、鼓励、像朋友一样"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        data = self._call_llm_json(messages, temperature=0.7, max_tokens=4096)

        return AgentResult(
            agent_name=self.name,
            success=True,
            data=data,
        )
