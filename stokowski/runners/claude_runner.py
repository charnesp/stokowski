"""Claude Code CLI runner implementation."""
from .base import BaseRunner


class ClaudeRunner(BaseRunner):
    """Runner for Claude Code CLI."""
    
    def __init__(self, config):
        super().__init__(config)
    
    async def run_turn(self, prompt, session_id=None, on_output=None, on_pid=None):
        raise NotImplementedError("run_turn not yet implemented")
    
    def supports_resume(self):
        return True
    
    def get_name(self):
        return "claude"