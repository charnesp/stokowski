"""Claude Code CLI runner implementation."""
import asyncio
import json
from datetime import datetime, timezone
from typing import Optional, Callable

from .base import BaseRunner, RunResult


class ClaudeRunner(BaseRunner):
    """Runner for Claude Code CLI."""
    
    def __init__(self, config):
        super().__init__(config)
    
    async def run_turn(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        on_output: Optional[Callable[[str], None]] = None,
        on_pid: Optional[Callable[[int], None]] = None
    ) -> RunResult:
        """Execute a single Claude Code turn."""
        cmd = self._build_command(prompt, session_id)
        
        # Create subprocess
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True
        )
        
        if on_pid and proc.pid:
            on_pid(proc.pid)
        
        # Parse streaming output
        result_data = await self._stream_output(proc, on_output)
        
        return RunResult(
            result=result_data.get("result", ""),
            session_id=result_data.get("session_id"),
            input_tokens=result_data.get("input_tokens", 0),
            output_tokens=result_data.get("output_tokens", 0),
            total_tokens=result_data.get("total_tokens", 0)
        )
    
    async def _stream_output(
        self,
        proc: asyncio.subprocess.Process,
        on_output: Optional[Callable[[str], None]]
    ) -> dict:
        """Stream and parse NDJSON output."""
        result_data = {
            "result": "",
            "session_id": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }
        
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            
            line_str = line.decode().strip()
            if not line_str:
                continue
            
            if on_output:
                on_output(line_str)
            
            try:
                event = json.loads(line_str)
                self._process_event(event, result_data)
            except json.JSONDecodeError:
                continue
        
        await proc.wait()
        return result_data
    
    def _process_event(self, event: dict, result_data: dict):
        """Process a single NDJSON event."""
        event_type = event.get("type", "")
        
        if event_type == "result":
            result_data["session_id"] = event.get("session_id")
            result_data["result"] = event.get("result", "")
            
            usage = event.get("usage", {})
            result_data["input_tokens"] = usage.get("input_tokens", 0)
            result_data["output_tokens"] = usage.get("output_tokens", 0)
            result_data["total_tokens"] = usage.get("total_tokens", 0)
    
    def supports_resume(self) -> bool:
        return True
    
    def get_name(self) -> str:
        return "claude"
    
    def _build_command(self, prompt: str, session_id: Optional[str] = None) -> list:
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