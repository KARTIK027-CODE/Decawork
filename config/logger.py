import sys
from loguru import logger
import json

def json_formatter(record):
    """Formats loguru records as structured JSON."""
    log_record = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "trace_id": record["extra"].get("trace_id", "unknown"),
        "step_id": record["extra"].get("step_id", None),
        "action": record["extra"].get("action", None),
        "target": record["extra"].get("target", None),
        "status": record["extra"].get("status", None),
        "retry_count": record["extra"].get("retry_count", 0),
        "error_message": str(record["exception"]) if record["exception"] else None,
        "context": record["extra"].get("context", {})
    }
    record["extra"]["serialized"] = json.dumps(log_record)
    return "{extra[serialized]}\\n"

def setup_logger():
    # Remove default handlers
    logger.remove()
    logger.configure(extra={"trace_id": "system"})
    
    # Add JSON file handler
    logger.add(
        "logs/agent_execution.json",
        format=json_formatter,
        level="INFO",
        rotation="100 MB"
    )
    
    # Console handler (human readable for debugging)
    logger.add(
        sys.stdout, 
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[trace_id]}</cyan> | <level>{message}</level>",
        level="INFO"
    )

setup_logger()
