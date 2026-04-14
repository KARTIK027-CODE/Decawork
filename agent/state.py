from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Literal
from config.logger import logger
import uuid

class ExecutionLog(BaseModel):
    action: str
    target: Optional[str] = None
    status: Literal['success', 'failed', 'skipped', 'running']
    details: str

class AgentStateModel(BaseModel):
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    current_step_index: int = 0
    total_steps: int = 0
    execution_history: List[ExecutionLog] = []
    current_page_snapshot: Optional[Dict[str, Any]] = None
    status: Literal['initialized', 'running', 'failed', 'completed'] = 'initialized'
    retry_metrics: Dict[str, int] = {}
    is_dry_run: bool = False

class AgentState:
    """Dependency-injected wrapper for manipulating and tracking the global state payload."""
    def __init__(self, is_dry_run: bool = False):
        self.state = AgentStateModel(is_dry_run=is_dry_run)
        
        # Bind trace_id automatically for all logs emitted using this context
        self.logger = logger.bind(trace_id=self.state.trace_id)
        self.logger.info("Agent State Initialized", extra={"status": "initialized"})

    def update_snapshot(self, snapshot: Dict[str, Any]):
        self.state.current_page_snapshot = snapshot
        self.logger.info("Page snapshot updated")

    def log_execution(self, action: str, status: Literal['success', 'failed', 'skipped'], details: str, target: Optional[str] = None):
        log_entry = ExecutionLog(action=action, status=status, details=details, target=target)
        self.state.execution_history.append(log_entry)
        
        self.logger.info(
            f"Execution: {action} -> {status} ({details})", 
            extra={
                "action": action,
                "status": status,
                "target": target,
                "step_id": self.state.current_step_index
            }
        )
        
    def increment_retry(self, key: str) -> int:
        if key not in self.state.retry_metrics:
            self.state.retry_metrics[key] = 0
        self.state.retry_metrics[key] += 1
        return self.state.retry_metrics[key]

    def set_status(self, new_status: Literal['initialized', 'running', 'failed', 'completed']):
        self.state.status = new_status
        self.logger.info(f"State transitioned to {new_status}", extra={"status": new_status})
    
    def get_context(self) -> Dict[str, Any]:
        return {
            "current_step_index": self.state.current_step_index,
            "total_steps": self.state.total_steps,
            "status": self.state.status,
            "is_dry_run": self.state.is_dry_run
        }
