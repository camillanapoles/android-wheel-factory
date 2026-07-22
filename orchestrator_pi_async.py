#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
AGENTIC-ORCHESTRATOR ASYNC + EMBEDDED PI-CODING AGENT (CI/CD RUNTIME)
'''

import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

WORKSPACE = Path.cwd()
STATE_FILE = WORKSPACE / ".agentic_state_async.json"
LOG_FILE = WORKSPACE / "orchestrator_pi_async.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger("AGENTIC-CI-ORCHESTRATOR")

async def load_state_async() -> Dict[str, Any]:
    if STATE_FILE.exists():
        def _read():
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return await asyncio.to_thread(_read)
    return {"sdk_version": "1.0.0", "phase": "INIT", "status": "RUNNING"}

async def save_state_async(state: Dict[str, Any]):
    state["updated_at"] = datetime.now().isoformat()
    def _write():
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    await asyncio.to_thread(_write)

async def verify_pi_cli_async() -> bool:
    try:
        process = await asyncio.create_subprocess_exec(
            "pi", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return process.returncode == 0
    except FileNotFoundError:
        return False

async def phase_act_embedded_pi_async(prompt_task: str) -> bool:
    logger.info("=== FASE ACT (CI/CD RUNTIME): Acionando Pi Coding Agent ===")
    
    cmd = [
        "pi", 
        "-p", prompt_task, 
        "--tools", "read,write,edit,bash",
        "--no-interactive"
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(WORKSPACE),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )
    
    if process.stdout:
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            print(f"[PI-CI-RUNNER] {line.decode('utf-8', errors='ignore').strip()}")
            
    await process.wait()
    return process.returncode == 0

async def main_async():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', '-p', type=str, required=True)
    args = parser.parse_args()

    if not await verify_pi_cli_async():
        logger.error("Pi CLI não encontrada no runner.")
        sys.exit(1)

    state = await load_state_async()
    state['phase'] = 'ACT'
    await save_state_async(state)

    success = await phase_act_embedded_pi_async(args.prompt)
    if success:
        state['status'] = 'SUCCESS'
        await save_state_async(state)
        logger.info("=== PIPELINE CI/CD CONCLUÍDO COM SUCESSO ===")
    else:
        state['status'] = 'FAILED'
        await save_state_async(state)
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main_async())
