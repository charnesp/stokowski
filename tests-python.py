#!/usr/bin/env python3
"""Script de test complet pour gérer les workspaces Mux."""

import asyncio
import json
import sys
import uuid
from pathlib import Path

import httpx

API_KEY = "2919df08fffff32124c9eb991d35d511d5b62452091799e27eff14b38c6b6498"
ENDPOINT = "http://localhost:9988"


class MuxWorkspaceManager:
    def __init__(self, endpoint=ENDPOINT, api_key=API_KEY):
        self.endpoint = endpoint.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def list_workspaces(self):
        """Liste tous les workspaces."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint}/api/workspace/list", headers=self.headers, timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def create_workspace(self, project_path, title, branch_name=None, trunk_branch="main"):
        """Crée un workspace avec runtime worktree."""
        if branch_name is None:
            branch_name = f"test-{uuid.uuid4().hex[:8]}"

        # Calculer srcBaseDir à partir du default-dir: ${default-dir}../src
        default_dir = await self.get_default_project_dir()
        # Enlever les guillemets si présents
        default_dir = default_dir.strip('"')
        src_base_dir = str(Path(default_dir).parent / "src")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint}/api/workspace/create",
                json={
                    "projectPath": project_path,
                    "title": title,
                    "branchName": branch_name,
                    "trunkBranch": trunk_branch,
                    "runtimeConfig": {"type": "worktree", "srcBaseDir": src_base_dir},
                },
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def set_project_trust(self, project_path, trusted=True):
        """Trust/untrust un projet."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint}/api/projects/setTrust",
                json={"projectPath": project_path, "trusted": trusted},
                headers=self.headers,
                timeout=10.0,
            )
            return response.status_code == 200

    async def send_message(
        self, workspace_id, message, agent_id="exec", model="ollama:kimi-k2.5:cloud"
    ):
        """Envoie un message à un workspace."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint}/api/workspace/sendMessage",
                json={
                    "workspaceId": workspace_id,
                    "message": message,
                    "options": {
                        "agentId": agent_id,
                        "model": model,
                        "mode": "exec",
                        "thinkingLevel": "medium",
                    },
                },
                headers=self.headers,
                timeout=300.0,
            )
            response.raise_for_status()
            return response.json()

    async def list_projects(self):
        """Liste tous les projets."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint}/api/projects/list", headers=self.headers, timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def create_project(self, project_path, auto_trust=False):
        """Crée un nouveau projet avec option auto-trust."""
        # Auto-trust avant création si demandé
        if auto_trust:
            print(f"[Auto-trust] Trusting project: {project_path}")
            await self.set_project_trust(project_path, True)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint}/api/projects/create",
                json={"projectPath": project_path},
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_default_project_dir(self):
        """Récupère le répertoire de projet par défaut."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint}/api/projects/getDefaultProjectDir",
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            return response.text

    async def clone_project(self, repo_url, clone_parent_dir=None):
        """Clone un repository Git. Retourne un générateur d'événements SSE."""
        payload = {"repoUrl": repo_url}
        if clone_parent_dir:
            payload["cloneParentDir"] = clone_parent_dir

        async with (
            httpx.AsyncClient() as client,
            client.stream(
                "POST",
                f"{self.endpoint}/api/projects/clone",
                json=payload,
                headers=self.headers,
                timeout=300.0,
            ) as response,
        ):
            response.raise_for_status()

            # Parser les événements SSE
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]  # Enlever "data: "
                    try:
                        data = json.loads(data_str)
                        yield data
                    except json.JSONDecodeError:
                        continue


async def main():
    manager = MuxWorkspaceManager()

    if len(sys.argv) < 2:
        print("Usage: python mux_workspace_manager.py <command> [args]")
        print("\nCommands:")
        print("  list                                    - Liste tous les workspaces")
        print("  projects                                - Liste tous les projets")
        print(
            "  default-dir                             - Affiche le répertoire de projet par défaut"
        )
        print("  create-project <project_path> [auto] - Crée un nouveau projet (auto=trust)")
        print("  clone <repo_url> [parent_dir]         - Clone un repository Git")
        print("  create <project_path> <title>          - Crée un workspace")
        print("  trust <project_path>                    - Trust un projet")
        print("  send <workspace_id> <message>        - Envoie un message")
        print("  full <project_path>                   - Test complet (create + send)")
        return

    command = sys.argv[1]

    if command == "list":
        workspaces = await manager.list_workspaces()
        print(f"\n{len(workspaces)} workspaces trouvés:\n")
        for ws in workspaces:
            print(f"  ID: {ws['id']}")
            print(f"  Name: {ws['name']}")
            print(f"  Title: {ws.get('title', 'N/A')}")
            print(f"  Project: {ws['projectPath']}")
            print(f"  Runtime: {ws['runtimeConfig']['type']}")
            print("-" * 60)

    elif command == "projects":
        projects = await manager.list_projects()
        print(f"\n{len(projects)} projets trouvés:\n")
        for project_path, project_config in projects:
            trusted = project_config.get("trusted", False)
            workspaces_count = len(project_config.get("workspaces", []))
            print(f"  Path: {project_path}")
            print(f"  Trusted: {'✅' if trusted else '❌'}")
            print(f"  Workspaces: {workspaces_count}")
            print("-" * 60)

    elif command == "default-dir":
        default_dir = await manager.get_default_project_dir()
        print(f"Répertoire de projet par défaut: {default_dir}")

    elif command == "create-project" and len(sys.argv) >= 3:
        project_path = sys.argv[2]
        auto_trust = len(sys.argv) > 3 and sys.argv[3] == "auto"
        print(f"Création du projet: {project_path}")
        result = await manager.create_project(project_path, auto_trust=auto_trust)
        print(json.dumps(result, indent=2))

    elif command == "clone" and len(sys.argv) >= 3:
        repo_url = sys.argv[2]
        parent_dir = sys.argv[3] if len(sys.argv) > 3 else None

        print(f"Clonage de {repo_url}...")
        if parent_dir:
            print(f"Dans: {parent_dir}")
        print("-" * 60)

        cloned_path = None
        async for event in manager.clone_project(repo_url, parent_dir):
            if event.get("type") == "progress":
                print(event.get("line", ""), end="")
            elif event.get("type") == "success":
                cloned_path = event.get("normalizedPath")
                print("\n✅ Projet cloné avec succès!")
                print(f"   Chemin: {cloned_path}")
            elif event.get("type") == "error":
                print(f"\n❌ Erreur: {event.get('error')}")

    elif command == "create" and len(sys.argv) >= 4:
        project_path = sys.argv[2]
        title = sys.argv[3]

        result = await manager.create_workspace(project_path, title)
        print(json.dumps(result, indent=2))

    elif command == "trust" and len(sys.argv) >= 3:
        project_path = sys.argv[2]
        success = await manager.set_project_trust(project_path, True)
        print(f"Trust {'réussi' if success else 'échoué'}")

    elif command == "send" and len(sys.argv) >= 4:
        workspace_id = sys.argv[2]
        message = sys.argv[3]
        result = await manager.send_message(workspace_id, message)
        print(json.dumps(result, indent=2))

    elif command == "full" and len(sys.argv) >= 3:
        project_path = sys.argv[2]

        print("=" * 60)
        print("TEST COMPLET: Create + Trust + Send")
        print("=" * 60)

        # Étape 1: Créer avec auto-trust
        print(f"\n1. Création workspace sur {project_path} avec auto-trust...")
        result = await manager.create_workspace(project_path, "Test Auto", auto_trust=True)
        print(f"   Résultat: {json.dumps(result, indent=2)}")

        if result.get("success"):
            workspace_id = result["metadata"]["id"]
            project_path_from_response = result["metadata"]["projectPath"]
            print(f"\n   ✅ Workspace créé: {workspace_id}")
            print(f"   📁 Project path (de la réponse): {project_path_from_response}")

            # Étape 2: Envoyer un message
            print(f"\n2. Envoi message au workspace {workspace_id}...")
            msg_result = await manager.send_message(workspace_id, "Echo 'Hello from test'")
            print(f"   Résultat: {json.dumps(msg_result, indent=2)}")
        else:
            print(f"\n   ❌ Échec: {result}")

    else:
        print("Commande invalide ou arguments manquants")


if __name__ == "__main__":
    asyncio.run(main())
