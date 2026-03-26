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
    
    def _build_command(self, prompt, session_id=None):
        """Build the CLI command for Claude Code."""
        cmd = [
            self.config.get("command", "claude"),
            "-p", prompt,
            "--output-format", "stream-json",
            "--verbose"
        ]
        
        if session_id:
            cmd.extend(["--resume", session_id])
        
        return cmd