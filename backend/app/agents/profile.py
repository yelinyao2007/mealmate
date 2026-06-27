"""
Profile Agent - Extracts and maintains user health profile.
Analyzes user health metrics, dietary restrictions, and goals.
"""
import json
from typing import Any, Dict

from app.agents.base import BaseAgent, AgentResult


class ProfileAgent(BaseAgent):
    name = "ProfileAgent"
    description = "用户画像代理 - 提取和维护用户的健康指标、饮食禁忌、目标，生成个性化推荐摘要"

    SYSTEM_PROMPT = """你是一位专业的健康营养顾问，负责根据用户的身体数据和目标，生成个性化的营养建议摘要。

你需要：
1. 根据身高、体重计算BMI，评估体重状况
2. 根据用户的goal（减脂/增肌/控糖/一般）推荐合理的每日目标热量和宏量营养素比例
3. 根据health_conditions（糖尿病/高血压等）给出饮食注意事项
4. 结合用户的饮食偏好(dietary)和过敏原(allergies)给出综合建议
5. 给出一周膳食核心原则总结

回复必须是有效的JSON格式：
{
  "bmi": 22.5,
  "bmi_category": "正常",
  "recommended_calories": 2000,
  "macro_targets": {
    "protein_g": 120,
    "fat_g": 55,
    "carbs_g": 250,
    "fiber_g": 30
  },
  "goal_analysis": {
    "goal": "减脂",
    "calorie_deficit": 300,
    "expected_weekly_loss_kg": 0.3,
    "key_principles": ["控制总热量", "增加蛋白质", "减少精制碳水"]
  },
  "health_warnings": [
    "注意低盐饮食",
    "避免高GI食物"
  ],
  "weekly_core_principles": [
    "每日摄入2000千卡",
    "蛋白质占比25%",
    "多食用全谷物和蔬菜"
  ],
  "summary": "根据你的BMI 22.5（正常范围），建议每日摄入2000千卡，蛋白质120g..."
}"""

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        height = input_data.get("height", 0)
        weight = input_data.get("weight", 0)
        age = input_data.get("age", 0)
        goal = input_data.get("goal", "")
        target_calories = input_data.get("target_calories", 0)
        health_conditions = input_data.get("health_conditions", [])
        preferences = input_data.get("preferences", {})

        user_message = f"""请根据以下用户数据，生成个性化的营养分析摘要：

身高: {height} cm
体重: {weight} kg
年龄: {age} 岁
目标: {goal or '未设定'} (可选值: lose_fat/减脂, gain_muscle/增肌, sugar_control/控糖, general/一般)
每日目标热量: {target_calories or '未设定'} kcal
健康状况: {', '.join(health_conditions) if health_conditions else '无特殊健康状况'}
饮食偏好: {json.dumps(preferences.get('dietary', []), ensure_ascii=False)}
过敏原: {json.dumps(preferences.get('allergies', []), ensure_ascii=False)}
烹饪水平: {preferences.get('skill_level', 'beginner')}
喜爱菜系: {json.dumps(preferences.get('cuisines', []), ensure_ascii=False)}

请从BMI、目标分析、健康预警、营养素分配等维度进行全面分析，给出JSON格式的结果。"""

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
