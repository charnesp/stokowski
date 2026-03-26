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
        
        # Get model from config (support both dataclass and dict)
        if hasattr(self.config, 'model'):
            model = self.config.model
        else:
            model = self.config.get("model", "gpt-4")
        
        # Get API key from config
        api_key = getattr(self.config, 'api_key', '') if hasattr(self.config, 'api_key') else self.config.get('api_key', '')
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        try:
            async with httpx.AsyncClient() as client:
                # First create/get a workspace
                workspace_response = await client.post(
                    f"{self.endpoint}/api/workspace/create",
                    json={
                        "projectPath": "/tmp/stokowski-workspace",
                        "title": "Stokowski Task",
                        "runtimeConfig": {"type": "local"}
                    },
                    headers=headers,
                    timeout=30.0
                )
                workspace_response.raise_for_status()
                workspace_data = workspace_response.json()
                
                if not workspace_data.get("success"):
                    raise RunnerError(f"Failed to create workspace: {workspace_data}")
                
                workspace_id = workspace_data["data"]["id"]
                
                # Then send the message
                response = await client.post(
                    f"{self.endpoint}/api/workspace/sendMessage",
                    json={
                        "workspaceId": workspace_id,
                        "message": prompt,
                        "options": {
                            "model": model,
                            "mode": "exec",
                            "thinkingLevel": "medium"
                        }
                    },
                    timeout=300.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Call on_output if provided (for logging/debugging)
                if on_output:
                    on_output(str(data))
                
                return RunResult(
                    result=data.get("result", ""),
                    session_id=workspace_id,
                    input_tokens=0,  # Mux API doesn't return token counts directly
                    output_tokens=0,
                    total_tokens=0
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
        # Support both dataclass and dict config (for tests)
        if hasattr(self.config, 'model'):
            model = self.config.model
        else:
            model = self.config.get("model", "gpt-4")
        
        payload = {
            "prompt": prompt,
            "model": model,
        }
        
        if session_id:
            payload["parent_workspace_id"] = session_id
        
        return payload