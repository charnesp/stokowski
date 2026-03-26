"""Base runner module with abstract interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class RunResult:
    """Result of a single agent turn execution."""
    result: str
    session_id: Optional[str]
    input_tokens: int
    output_tokens: int
    total_tokens: int


class RunnerError(Exception):
    """Base exception for runner errors."""
    pass


class RunnerTimeout(RunnerError):
    """Raised when a runner operation times out."""
    pass


class RunnerConnectionError(RunnerError):
    """Raised when a runner cannot connect to its backend."""
    pass


class BaseRunner(ABC):
    """Abstract base class for all runners."""
    
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    async def run_turn(self, prompt, session_id=None, on_output=None, on_pid=None):
        """Execute a single turn."""
        pass
    
    @abstractmethod
    def supports_resume(self):
        """Whether this runner supports multi-turn sessions."""
        pass
    
    @abstractmethod
    def get_name(self):
        """Return the runner name."""
        pass