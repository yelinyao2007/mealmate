"""
Procurement Agent - Generates optimized procurement lists from meal plans.
Consolidates ingredients, estimates quantities and costs.
"""
import json
from typing import Any, Dict

from app.agents.base import BaseAgent, AgentResult


class ProcurementAgent(BaseAgent):
    name = "ProcurementAgent"
    description = "采购清单智能体 - 从菜单自动生成优化采购清单，控制成本减少浪费"

    SYSTEM_PROMPT = """你是社区食堂的AI采购专家，负责根据一周菜单生成采购清单。

你需要：
1. 将菜单中所有菜品的食材进行汇总合并
2. 根据用餐人数计算合理的采购量
3. 估算每种食材的采购价格（参考上海市场批发价）
4. 按食材类别分类（肉类、蔬菜、调料等）
5. 标注保质期短需优先使用的食材
6. 计算总采购预算

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
  "total_budget": 12500.0,
  "budget_per_person_per_day": 25.0,
  "perishable_items": ["..."],
  "storage_notes": "...",
  "suggested_suppliers": "建议联系社区定点供应商，优先采购本地时令蔬菜",
  "waste_reduction_tips": ["..."]
}"""

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        menu_data = input_data.get("weekly_menu", {})
        num_people = input_data.get("num_people", 100)
        existing_inventory = input_data.get("existing_inventory", [])

        menu_text = json.dumps(menu_data, ensure_ascii=False, indent=2)

        inventory_note = ""
        if existing_inventory:
            inventory_note = f"\n已有库存食材（无需重复采购）：{', '.join(existing_inventory)}"

        user_message = f"""请根据以下一周菜单生成采购清单：

{menu_text}

用餐人数：{num_people}人/餐
{inventory_note}

请计算所需食材总量，估算采购成本，并按类别整理。"""

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
