"""Workflow router - Orchestrates multi-agent workflows for meal planning."""
import time
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import User, WorkflowExecution
from app.auth import get_optional_user
from app.agents.orchestrator import WorkflowOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflow", tags=["workflow"])

orchestrator = WorkflowOrchestrator()


@router.get("/types")
def get_workflow_types():
    """Get available workflow types and their descriptions."""
    return {
        "full_meal_service": {
            "name": "全流程膳食服务",
            "description": "完整膳食规划：周菜单生成→营养分析→采购清单→个性化定制",
            "agents": ["菜单规划", "营养分析", "采购清单", "膳食定制"]
        },
        "menu_and_nutrition": {
            "name": "菜单与营养",
            "description": "周菜单生成 + 营养均衡分析",
            "agents": ["菜单规划", "营养分析"]
        },
        "menu_and_procurement": {
            "name": "菜单与采购",
            "description": "周菜单生成 + 采购清单生成",
            "agents": ["菜单规划", "采购清单"]
        },
        "custom_meal_plan": {
            "name": "个性化定制方案",
            "description": "周菜单生成 + 针对不同青年群体的个性化调整",
            "agents": ["菜单规划", "膳食定制"]
        }
    }


@router.post("/execute")
def execute_workflow(
    request_data: dict,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Execute a workflow with the given configuration."""
    workflow_type = request_data.get("workflow_type", "full_meal_service")
    
    # Build input data from request
    input_data = {
        "num_people": request_data.get("num_people", 100),
        "budget_per_meal": request_data.get("budget_per_meal", 15),
        "season": request_data.get("season", "春季"),
        "dietary_requirements": request_data.get("dietary_requirements", []),
        "special_requirements": request_data.get("special_requirements", ""),
        "target_groups": request_data.get("target_groups", ["健身爱好者"]),
        "health_conditions": request_data.get("health_conditions", []),
        "target_population": request_data.get("target_population", "青年群体"),
        "existing_inventory": request_data.get("existing_inventory", []),
    }

    # Inject user profile from DB into input_data for personalized workflow
    if current_user:
        input_data["user_profile"] = {
            "height": current_user.height or 0,
            "weight": current_user.weight or 0,
            "age": current_user.age or 0,
            "goal": current_user.goal or "",
            "target_calories": current_user.target_calories or 0,
            "health_conditions": current_user.health_conditions or [],
            "allergies": (current_user.preferences or {}).get("allergies", []),
            "dietary": (current_user.preferences or {}).get("dietary", []),
            "skill_level": (current_user.preferences or {}).get("skill_level", "beginner"),
            "cuisines": (current_user.preferences or {}).get("cuisines", []),
        }

    # Use demo user if not authenticated
    user_id = current_user.id if current_user else 0
    
    # Create workflow execution record
    execution = WorkflowExecution(
        user_id=user_id,
        workflow_type=workflow_type,
        input_data=input_data,
        status="running",
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # Step update callback
    step_updates = []
    
    def on_step_update(step):
        step_updates.append(step)
        logger.info(f"Step {step.step_number} ({step.agent_name}): {step.status}")
    
    try:
        # Execute workflow
        result = orchestrator.execute_workflow(
            workflow_type=workflow_type,
            input_data=input_data,
            on_step_update=on_step_update
        )
        
        # Update execution record
        execution.status = "completed" if result.success else "error"
        execution.output_data = result.final_output
        execution.steps_log = [
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
            for s in result.steps
        ]
        execution.total_duration_ms = result.total_duration_ms
        execution.error_message = result.error if not result.success else None
        execution.steps_count = len(result.steps)
        
        db.commit()
        db.refresh(execution)
        
        return {
            "execution_id": execution.id,
            "status": execution.status,
            "workflow_type": workflow_type,
            "result_data": result.final_output,
            "steps_log": execution.steps_log,
            "total_duration_ms": result.total_duration_ms,
            "steps_count": len(result.steps),
            "error_message": result.error if not result.success else None,
        }
        
    except Exception as e:
        logger.exception("Workflow execution failed")
        execution.status = "error"
        execution.error_message = str(e)
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.get("/history")
def get_workflow_history(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get user's workflow execution history."""
    user_id = current_user.id if current_user else 0
    executions = db.query(WorkflowExecution).filter(
        WorkflowExecution.user_id == user_id
    ).order_by(WorkflowExecution.created_at.desc()).limit(20).all()
    
    return [
        {
            "id": e.id,
            "workflow_type": e.workflow_type,
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "total_duration_ms": e.total_duration_ms,
            "steps_count": e.steps_count,
            "error_message": e.error_message,
        }
        for e in executions
    ]


@router.get("/{execution_id}")
def get_workflow_execution(
    execution_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific workflow execution."""
    user_id = current_user.id if current_user else 0
    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.id == execution_id,
        WorkflowExecution.user_id == user_id
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return {
        "id": execution.id,
        "workflow_type": execution.workflow_type,
        "status": execution.status,
        "input_data": execution.input_data,
        "output_data": execution.output_data,
        "steps_log": execution.steps_log,
        "total_duration_ms": execution.total_duration_ms,
        "steps_count": execution.steps_count,
        "error_message": execution.error_message,
        "created_at": execution.created_at.isoformat() if execution.created_at else None,
    }
