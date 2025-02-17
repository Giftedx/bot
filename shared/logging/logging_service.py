import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
import traceback

class LoggingService:
    """Centralized logging service with structured logging support"""
    
    def __init__(self, service_name: str, log_level: str = "INFO"):
        self.service_name = service_name
        self.logger = self._setup_logger(log_level)
        self.audit_logger = self._setup_audit_logger()
    
    def _setup_logger(self, log_level: str) -> logging.Logger:
        """Setup the main application logger"""
        logger = logging.getLogger(self.service_name)
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create logs directory if it doesn't exist
        Path("logs").mkdir(exist_ok=True)
        
        # File handler for all logs
        file_handler = logging.FileHandler(f"logs/{self.service_name}.log")
        file_handler.setFormatter(self._get_formatter())
        logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.FileHandler(f"logs/{self.service_name}_error.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self._get_formatter())
        logger.addHandler(error_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self._get_formatter())
        logger.addHandler(console_handler)
        
        return logger
    
    def _setup_audit_logger(self) -> logging.Logger:
        """Setup the audit logger for tracking important operations"""
        audit_logger = logging.getLogger(f"{self.service_name}_audit")
        audit_logger.setLevel(logging.INFO)
        
        # Create audit log file handler
        audit_handler = logging.FileHandler(f"logs/{self.service_name}_audit.log")
        audit_handler.setFormatter(self._get_formatter())
        audit_logger.addHandler(audit_handler)
        
        return audit_logger
    
    def _get_formatter(self) -> logging.Formatter:
        """Get the log formatter"""
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _format_log(self, message: str, extra: Optional[Dict[str, Any]] = None) -> str:
        """Format log message with extra data as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "message": message
        }
        if extra:
            log_data.update(extra)
        return json.dumps(log_data)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log an info message"""
        self.logger.info(self._format_log(message, extra))
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log a warning message"""
        self.logger.warning(self._format_log(message, extra))
    
    def error(self, message: str, error: Optional[Exception] = None, extra: Optional[Dict[str, Any]] = None):
        """Log an error message with optional exception details"""
        log_data = extra or {}
        if error:
            log_data.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "stacktrace": traceback.format_exc()
            })
        self.logger.error(self._format_log(message, log_data))
    
    def critical(self, message: str, error: Optional[Exception] = None, extra: Optional[Dict[str, Any]] = None):
        """Log a critical error"""
        log_data = extra or {}
        if error:
            log_data.update({
                "error_type": type(error).__name__,
                "error_message": str(error),
                "stacktrace": traceback.format_exc()
            })
        self.logger.critical(self._format_log(message, log_data))
    
    def audit_log(self, action: str, user_id: str, details: Dict[str, Any]):
        """Log an audit event"""
        audit_data = {
            "action": action,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            **details
        }
        self.audit_logger.info(json.dumps(audit_data))
    
    def performance_log(self, operation: str, duration_ms: float, extra: Optional[Dict[str, Any]] = None):
        """Log performance metrics"""
        perf_data = {
            "operation": operation,
            "duration_ms": duration_ms,
            **(extra or {})
        }
        self.info("Performance metric", perf_data)
    
    def security_log(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """Log security-related events"""
        security_data = {
            "event_type": event_type,
            "user_id": user_id,
            **details
        }
        self.audit_logger.info(self._format_log("Security event", security_data)) 