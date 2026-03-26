"""Mux HTTP API runner implementation."""
from typing import Optional, Callable

import httpx

from .base import BaseRunner, RunResult, RunnerError


class MuxRunner(BaseRunner):
    """Runner for Mux HTTP API."""
    
    def __init__(self, config, endpoint="http://localhost:9988"):
        super().__init__(config)
        self.endpoint = endpoint.rstrip('/')
    
    async def run_turn(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        on_output: Optional[Callable[[str], None]] = None,
        on_pid: Optional[Callable[[int], None]] = None
    ) -> RunResult:
        """Execute a single turn via Mux HTTP API."""
        # Skip on_pid - no subprocess for HTTP API
        
        payload = self._build_payload(prompt, session_id)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.endpoint}/api/v1/tasks",
                    json=payload,
                    timeout=300.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Call on_output if provided (for logging/debugging)
                if on_output:
                    on_output(str(data))
                
                return RunResult(
                    result=data.get("result", ""),
                    session_id=data.get("workspace_id"),
                    input_tokens=data.get("input_tokens", 0),
                    output_tokens=data.get("output_tokens", 0),
                    total_tokens=data.get("total_tokens", 0)
                )
                
        except httpx.HTTPError as e:
            raise RunnerError(f"HTTP error: {e}")
        except Exception as e:
            raise RunnerError(f"Error calling Mux API: {e}")
    
    def supports_resume(self) -> bool:
        return True
    
    def get_name(self) -> str:
        return "mux"
    
    def _build_payload(self, prompt: str, session_id: Optional[str] = None) -> dict:
        """Build the HTTP payload for Mux API."""
        payload = {
            "prompt": prompt,
            "model": self.config.get("model", "gpt-4"),
        }
        
        if session_id:
            payload["parent_workspace_id"] = session_id
        
        return payload