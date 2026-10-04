import json
import logging
import inspect
from functools import wraps
from datetime import datetime, timezone
from app.extensions import db
from app.models.agents import AgentRegistry, AgentToolExecution

logger = logging.getLogger(__name__)

def agent_tool(name, purpose, is_high_risk=False):
    """
    Milestone 5: Tool Framework
    Decorator that explicitly registers a method as an approved agent tool.
    Enforces audit logging via AgentToolExecution.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, task, *args, **kwargs):
            # Pre-execution: Validate task and permissions
            if task.status != 'RUNNING':
                raise Exception(f"Cannot execute tool on task {task.id} in state {task.status}")
                
            tool_args = inspect.signature(func).bind(self, task, *args, **kwargs).arguments
            clean_args = {k: v for k, v in tool_args.items() if k not in ('self', 'task')}
            
            # Execute the tool
            try:
                result = func(self, task, *args, **kwargs)
                
                # Post-execution: Audit successful execution
                audit = AgentToolExecution(
                    task_id=task.id,
                    agent_id=self.agent_id,
                    tool_name=name,
                    input_args=clean_args,
                    output_result=result,
                    is_high_risk=is_high_risk
                )
                db.session.add(audit)
                db.session.commit()
                
                return result
            except Exception as e:
                # Audit failed execution
                audit = AgentToolExecution(
                    task_id=task.id,
                    agent_id=self.agent_id,
                    tool_name=name,
                    input_args=clean_args,
                    output_result={"error": str(e)},
                    is_high_risk=is_high_risk
                )
                db.session.add(audit)
                db.session.commit()
                raise
                
        # Register metadata on the wrapper
        wrapper._is_agent_tool = True
        wrapper._tool_name = name
        wrapper._tool_purpose = purpose
        wrapper._is_high_risk = is_high_risk
        return wrapper
    return decorator

class BaseAgent:
    def __init__(self):
        self.agent_id = None # Set by subclass
        self.agent_name = None
        self.purpose = None
        self.version = 'v1.0'
        
    def register(self):
        """Milestone 2: Ensure agent is registered in the DB"""
        agent = AgentRegistry.query.get(self.agent_id)
        
        # Discover tools
        tools = []
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if getattr(method, '_is_agent_tool', False):
                tools.append(method._tool_name)
                
        if not agent:
            agent = AgentRegistry(
                id=self.agent_id,
                name=self.agent_name,
                version=self.version,
                purpose=self.purpose,
                allowed_tools=tools
            )
            db.session.add(agent)
        else:
            agent.allowed_tools = tools
            agent.version = self.version
            
        db.session.commit()
        return agent

    def process_task(self, task):
        """
        Abstract method. Every agent implements its specific logic here.
        Must return a dict representing the result payload, or raise an Exception.
        """
        raise NotImplementedError("Agents must implement process_task()")
