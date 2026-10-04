import json
import uuid
import logging
from datetime import datetime, timezone
from app.extensions import db
from app.models.agents import AgentRegistry, AgentTask
from app.services.agents.inventory_agent import InventoryAgent
from app.services.agents.kitchen_agent import KitchenAgent
from app.services.agents.procurement_agent import ProcurementAgent
from app.services.agents.demand_agent import DemandAgent
from app.services.agents.enterprise_agent import EnterpriseAgent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Milestone 13 & 15: Agent Orchestrator
    Coordinates specialized agents, creates tasks, handles retries and state.
    """
    
    # In a real system, these would be dynamically loaded.
    AGENTS = {
        'INVENTORY_AGENT': InventoryAgent(),
        'KITCHEN_AGENT': KitchenAgent(),
        'PROCUREMENT_AGENT': ProcurementAgent(),
        'DEMAND_AGENT': DemandAgent(),
        'ENTERPRISE_AGENT': EnterpriseAgent()
    }
    
    @staticmethod
    def initialize_agents():
        """Registers all agents to DB (Milestone 2)"""
        for agent in AgentOrchestrator.AGENTS.values():
            agent.register()
            
    @staticmethod
    def dispatch_task(agent_id, trigger_event, payload, correlation_id=None, institution_id=None, priority='MEDIUM'):
        """
        Creates a task and dispatches it to the designated agent.
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
            
        task = AgentTask(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            institution_id=institution_id,
            trigger_event=trigger_event,
            correlation_id=correlation_id,
            priority=priority,
            input_payload=payload
        )
        db.session.add(task)
        db.session.commit()
        
        # In production this would send to Celery/SQS. Here we execute synchronously for MVP.
        return AgentOrchestrator.execute_task(task.id)

    @staticmethod
    def execute_task(task_id):
        """
        Executes a task securely. (Milestone 21, 22)
        """
        task = AgentTask.query.get(task_id)
        if not task:
            return None
            
        agent_instance = AgentOrchestrator.AGENTS.get(task.agent_id)
        if not agent_instance:
            task.status = 'FAILED'
            task.error_message = f"Agent {task.agent_id} not available."
            db.session.commit()
            return task
            
        agent_record = AgentRegistry.query.get(task.agent_id)
        if agent_record.status != 'ACTIVE':
            task.status = 'CANCELLED'
            task.error_message = f"Agent {task.agent_id} is {agent_record.status}"
            db.session.commit()
            return task
            
        task.status = 'RUNNING'
        task.started_at = datetime.now(timezone.utc)
        db.session.commit()
        
        try:
            # Delegate to specialized agent
            result = agent_instance.process_task(task)
            
            task.result_payload = result
            task.status = 'COMPLETED'
            
            # Reset failure count (Self-healing Milestone 22)
            agent_record.failure_count = 0
            
        except Exception as e:
            logger.error(f"Task {task.id} failed: {str(e)}")
            task.error_message = str(e)
            task.status = 'FAILED'
            
            agent_record.failure_count += 1
            if agent_record.failure_count > 5:
                agent_record.status = 'PAUSED' # Circuit Breaker (Milestone 62)
                
        finally:
            task.completed_at = datetime.now(timezone.utc)
            agent_record.last_execution_at = datetime.now(timezone.utc)
            db.session.commit()
            
        return task
