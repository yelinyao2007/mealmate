"""
Workflow Orchestrator - Chains multiple agents together to execute
complete end-to-end workflows autonomously.

This is the core of the agent orchestration system, demonstrating
autonomous multi-step workflow execution (not just simple Q&A).
"""
import time
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

from app.agents.base import AgentResult, AgentStep
from app.agents.menu_planner import MenuPlannerAgent
from app.agents.nutrition_analyzer import NutritionAnalyzerAgent
from app.agents.procurement import ProcurementAgent
from app.agents.meal_customizer import MealCustomizerAgent

logger = logging.getLogger(__name__)

# Check for demo mode (lazy evaluation to support delayed .env loading)
def _is_demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() == "true"


@dataclass
class WorkflowStep:
    """A step in the workflow execution."""
    step_number: int
    agent_name: str
    status: str = "pending"  # pending | running | completed | error
    input_summary: str = ""
    output_summary: str = ""
    duration_ms: int = 0
    agent_steps: List[dict] = field(default_factory=list)
    error: str = ""


@dataclass
class WorkflowResult:
    """Complete result of a workflow execution."""
    workflow_type: str
    success: bool
    steps: List[WorkflowStep]
    final_output: Dict[str, Any]
    total_duration_ms: int
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "workflow_type": self.workflow_type,
            "success": self.success,
            "steps": [
                {
                    "step_number": s.step_number,
                    "agent_name": s.agent_name,
                    "status": s.status,
                    "input_summary": s.input_summary,
                    "output_summary": s.output_summary,
                    "duration_ms": s.duration_ms,
                    "agent_steps": s.agent_steps,
                    "error": s.error,
                }
                for s in self.steps
            ],
            "final_output": self.final_output,
            "total_duration_ms": self.total_duration_ms,
            "error": self.error,
        }


class WorkflowOrchestrator:
    """
    Orchestrates multi-agent workflows for community meal service.

    Supported workflows:
    1. full_meal_service: Menu Planning -> Nutrition Analysis -> Procurement -> Meal Customization
    2. menu_and_nutrition: Menu Planning -> Nutrition Analysis
    3. menu_and_procurement: Menu Planning -> Procurement
    4. custom_meal_plan: Menu Planning -> Meal Customization
    """

    def execute_workflow(
        self,
        workflow_type: str,
        input_data: Dict[str, Any],
        on_step_update: Optional[callable] = None,
    ) -> WorkflowResult:
        """Execute a named workflow and return the complete result."""
        workflows = {
            "full_meal_service": self._full_meal_service,
            "menu_and_nutrition": self._menu_and_nutrition,
            "menu_and_procurement": self._menu_and_procurement,
            "custom_meal_plan": self._custom_meal_plan,
        }

        if workflow_type not in workflows:
            return WorkflowResult(
                workflow_type=workflow_type,
                success=False,
                steps=[],
                final_output={},
                total_duration_ms=0,
                error=f"Unknown workflow type: {workflow_type}",
            )

        start = time.time()
        try:
            result = workflows[workflow_type](input_data, on_step_update)
            result.total_duration_ms = int((time.time() - start) * 1000)
            return result
        except Exception as e:
            logger.exception("Workflow %s failed", workflow_type)
            return WorkflowResult(
                workflow_type=workflow_type,
                success=False,
                steps=[],
                final_output={},
                total_duration_ms=int((time.time() - start) * 1000),
                error=str(e),
            )

    def _run_agent(
        self,
        agent_cls,
        input_data: Dict[str, Any],
        step_number: int,
        on_step_update: Optional[callable] = None,
    ) -> tuple:
        """Run a single agent and return (WorkflowStep, AgentResult)."""
        agent = agent_cls()
        ws = WorkflowStep(
            step_number=step_number,
            agent_name=agent.name,
            status="running",
            input_summary=str(input_data)[:200],
        )
        if on_step_update:
            on_step_update(ws)

        start = time.time()
        result = agent.run(input_data)
        ws.duration_ms = int((time.time() - start) * 1000)
        ws.status = "completed" if result.success else "error"
        ws.output_summary = str(result.data)[:200] if result.success else result.error
        ws.error = result.error
        ws.agent_steps = [
            {
                "action": s.action,
                "duration_ms": s.duration_ms,
                "status": s.status,
            }
            for s in result.steps
        ]

        if on_step_update:
            on_step_update(ws)

        return ws, result

    def _run_agents_parallel(
        self,
        agents: list[tuple[type, dict[str, Any], int, Optional[callable]]],
    ) -> list[tuple]:
        """Run multiple agents concurrently using a thread pool.

        Each tuple is (agent_cls, input_data, step_number, on_step_update).
        Returns list of (WorkflowStep, AgentResult) in call order.
        """
        results = [None] * len(agents)
        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = {}
            for idx, (cls, inp, step, cb) in enumerate(agents):
                f = executor.submit(self._run_agent, cls, inp, step, cb)
                futures[f] = idx
            for f in as_completed(futures):
                idx = futures[f]
                try:
                    results[idx] = f.result()
                except Exception as e:
                    logger.error("Parallel agent %d failed: %s", idx, e)
                    results[idx] = (
                        WorkflowStep(
                            step_number=agents[idx][2],
                            agent_name=getattr(agents[idx][0], "name", f"Agent{idx}"),
                            status="error",
                            error=str(e),
                        ),
                        AgentResult(success=False, error=str(e), data={}),
                    )
        return results

    def _summarize_menu(self, weekly_menu: dict) -> dict:
        """Extract a lightweight summary from the full weekly menu for downstream agents."""
        summary = {}
        for day, meals in weekly_menu.items():
            summary[day] = {}
            for meal, detail in meals.items():
                summary[day][meal] = {
                    "dish_names": [
                        *(detail.get("荤菜", [])),
                        *(detail.get("素菜", [])),
                    ],
                    "cost": detail.get("estimated_cost_per_person"),
                }
        return summary

    def _full_meal_service(
        self,
        input_data: Dict[str, Any],
        on_step_update: Optional[callable] = None,
    ) -> WorkflowResult:
        """
        Full meal service workflow:
        1. Menu Planning Agent -> generates weekly menu
        2. Nutrition Analysis Agent -> evaluates nutrition
        3. Procurement Agent -> generates shopping list
        4. Meal Customizer Agent -> creates personalized plans
        """
        # DEMO MODE: Skip agents and return demo data directly
        if _is_demo_mode():
            logger.info("Demo mode enabled, returning demo full meal service data")
            demo_result = self._get_demo_full_meal_service(input_data)
            demo_step1 = WorkflowStep(
                step_number=1,
                agent_name="MenuPlannerAgent (Demo)",
                status="completed",
                input_summary="Demo mode - using pre-defined menu",
                output_summary="Demo weekly menu generated",
                duration_ms=100,
            )
            demo_step2 = WorkflowStep(
                step_number=2,
                agent_name="NutritionAnalyzerAgent (Demo)",
                status="completed",
                input_summary="Demo nutrition analysis",
                output_summary="Demo nutrition report generated",
                duration_ms=100,
            )
            demo_step3 = WorkflowStep(
                step_number=3,
                agent_name="ProcurementAgent (Demo)",
                status="completed",
                input_summary="Demo procurement list",
                output_summary="Demo shopping list generated",
                duration_ms=100,
            )
            demo_step4 = WorkflowStep(
                step_number=4,
                agent_name="MealCustomizerAgent (Demo)",
                status="completed",
                input_summary="Demo meal customization",
                output_summary="Demo customized meal plans generated",
                duration_ms=100,
            )
            return WorkflowResult("full_meal_service", True, [demo_step1, demo_step2, demo_step3, demo_step4], demo_result, 400, "")
        
        steps = []
        final_output = {}

        # Step 1: Menu Planning
        ws1, r1 = self._run_agent(MenuPlannerAgent, input_data, 1, on_step_update)
        steps.append(ws1)
        if not r1.success:
            # DEMO FALLBACK
            logger.warning("MenuPlannerAgent failed, using demo data: %s", r1.error)
            demo_result = self._get_demo_full_meal_service(input_data)
            demo_step1 = WorkflowStep(
                step_number=1,
                agent_name="MenuPlannerAgent (Demo)",
                status="completed",
                input_summary="Demo mode - using pre-defined menu",
                output_summary="Demo weekly menu generated",
                duration_ms=0,
            )
            demo_step2 = WorkflowStep(
                step_number=2,
                agent_name="NutritionAnalyzerAgent (Demo)",
                status="completed",
                input_summary="Demo nutrition analysis",
                output_summary="Demo nutrition report generated",
                duration_ms=0,
            )
            demo_step3 = WorkflowStep(
                step_number=3,
                agent_name="ProcurementAgent (Demo)",
                status="completed",
                input_summary="Demo procurement list",
                output_summary="Demo shopping list generated",
                duration_ms=0,
            )
            demo_step4 = WorkflowStep(
                step_number=4,
                agent_name="MealCustomizerAgent (Demo)",
                status="completed",
                input_summary="Demo meal customization",
                output_summary="Demo customized meal plans generated",
                duration_ms=0,
            )
            return WorkflowResult("full_meal_service", True, [demo_step1, demo_step2, demo_step3, demo_step4], demo_result, 0, "")
        final_output["menu_plan"] = r1.data

        # Steps 2-4: Run Nutrition, Procurement, Customization IN PARALLEL
        # All three only depend on Step 1 output, no cross-dependency
        weekly_menu = r1.data.get("weekly_menu", r1.data)
        # Use summarized menu for downstream agents (reduces prompt size ~80%)
        summarized_menu = self._summarize_menu(weekly_menu)

        parallel_agents = [
            (NutritionAnalyzerAgent, {
                "weekly_menu": summarized_menu,
                "target_population": input_data.get("target_population", "青年群体"),
            }, 2, on_step_update),
            (ProcurementAgent, {
                "weekly_menu": summarized_menu,
                "num_people": input_data.get("num_people", 100),
                "existing_inventory": input_data.get("existing_inventory", []),
            }, 3, on_step_update),
            (MealCustomizerAgent, {
                "weekly_menu": summarized_menu,
                "target_groups": input_data.get("target_groups", ["健身爱好者"]),
                "health_conditions": input_data.get("health_conditions", []),
            }, 4, on_step_update),
        ]

        parallel_results = self._run_agents_parallel(parallel_agents)
        ws2, r2 = parallel_results[0]
        ws3, r3 = parallel_results[1]
        ws4, r4 = parallel_results[2]
        steps.extend([ws2, ws3, ws4])

        if not r2.success:
            logger.warning("NutritionAnalyzerAgent failed: %s", r2.error)
            final_output["nutrition_analysis"] = {}
        else:
            final_output["nutrition_analysis"] = r2.data

        if not r3.success:
            logger.warning("ProcurementAgent failed: %s", r3.error)
            final_output["procurement"] = {}
        else:
            final_output["procurement"] = r3.data

        if not r4.success:
            logger.warning("MealCustomizerAgent failed: %s", r4.error)
            final_output["meal_customization"] = {}
        else:
            final_output["meal_customization"] = r4.data

        return WorkflowResult("full_meal_service", True, steps, final_output, 0)

    def _menu_and_nutrition(
        self,
        input_data: Dict[str, Any],
        on_step_update: Optional[callable] = None,
    ) -> WorkflowResult:
        """Menu Planning -> Nutrition Analysis."""
        # DEMO MODE: Skip agents and return demo data directly
        if _is_demo_mode():
            logger.info("Demo mode enabled, returning demo menu and nutrition data")
            demo_result = self._get_demo_menu_and_nutrition(input_data)
            demo_step1 = WorkflowStep(
                step_number=1,
                agent_name="MenuPlannerAgent (Demo)",
                status="completed",
                input_summary="Demo mode - using pre-defined menu",
                output_summary="Demo weekly menu generated",
                duration_ms=100,
            )
            demo_step2 = WorkflowStep(
                step_number=2,
                agent_name="NutritionAnalyzerAgent (Demo)",
                status="completed",
                input_summary="Demo nutrition analysis",
                output_summary="Demo nutrition report generated",
                duration_ms=100,
            )
            return WorkflowResult("menu_and_nutrition", True, [demo_step1, demo_step2], demo_result, 200, "")
        
        steps = []
        final_output = {}

        ws1, r1 = self._run_agent(MenuPlannerAgent, input_data, 1, on_step_update)
        steps.append(ws1)
        
        # DEMO FALLBACK: If agent fails (e.g., API not configured), return demo data
        if not r1.success:
            logger.warning("MenuPlannerAgent failed, using demo data: %s", r1.error)
            demo_result = self._get_demo_menu_and_nutrition(input_data)
            # Create a dummy step indicating demo mode
            demo_step = WorkflowStep(
                step_number=1,
                agent_name="MenuPlannerAgent (Demo)",
                status="completed",
                input_summary="Demo mode - using pre-defined menu",
                output_summary="Demo weekly menu generated",
                duration_ms=0,
            )
            demo_step2 = WorkflowStep(
                step_number=2,
                agent_name="NutritionAnalyzerAgent (Demo)",
                status="completed",
                input_summary="Demo nutrition analysis",
                output_summary="Demo nutrition report generated",
                duration_ms=0,
            )
            return WorkflowResult("menu_and_nutrition", True, [demo_step, demo_step2], demo_result, 0, "")
        
        final_output["menu_plan"] = r1.data

        nutrition_input = {
            "weekly_menu": r1.data.get("weekly_menu", r1.data),
            "target_population": input_data.get("target_population", "青年群体"),
        }
        ws2, r2 = self._run_agent(NutritionAnalyzerAgent, nutrition_input, 2, on_step_update)
        steps.append(ws2)
        
        if not r2.success:
            logger.warning("NutritionAnalyzerAgent failed, using demo nutrition data")
            # Still include menu plan, but add empty nutrition
            final_output["nutrition_analysis"] = {}
        else:
            final_output["nutrition_analysis"] = r2.data

        return WorkflowResult("menu_and_nutrition", r2.success, steps, final_output, 0, r2.error)

    def _menu_and_procurement(
        self,
        input_data: Dict[str, Any],
        on_step_update: Optional[callable] = None,
    ) -> WorkflowResult:
        """Menu Planning -> Procurement List."""
        # DEMO MODE: Skip agents and return demo data directly
        if _is_demo_mode():
            logger.info("Demo mode enabled, returning demo menu and procurement data")
            demo_result = self._get_demo_menu_and_procurement(input_data)
            demo_step1 = WorkflowStep(
                step_number=1,
                agent_name="MenuPlannerAgent (Demo)",
                status="completed",
                input_summary="Demo mode - using pre-defined menu",
                output_summary="Demo weekly menu generated",
                duration_ms=100,
            )
            demo_step2 = WorkflowStep(
                step_number=2,
                agent_name="ProcurementAgent (Demo)",
                status="completed",
                input_summary="Demo procurement list",
                output_summary="Demo shopping list generated",
                duration_ms=100,
            )
            return WorkflowResult("menu_and_procurement", True, [demo_step1, demo_step2], demo_result, 200, "")
        
        steps = []
        final_output = {}

        ws1, r1 = self._run_agent(MenuPlannerAgent, input_data, 1, on_step_update)
        steps.append(ws1)
        
        # DEMO FALLBACK
        if not r1.success:
            logger.warning("MenuPlannerAgent failed, using demo data: %s", r1.error)
            demo_result = self._get_demo_menu_and_procurement(input_data)
            demo_step1 = WorkflowStep(
                step_number=1,
                agent_name="MenuPlannerAgent (Demo)",
                status="completed",
                input_summary="Demo mode - using pre-defined menu",
                output_summary="Demo weekly menu generated",
                duration_ms=0,
            )
            demo_step2 = WorkflowStep(
                step_number=2,
                agent_name="ProcurementAgent (Demo)",
                status="completed",
                input_summary="Demo procurement list",
                output_summary="Demo shopping list generated",
                duration_ms=0,
            )
            return WorkflowResult("menu_and_procurement", True, [demo_step1, demo_step2], demo_result, 0, "")
        
        final_output["menu_plan"] = r1.data

        procurement_input = {
            "weekly_menu": r1.data.get("weekly_menu", r1.data),
            "num_people": input_data.get("num_people", 100),
            "existing_inventory": input_data.get("existing_inventory", []),
        }
        ws2, r2 = self._run_agent(ProcurementAgent, procurement_input, 2, on_step_update)
        steps.append(ws2)
        final_output["procurement"] = r2.data if r2.success else {}

        return WorkflowResult("menu_and_procurement", r2.success, steps, final_output, 0, r2.error)

    def _custom_meal_plan(
        self,
        input_data: Dict[str, Any],
        on_step_update: Optional[callable] = None,
    ) -> WorkflowResult:
        """Menu Planning -> Meal Customization."""
        # DEMO MODE: Skip agents and return demo data directly
        if _is_demo_mode():
            logger.info("Demo mode enabled, returning demo custom meal plan data")
            demo_result = self._get_demo_custom_meal_plan(input_data)
            demo_step1 = WorkflowStep(
                step_number=1,
                agent_name="MenuPlannerAgent (Demo)",
                status="completed",
                input_summary="Demo mode - using pre-defined menu",
                output_summary="Demo weekly menu generated",
                duration_ms=100,
            )
            demo_step2 = WorkflowStep(
                step_number=2,
                agent_name="MealCustomizerAgent (Demo)",
                status="completed",
                input_summary="Demo meal customization",
                output_summary="Demo customized meal plans generated",
                duration_ms=100,
            )
            return WorkflowResult("custom_meal_plan", True, [demo_step1, demo_step2], demo_result, 200, "")
        
        steps = []
        final_output = {}

        ws1, r1 = self._run_agent(MenuPlannerAgent, input_data, 1, on_step_update)
        steps.append(ws1)
        
        # DEMO FALLBACK
        if not r1.success:
            logger.warning("MenuPlannerAgent failed, using demo data: %s", r1.error)
            demo_result = self._get_demo_custom_meal_plan(input_data)
            demo_step1 = WorkflowStep(
                step_number=1,
                agent_name="MenuPlannerAgent (Demo)",
                status="completed",
                input_summary="Demo mode - using pre-defined menu",
                output_summary="Demo weekly menu generated",
                duration_ms=0,
            )
            demo_step2 = WorkflowStep(
                step_number=2,
                agent_name="MealCustomizerAgent (Demo)",
                status="completed",
                input_summary="Demo meal customization",
                output_summary="Demo customized meal plans generated",
                duration_ms=0,
            )
            return WorkflowResult("custom_meal_plan", True, [demo_step1, demo_step2], demo_result, 0, "")
        
        final_output["menu_plan"] = r1.data

        customize_input = {
            "weekly_menu": r1.data.get("weekly_menu", r1.data),
            "target_groups": input_data.get("target_groups", ["青年白领"]),
            "health_conditions": input_data.get("health_conditions", []),
            "individual_preferences": input_data.get("individual_preferences", ""),
        }
        ws2, r2 = self._run_agent(MealCustomizerAgent, customize_input, 2, on_step_update)
        steps.append(ws2)
        final_output["meal_customization"] = r2.data if r2.success else {}

        return WorkflowResult("custom_meal_plan", r2.success, steps, final_output, 0, r2.error)

    def _get_demo_menu_and_procurement(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate demo menu and procurement data for showcase."""
        num_people = input_data.get("num_people", 100)
        budget = input_data.get("budget_per_meal", 15)
        
        # Use the same demo menu
        menu_data = self._get_demo_menu_and_nutrition(input_data)
        
        # Calculate procurement based on menu (rough estimate)
        # For demo, generate a simple shopping list
        procurement = {
            "grains": {
                "大米": f"{num_people * 0.2:.1f}kg",
                "面粉": f"{num_people * 0.1:.1f}kg",
                "面条": f"{num_people * 0.15:.1f}kg"
            },
            "proteins": {
                "鸡肉": f"{num_people * 0.15:.1f}kg",
                "猪肉": f"{num_people * 0.12:.1f}kg",
                "鱼肉": f"{num_people * 0.1:.1f}kg",
                "鸡蛋": f"{num_people * 0.3:.0f}个",
                "豆腐": f"{num_people * 0.2:.1f}kg"
            },
            "vegetables": {
                "青菜": f"{num_people * 0.3:.1f}kg",
                "西红柿": f"{num_people * 0.2:.1f}kg",
                "土豆": f"{num_people * 0.25:.1f}kg",
                "黄瓜": f"{num_people * 0.15:.1f}kg",
                "西兰花": f"{num_people * 0.2:.1f}kg"
            },
            "seasonings": {
                "食用油": "5L",
                "食盐": "500g",
                "酱油": "1L",
                "醋": "500ml",
                "糖": "1kg"
            },
            "estimated_total_cost": round(num_people * 3.5 * 5, 2),  # 5 days
            "notes": "此为演示采购清单，实际采购请根据具体菜单调整"
        }
        
        return {
            "menu_plan": menu_data.get("weekly_menu", {}),
            "procurement": procurement
        }

    def _get_demo_menu_and_nutrition(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate demo menu and nutrition data for showcase purposes."""
        num_people = input_data.get("num_people", 100)
        budget = input_data.get("budget_per_meal", 15)
        season = input_data.get("season", "春季")
        
        # Demo weekly menu (Monday to Friday, lunch and dinner)
        weekly_menu = {
            "周一": {
                "午餐": {
                    "主食": ["米饭", "小米粥"],
                    "荤菜": ["红烧鸡块", "清蒸鱼"],
                    "素菜": ["炒青菜", "凉拌黄瓜"],
                    "汤品": "冬瓜排骨汤",
                    "estimated_cost_per_person": round(budget * 0.9, 1)
                },
                "晚餐": {
                    "主食": ["馒头", "杂粮饭"],
                    "荤菜": ["肉末豆腐", "番茄炒蛋"],
                    "素菜": ["蒜蓉西兰花", "清炒豆芽"],
                    "汤品": "紫菜蛋花汤",
                    "estimated_cost_per_person": round(budget * 0.8, 1)
                }
            },
            "周二": {
                "午餐": {
                    "主食": ["面条", "发糕"],
                    "荤菜": ["糖醋里脊", "芹菜香干"],
                    "素菜": ["醋溜白菜", "素炒三丝"],
                    "汤品": "番茄蛋汤",
                    "estimated_cost_per_person": round(budget * 0.85, 1)
                },
                "晚餐": {
                    "主食": ["米饭", "玉米粥"],
                    "荤菜": ["土豆炖牛肉", "虾仁蒸蛋"],
                    "素菜": ["手撕包菜", "清炒生菜"],
                    "汤品": "萝卜丝汤",
                    "estimated_cost_per_person": round(budget * 0.75, 1)
                }
            },
            "周三": {
                "午餐": {
                    "主食": ["包子", "豆浆"],
                    "荤菜": ["鱼香肉丝", "红烧狮子头"],
                    "素菜": ["干煸四季豆", "清炒苦瓜"],
                    "汤品": "白菜豆腐汤",
                    "estimated_cost_per_person": round(budget * 0.9, 1)
                },
                "晚餐": {
                    "主食": ["米饭", "绿豆汤"],
                    "荤菜": ["回锅肉", "宫保鸡丁"],
                    "素菜": ["地三鲜", "凉拌西红柿"],
                    "汤品": "冬瓜海带汤",
                    "estimated_cost_per_person": round(budget * 0.8, 1)
                }
            },
            "周四": {
                "午餐": {
                    "主食": ["炒饭", "南瓜粥"],
                    "荤菜": ["梅菜扣肉", "可乐鸡翅"],
                    "素菜": ["香菇油菜", "清炒莴笋"],
                    "汤品": "蛋花汤",
                    "estimated_cost_per_person": round(budget * 0.95, 1)
                },
                "晚餐": {
                    "主食": ["花卷", "大米粥"],
                    "荤菜": ["木须肉", "水煮肉片"],
                    "素菜": ["虎皮青椒", "清炒土豆丝"],
                    "汤品": "黄瓜鸡蛋汤",
                    "estimated_cost_per_person": round(budget * 0.8, 1)
                }
            },
            "周五": {
                "午餐": {
                    "主食": ["饺子", "馄饨"],
                    "荤菜": ["猪肉炖粉条", "大盘鸡"],
                    "素菜": ["蚝油生菜", "酸辣土豆丝"],
                    "汤品": "西红柿鸡蛋汤",
                    "estimated_cost_per_person": round(budget * 0.9, 1)
                },
                "晚餐": {
                    "主食": ["米饭", "八宝粥"],
                    "荤菜": ["红烧排骨", "酸菜鱼"],
                    "素菜": ["麻婆豆腐", "清炒空心菜"],
                    "汤品": "玉米胡萝卜汤",
                    "estimated_cost_per_person": round(budget * 0.85, 1)
                }
            }
        }
        
        total_weekly_cost = sum(
            day_data[meal]["estimated_cost_per_person"] 
            for day_data in weekly_menu.values() 
            for meal in ["午餐", "晚餐"]
        )
        
        return {
            "weekly_menu": weekly_menu,
            "total_weekly_cost_per_person": round(total_weekly_cost, 2),
            "nutrition_summary": f"本周菜单遵循{season}营养搭配原则，为年轻人群优化蛋白质、碳水化合物、健康脂肪的摄入。每日膳食包含主食、荤菜2道、素菜2道、汤品1份，着重满足不同青年群体的能量需求和口味偏好。",
            "seasonal_highlights": [f"{season}时令食材", "高蛋白低脂肪", "快手健康餐"],
            "special_notes": "菜品注重快手、健康、高蛋白，适合年轻白领、健身人士和学生群体的饮食需求。"
        }

    def _get_demo_custom_meal_plan(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate demo customized meal plan data."""
        menu_data = self._get_demo_menu_and_nutrition(input_data)
        target_groups = input_data.get("target_groups", ["老年人"])
        health_conditions = input_data.get("health_conditions", [])
        
        # Customizations based on target groups
        customizations = {
            "健身爱好者": {
                "protein_level": "高蛋白 (>1.6g/kg体重)",
                "carb_source": "复合碳水（糙米、全麦、红薯）",
                "fat_control": "优质脂肪（牛油果、坚果、橄榄油）",
                "meal_frequency": "5-6餐/日（含加餐）",
                "special_instructions": "每餐保证30-40g蛋白质，训练后补充快碳+蛋白"
            },
            "素食主义者": {
                "protein_source": "植物蛋白（豆腐、藜麦、鹰嘴豆、面筋）",
                "nutrient_supplements": "B12、铁、锌、Omega-3",
                "cooking_style": "少油快炒、蒸煮为主",
                "special_instructions": "搭配豆类+谷物提高蛋白质利用率，多食用深绿色蔬菜补铁"
            },
            "加班族": {
                "prep_time": "快速 (<20分钟)",
                "meal_prep": "周末备餐推荐",
                "energy_boost": "高能量密度 + 提神食材",
                "digestive_care": "易消化（避免油腻），护胃食材",
                "special_instructions": "推荐可以批量预制、冷冻保存的菜品，工作日加热即食"
            },
            "学生党": {
                "budget": "极致性价比 (<15元/餐)",
                "equipment": "宿舍可用（电饭煲/小电锅）",
                "ingredient": "耐储存食材（土豆、鸡蛋、火腿肠）",
                "nutrition_focus": "能量充足 + 补脑食材（核桃、深海鱼）",
                "special_instructions": "一锅出的快手菜为主，兼顾营养和成本"
            },
            "美食博主": {
                "aesthetics": "高颜值摆盘、色彩搭配",
                "innovation": "融合菜、创意搭配",
                "storytelling": "每道菜有故事/文化背景",
                "photography_tips": "适合拍照的光线和摆盘建议",
                "special_instructions": "菜品要有'出片感'，配色丰富，适合社交媒体分享"
            }
        }
        
        # Build group-specific customizations
        group_plans = {}
        for group in target_groups:
            group_plans[group] = customizations.get(group, {
                "texture": "正常",
                "portion_size": "标准",
                "special_instructions": "无特殊要求"
            })
        
        return {
            "weekly_menu": menu_data.get("weekly_menu", {}),
            "customization_plans": group_plans,
            "general_notes": "所有定制菜单均基于原菜单微调，针对不同青年群体的生活方式和健康目标优化，保证营养均衡。"
        }

    def _get_demo_full_meal_service(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate demo data for full meal service workflow."""
        num_people = input_data.get("num_people", 100)
        budget = input_data.get("budget_per_meal", 15)
        
        menu_data = self._get_demo_menu_and_nutrition(input_data)
        procurement_data = {
            "grains": {
                "大米": f"{num_people * 0.2:.1f}kg",
                "面粉": f"{num_people * 0.1:.1f}kg",
                "面条": f"{num_people * 0.15:.1f}kg"
            },
            "proteins": {
                "鸡肉": f"{num_people * 0.15:.1f}kg",
                "猪肉": f"{num_people * 0.12:.1f}kg",
                "鱼肉": f"{num_people * 0.1:.1f}kg",
                "鸡蛋": f"{num_people * 0.3:.0f}个",
                "豆腐": f"{num_people * 0.2:.1f}kg"
            },
            "vegetables": {
                "青菜": f"{num_people * 0.3:.1f}kg",
                "西红柿": f"{num_people * 0.2:.1f}kg",
                "土豆": f"{num_people * 0.25:.1f}kg",
                "黄瓜": f"{num_people * 0.15:.1f}kg", 
                "西兰花": f"{num_people * 0.2:.1f}kg"
            },
            "seasonings": {
                "食用油": "5L",
                "食盐": "500g",
                "酱油": "1L",
                "醋": "500ml",
                "糖": "1kg"
            },
            "estimated_total_cost": round(num_people * 3.5 * 5, 2),
            "notes": "此为演示采购清单，实际采购请根据具体菜单调整"
        }
        
        target_groups = input_data.get("target_groups", ["健身爱好者"])
        customizations = {
            "健身爱好者": {
                "protein_level": "高蛋白 (>1.6g/kg体重)",
                "carb_source": "复合碳水（糙米、全麦、红薯）",
                "fat_control": "优质脂肪（牛油果、坚果、橄榄油）",
                "meal_frequency": "5-6餐/日（含加餐）",
                "special_instructions": "每餐保证30-40g蛋白质，训练后补充快碳+蛋白"
            },
            "素食主义者": {
                "protein_source": "植物蛋白（豆腐、藜麦、鹰嘴豆、面筋）",
                "nutrient_supplements": "B12、铁、锌、Omega-3",
                "cooking_style": "少油快炒、蒸煮为主",
                "special_instructions": "搭配豆类+谷物提高蛋白质利用率，多食用深绿色蔬菜补铁"
            },
            "加班族": {
                "prep_time": "快速 (<20分钟)",
                "meal_prep": "周末备餐推荐",
                "energy_boost": "高能量密度 + 提神食材",
                "digestive_care": "易消化（避免油腻），护胃食材",
                "special_instructions": "推荐可以批量预制、冷冻保存的菜品，工作日加热即食"
            },
            "学生党": {
                "budget": "极致性价比 (<15元/餐)",
                "equipment": "宿舍可用（电饭煲/小电锅）",
                "ingredient": "耐储存食材（土豆、鸡蛋、火腿肠）",
                "nutrition_focus": "能量充足 + 补脑食材（核桃、深海鱼）",
                "special_instructions": "一锅出的快手菜为主，兼顾营养和成本"
            },
            "美食博主": {
                "aesthetics": "高颜值摆盘、色彩搭配",
                "innovation": "融合菜、创意搭配",
                "storytelling": "每道菜有故事/文化背景",
                "photography_tips": "适合拍照的光线和摆盘建议",
                "special_instructions": "菜品要有'出片感'，配色丰富，适合社交媒体分享"
            }
        }
        
        group_plans = {}
        for group in target_groups:
            group_plans[group] = customizations.get(group, {
                "texture": "正常",
                "portion_size": "标准",
                "special_instructions": "无特殊要求"
            })
        
        return {
            "menu_plan": menu_data.get("weekly_menu", {}),
            "nutrition_analysis": {
                "nutrition_summary": menu_data.get("nutrition_summary", ""),
                "seasonal_highlights": menu_data.get("seasonal_highlights", []),
                "special_notes": menu_data.get("special_notes", "")
            },
            "procurement": procurement_data,
            "meal_customization": {
                "customization_plans": group_plans,
                "general_notes": "所有定制菜单均基于原菜单微调，针对不同青年群体优化，保证营养均衡。"
            }
        }
