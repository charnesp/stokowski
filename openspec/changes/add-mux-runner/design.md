# Technical Design: Add Mux Runner

## Overview

Refactor the runner system to support a modular architecture with an abstract `BaseRunner` class and concrete implementations for Claude (CLI) and Mux (HTTP API).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    orchestrator.py                          │
│  ┌─────────────┐    ┌─────────────────┐                    │
│  │ RunAttempt  │───▶│ RunnerFactory   │                    │
│  └─────────────┘    │   .create()       │                    │
│                     └────────┬────────┘                    │
└──────────────────────────────┼──────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
    ┌────────────┐      ┌──────────────┐     ┌──────────┐
    │BaseRunner  │◄────│ ClaudeRunner │     │MuxRunner │
    │(abstract)  │      │  (CLI)       │     │  (HTTP)  │
    └────────────┘      └──────────────┘     └────┬─────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │  Mux API     │
                                          │  (external)  │
                                          └──────────────┘
```

## Components

### 1. BaseRunner (Abstract)

**Description:** Classe abstraite définissant l'interface commune pour tous les runners. Elle définit les méthodes abstraites que chaque implémentation concrète doit fournir :
- `run_turn()`: Exécute un tour d'agent avec le prompt donné, retourne le résultat encapsulé dans RunResult
- `supports_resume()`: Indique si le runner supporte les sessions multi-tours
- `get_name()`: Retourne l'identifiant du runner ("claude" ou "mux")

**RunResult:** Dataclass pour encapsuler le résultat d'un tour d'exécution, contenant le texte résultat, l'ID de session, et les métriques de tokens.

### 2. ClaudeRunner

**Description:** Implémentation utilisant l'exécution en ligne de commande via subprocess. Lance le CLI Claude Code avec les arguments appropriés, capture la sortie NDJSON en streaming, et parse les événements pour extraire le résultat et les métadonnées.

### 3. MuxRunner

**Description:** Implémentation utilisant des appels HTTP à l'API Mux. Envoie des requêtes POST à l'endpoint des tâches, gère le streaming de la réponse (SSE ou chunked), et extrait le résultat et les métriques de la réponse JSON.

### 4. RunnerFactory

**Description:** Pattern factory pour instancier dynamiquement le bon runner selon la configuration. Maintient un registre des types de runners disponibles et crée l'instance appropriée en injectant les dépendances nécessaires (configuration, endpoint Mux si applicable). Lève une erreur si le type de runner demandé n'est pas reconnu.

## Data Flow

### ClaudeRunner
1. Build CLI args with optional --resume
2. Create subprocess with asyncio
3. Stream stdout (NDJSON)
4. Parse events: assistant, tool_use, result
5. Extract session_id from result event
6. Return RunResult

### MuxRunner
1. Build HTTP payload with prompt, model, parent_workspace_id
2. POST to /api/v1/tasks
3. Stream response (SSE or chunked)
4. Parse events similar to Claude NDJSON
5. Extract workspace_id from response
6. Return RunResult

## Error Handling

- ClaudeRunner: Subprocess exit codes, timeouts, parse errors
- MuxRunner: HTTP errors, connection errors, timeouts

## Configuration

```yaml
states:
  coding:
    type: agent
    runner: mux
    mux:
      endpoint: http://localhost:9988
```

## Testing Strategy

1. Unit tests for each runner with mocks
2. Factory creation tests
3. Integration tests with real workflow