"""Mux HTTP API runner implementation."""
from .base import BaseRunner


class MuxRunner(BaseRunner):
    """Runner for Mux HTTP API."""
    
    def __init__(self, config, endpoint="http://localhost:9988"):
        super().__init__(config)
        self.endpoint = endpoint.rstrip('/')
    
    async def run_turn(self, prompt, session_id=None, on_output=None, on_pid=None):
        raise NotImplementedError("run_turn not yet implemented")
    
    def supports_resume(self):
        return True
    
    def get_name(self):
        return "mux"
    
    def _build_payload(self, prompt, session_id=None):
        """Build the HTTP payload for Mux API."""
        payload = {
            "prompt": prompt,
            "model": self.config.get("model", "gpt-4"),
        }
        
        if session_id:
            payload["parent_workspace_id"] = session_id
        
        return payload