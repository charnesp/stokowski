"""Runner factory module."""
from typing import Dict, Type

from .base import BaseRunner


class RunnerFactory:
    """Factory for creating runner instances."""
    
    _runners: Dict[str, Type[BaseRunner]] = {}
    
    @classmethod
    def create(cls, runner_type: str, config, **kwargs) -> BaseRunner:
        """Create a runner instance of the specified type."""
        if runner_type not in cls._runners:
            raise ValueError(f"Unknown runner type: {runner_type}")
        
        runner_class = cls._runners[runner_type]
        return runner_class(config)
    
    @classmethod
    def register(cls, name: str, runner_class: Type[BaseRunner]):
        """Register a runner class."""
        cls._runners[name] = runner_class