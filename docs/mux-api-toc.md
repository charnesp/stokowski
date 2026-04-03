# Mux API v0.22.0 - Documentation

> **Source:** `api-mux.yaml` (OpenAPI spec)
> **Generated:** 2026-03-25
> **Purpose:** Migration guide for Symphony (stdio → HTTP API)

---

## Table des Matières

1. [Vue d'Ensemble](#1-vue-densemble)
2. [Authentification](#2-authentification)
3. [Endpoints Critiques pour Symphony](#3-endpoints-critiques-pour-symphony)
   - [Workspace Lifecycle](#31-workspace-lifecycle)
   - [Messaging & Tool Calls](#32-messaging--tool-calls)
   - [Monitoring & Info](#33-monitoring--info)
4. [Comparaison: stdio vs HTTP](#4-comparaison-stdio-vs-http)
5. [Questions Ouvertes](#5-questions-ouvertes)

---

## 1. Vue d'Ensemble

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MUX SERVER (remote)                              │
│                      localhost:9988                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   REST API                      WebSocket (future?)                  │
│   ════════════════              ═══════════════════════             │
│                                                                      │
│   POST /api/workspace/create    WS /api/sessions/:id/stream         │
│   POST /api/workspace/sendMessage                                    │
│   POST /api/workspace/answerDelegatedToolCall                       │
│   GET  /api/workspace/list                                         │
│   POST /api/workspace/interruptStream                               │
│   ...                                                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     SYMPHONY (Elixir)                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Avant (stdio):           Après (HTTP):                            │
│   ┌─────────┐              ┌─────────┐     ┌─────────────┐         │
│   │Orchestr-│◄── stdio ───►│  mux    │     │  HTTPoison  │         │
│   │ator     │  JSON msgs   │(local)  │     │   + Jason   │         │
│   └─────────┘              └─────────┘     └──────┬──────┘         │
│                                                     │                │
│                                                     ▼                │
│                                              ┌─────────────┐         │
│                                              │ Mux API     │         │
│                                              │ (remote)    │         │
│                                              └─────────────┘         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Base URL

```
/api
```

### Authentification

- **Type:** Bearer Token
- **Header:** `Authorization: Bearer <token>`
- **Token:** Configuré via `--auth-token` au démarrage du server Mux

---

## 2. Authentification

### `/server/getApiServerStatus` (ligne 607)

Vérifie si le server API est accessible.

**Request:** `POST /api/server/getApiServerStatus`

```json
{}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "running": true,
    "port": 9988
  }
}
```

### `/server/setApiServerSettings` (ligne 671)

Configure les settings du server.

**Request:**
```json
{
  "host": "0.0.0.0",
  "port": 9988,
  "authToken": "optional-token",
  "allowHttpOrigin": true
}
```

---

## 3. Endpoints Critiques pour Symphony

### 3.1 Workspace Lifecycle

#### `/workspace/list` (ligne 9597)

Liste tous les workspaces.

**Request:** `POST /api/workspace/list`
```json
{
  "archived": false  // optionnel
}
```

**Response:**
```json
[
  {
    "id": "abc123def4",
    "name": "plan-a1b2",
    "title": "Fix authentication bug",
    "projectName": "my-app",
    "projectPath": "/Users/charles/projects/my-app",
    "createdAt": "2026-03-25T10:00:00Z",
    "runtimeConfig": {
      "type": "worktree",
      "srcBaseDir": "~/.mux/src"
    },
    "aiSettings": {
      "model": "anthropic:claude-sonnet-4-5",
      "thinkingLevel": "medium"
    }
  }
]
```

---

#### `/workspace/create` (ligne 9956)

**⭐ CRITIQUE** - Crée un nouveau workspace.

**Request:** `POST /api/workspace/create`

```json
{
  "projectPath": "/Users/charles/projects/my-app",
  "branchName": "linear-ISSUE-123",
  "trunkBranch": "main",
  "title": "Fix login bug - ISSUE-123",
  "runtimeConfig": {
    "type": "worktree",
    "srcBaseDir": "~/.mux/src",
    "bgOutputDir": "/tmp/mux-bashes"
  },
  "sectionId": "optional-section-id"
}
```

**Options runtimeConfig:**

| Type | Champs requis | Description |
|------|---------------|-------------|
| `local` | `type`, `srcBaseDir` | Execution locale legacy |
| `local` | `type` seulement | Execution locale simple |
| `worktree` | `type`, `srcBaseDir` | ⭐ **Recommandé** - Git worktree isolé |
| `ssh` | `type`, `host`, `srcBaseDir` | Execution remote via SSH |
| `docker` | `type`, `image` | Container Docker |
| `devcontainer` | `type`, `configPath` | Dev container |

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "abc123def4",
    "name": "linear-issue-123",
    "title": "Fix login bug - ISSUE-123",
    "projectName": "my-app",
    "projectPath": "/Users/charles/projects/my-app",
    "createdAt": "2026-03-25T10:00:00Z",
    "pendingAutoTitle": false,
    "forkFamilyBaseName": "linear-issue-123"
  }
}
```

**Erreurs possibles:**
```json
{
  "success": false,
  "error": {
    "type": "runtime_start_failed",
    "message": "SSH connection failed"
  }
}
```

---

#### `/workspace/remove` (ligne 10942)

Supprime un workspace.

**Request:** `POST /api/workspace/remove`
```json
{
  "workspaceId": "abc123def4"
}
```

---

#### `/workspace/fork` (ligne 11511)

Fork un workspace existant (pour exploration/branching).

---

### 3.2 Messaging & Tool Calls

#### `/workspace/sendMessage` (ligne 11898)

**⭐ CRITIQUE** - Envoie un message et démarre un turn.

**Request:** `POST /api/workspace/sendMessage`

```json
{
  "workspaceId": "abc123def4",
  "message": "Fix the authentication bug in the login flow",
  "options": {
    "thinkingLevel": "medium",
    "model": "anthropic:claude-sonnet-4-5",
    "mode": "exec",
    "agentId": "default",
    "toolPolicy": [
      {
        "regex_match": "bash",
        "action": "enable"
      },
      {
        "regex_match": "file_edit_.*",
        "action": "enable"
      },
      {
        "regex_match": ".*",
        "action": "disable"
      }
    ],
    "additionalSystemInstructions": "You are working on Linear issue ISSUE-123...",
    "providerOptions": {
      "anthropic": {
        "cacheTtl": "5m"
      }
    }
  }
}
```

**Options détaillées:**

| Option | Type | Description |
|--------|------|-------------|
| `thinkingLevel` | enum | `off`, `low`, `medium`, `high`, `xhigh`, `max` |
| `model` | string | Format: `provider:model` (ex: `anthropic:claude-sonnet-4-5`) |
| `mode` | enum | `plan`, `exec`, `compact` |
| `agentId` | string | Agent à utiliser |
| `toolPolicy` | array | Filtres sur les outils disponibles |
| `additionalSystemInstructions` | string | Instructions système additionnelles |
| `maxOutputTokens` | number | Limite de tokens en sortie |
| `delegatedToolNames` | array | Outils à déléguer au client (ACP) |

**Response:**
```json
{
  "success": true,
  "data": {
    "turnId": "turn-xyz-789"
  }
}
```

**Erreurs:**
- `api_key_not_found` - Clé API provider manquante
- `oauth_not_connected` - OAuth non configuré
- `provider_disabled` - Provider désactivé
- `runtime_not_ready` - Runtime pas prêt
- `runtime_start_failed` - Échec démarrage runtime
- `policy_denied` - Policy refuse l'opération

---

#### `/workspace/answerDelegatedToolCall` (ligne 12351)

**⭐ CRITIQUE** - Répond à un tool call delegated.

**Request:** `POST /api/workspace/answerDelegatedToolCall`

```json
{
  "workspaceId": "abc123def4",
  "toolCallId": "tool-call-id-from-stream",
  "result": {
    "output": "Command output or file content..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {}
}
```

---

#### `/workspace/answerAskUserQuestion` (ligne 12302)

Répond à une question posée par l'agent à l'utilisateur.

**Request:**
```json
{
  "workspaceId": "abc123def4",
  "toolCallId": "question-id",
  "answers": {
    "confirmed": "yes",
    "filename": "auth.go"
  }
}
```

---

#### `/workspace/interruptStream` (ligne 12924)

Interrompt le turn en cours.

**Request:** `POST /api/workspace/interruptStream`

```json
{
  "workspaceId": "abc123def4",
  "options": {
    "soft": true,
    "abandonPartial": false,
    "sendQueuedImmediately": false
  }
}
```

| Option | Description |
|--------|-------------|
| `soft` | Interruption douce (permet de finir le turn actuel) |
| `abandonPartial` | Abandonne les réponses partielles |
| `sendQueuedImmediately` | Envoie immédiatement les messages en queue |

---

#### `/workspace/resumeStream` (ligne 12394)

Reprend un stream interrompu.

---

#### `/workspace/clearQueue` (ligne 12971)

Vide la queue de messages.

---

### 3.3 Monitoring & Info

#### `/workspace/getInfo` (ligne 13425)

**⭐ CRITIQUE** - Récupère les infos d'un workspace.

**Request:** `POST /api/workspace/getInfo`

```json
{
  "workspaceId": "abc123def4"
}
```

**Response:**
```json
{
  "id": "abc123def4",
  "name": "linear-issue-123",
  "title": "Fix login bug - ISSUE-123",
  "projectName": "my-app",
  "projectPath": "/Users/charles/projects/my-app",
  "createdAt": "2026-03-25T10:00:00Z",
  "runtimeConfig": {
    "type": "worktree",
    "srcBaseDir": "~/.mux/src",
    "bgOutputDir": "/tmp/mux-bashes"
  },
  "aiSettingsByAgent": {
    "default": {
      "model": "anthropic:claude-sonnet-4-5",
      "thinkingLevel": "medium"
    }
  }
}
```

---

#### `/workspace/stopRuntime` (ligne 11308)

Arrête le runtime d'un workspace.

```json
{
  "workspaceId": "abc123def4"
}
```

---

#### `/workspace/getRuntimeStatuses` (ligne 11346)

Statut des runtimes.

---

#### `/workspace/getFullReplay` (ligne 14128)

Historique complet d'un workspace (messages, tool calls, etc.).

---

#### `/workspace/getLastLlmRequest` (ligne 13787)

Dernière requête LLM envoyée (pour debugging).

---

#### `/workspace/stats/subscribe` (ligne 20872)

Souscrit aux statistiques en temps réel.

---

#### `/workspace/getSessionUsage` (ligne 20324)

Usage de la session (tokens, coût, etc.).

---

## 4. Comparaison: stdio vs HTTP

### Mapping des Concepts

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STDO (Codex App Server)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Communication:     Port stdio (JSON-RPC 2.0)                       │
│  Spawn:             Port.spawn/3                                     │
│  Messages:          JSON sur stdin/stdout                            │
│  Session ID:        Composite (thread_id + turn_id)                  │
│  Tool calls:        Via protocol (output-available)                 │
│  Errors:            Dans le JSON response                           │
│                                                                      │
│  Workflow:                                                         │
│  1. start_session → Port ouvert, init envoyé                       │
│  2. start_turn → thread.start + turn.start                          │
│  3. await_turn_completion → Lecture stdout en boucle                │
│  4. Tool calls → Pattern match sur le stream JSON                   │
│  5. stop_session → Port fermé                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         HTTP API                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Communication:     REST (HTTP POST) + WebSocket (futur)            │
│  Spawn:             POST /workspace/create                           │
│  Messages:          POST /workspace/sendMessage                      │
│  Session ID:        workspaceId (10 hex chars)                      │
│  Tool calls:        POST /workspace/answerDelegatedToolCall          │
│  Errors:            { success: false, error: {...} }                 │
│                                                                      │
│  Workflow:                                                          │
│  1. POST /workspace/create → { id, name, ... }                      │
│  2. POST /workspace/sendMessage → { turnId }                        │
│  3. [Polling ou WebSocket] → Réponses streaming                     │
│  4. POST /workspace/answerDelegatedToolCall → Réponse tool          │
│  5. POST /workspace/remove → Nettoyage                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Différences Clés

| Aspect | Stdio | HTTP API |
|--------|-------|----------|
| **Latence** | Minimale (IPC) | Network overhead |
| **Fiabilité** | Sensible aux crashs | Meilleure supervision |
| **Scalabilité** | Local only | Remote possible |
| **Tool calls** | Inline dans stream | Séparés (delegation) |
| **State management** | Implicite | Explicite (workspaceId) |
| **Streaming** | stdout continu | Polling ou WebSocket |

---

## 5. Architecture Code Symphony Actuel

### Code Actuel: `Codex.AppServer` (elixir/lib/symphony_elixir/codex/app_server.ex)

Le module actuel implémente le protocol JSON-RPC 2.0 sur stdio:

```elixir
defmodule SymphonyElixir.Codex.AppServer do
  # Session state
  defstruct [
    :port,           # Port (stdio)
    :metadata,       # PID info
    :approval_policy,
    :auto_approve_requests,
    :thread_sandbox,
    :turn_sandbox_policy,
    :thread_id,      # ← ID composite (workspace + thread)
    :workspace,
    :worker_host
  ]

  # Flow stdio:
  # 1. start_session → Port.open → initialize
  # 2. start_thread → thread/start
  # 3. run_turn → turn/start
  # 4. await_turn_completion → receive_loop
  # 5. Tool calls: "item/tool/call" → execute → send result
  # 6. stop_session → Port.close
end
```

### Flux JSON-RPC stdio:

```
SYMPHONY                          MUX (stdio)
   │                                  │
   │  ─── initialize ──────────────► │
   │  ◄── { id, capabilities } ───── │
   │  ─── initialized ──────────────► │
   │                                  │
   │  ─── thread/start ─────────────► │
   │  ◄── { thread: { id } } ──────── │
   │                                  │
   │  ─── turn/start ───────────────► │
   │  ◄── { turn: { id } } ────────── │
   │                                  │
   │  ◄─── streaming JSON ──────────── │
   │       { method: "item/tool/call",│
   │         id: "xxx",               │
   │         params: {...} }          │
   │                                  │
   │  ─── { id, result } ───────────► │
   │                                  │
   │  ◄─── ... continues ... ─────────│
   │                                  │
   │  ◄── { method: "turn/completed"} │
```

### Messages clés gérés:

| Message stdio | Direction | Action |
|---------------|-----------|--------|
| `initialize` | S → M | Init session |
| `initialized` | S → M | Confirme init |
| `thread/start` | S → M | Démarre thread |
| `turn/start` | S → M | Démarre turn |
| `item/tool/call` | M → S | Tool call |
| `item/commandExecution/requestApproval` | M → S | Approval |
| `turn/completed` | M → S | Turn fini |
| `turn/failed` | M → S | Erreur |
| `turn/cancelled` | M → S | Annulé |

---

## 6. Migration: stdio → HTTP

### Mapping Direct

| stdio (JSON-RPC) | HTTP API | Diff |
|------------------|----------|------|
| `Port.spawn` | `POST /workspace/create` | Process → HTTP |
| `initialize` | Auth header | - |
| `thread/start` | Session implicite | - |
| `turn/start` | `POST /workspace/sendMessage` | Composite → separate |
| `receive_loop` | Polling ou WebSocket | Sync → Async |
| `item/tool/call` | Via delegation | Inline → explicit |
| Tool result | `POST /workspace/answerDelegatedToolCall` | Implicit → explicit |
| `turn/completed` | Dans response | Aggregé → distribué |

### Nouveau Module: `MuxApi.Client`

```elixir
defmodule SymphonyElixir.MuxApi.Client do
  @moduledoc """
  Client HTTP pour l'API Mux distante.
  Remplace Codex.AppServer pour la communication stdio.
  """

  @base_url "http://localhost:9988/api"

  # Workspace lifecycle
  def create_workspace(config)
  def list_workspaces()
  def remove_workspace(workspace_id)

  # Messaging
  def send_message(workspace_id, message, opts \\ [])
  def answer_tool_call(workspace_id, tool_call_id, result)
  def interrupt_stream(workspace_id, opts \\ [])

  # Monitoring
  def get_workspace_info(workspace_id)
  def get_full_replay(workspace_id)
end
```

### Différences Architecture

```
AVANT (stdio):                          APRÈS (HTTP):
┌─────────┐                            ┌─────────┐
│Symphony │                            │Symphony │
└────┬────┘                            └────┬────┘
     │                                      │
     │ stdio (local)                        │ HTTP (remote)
     ▼                                      ▼
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐
│  Port   │────►│    mux     │     │ HTTPoison   │────►│  mux    │
│ (spawn) │◄────│  (local)   │     │             │◄────│ :9988   │
└─────────┘     └─────────────┘     └─────────────┘     └─────────┘
     │                                      │
     │                                     │
     ▼                                      ▼
 Synchro                              Async/Poll
 (blocking)
```

### Points de vigilance:

1. **Token auth** - Comment obtenir le bearer token ?
2. **Streaming** - Comment recevoir les tool calls en temps réel ?
3. **Timeout handling** - Changer de `receive_loop` à polling
4. **Tool delegation** - Configurer `delegatedToolNames` correctement
5. **Workspace path** - S'assurer que Mux crée le bon directory

---

## 7. Questions Ouvertes

### Streaming: `/workspace/onChat` (ligne 16202)

**⭐ CRITIQUE** - C'est le endpoint de streaming SSE !

**Request:** `POST /api/workspace/onChat`

```json
{
  "workspaceId": "abc123def4",
  "mode": {
    "type": "live"  // "full", "since", ou "live"
  }
}
```

**Response:** `text/event-stream`

**Events SSE:**

| Event Type | Description |
|------------|-------------|
| `heartbeat` | Keep-alive |
| `caught-up` | Sync point atteint |
| `stream-start` | Nouveau stream démarre |
| `stream-delta` | Texte en streaming (delta) |
| `stream-lifecycle` | Phase: idle, preparing, streaming, completing, interrupted, failed |
| `stream-error` | Erreur (avec errorType) |
| `stream-end` | Stream terminé |
| `stream-abort` | Stream avorté |
| `delete` | Message supprimé |

**Stream Delta (tool calls):**
```json
{
  "event": "message",
  "data": {
    "type": "stream-end",
    "workspaceId": "abc123def4",
    "messageId": "msg-xyz",
    "parts": [
      { "type": "text", "text": "Fixing..." },
      { "type": "dynamic-tool", "toolCallId": "tool-1", "toolName": "bash", "input": {...}, "state": "input-available" },
      { "type": "dynamic-tool", "toolCallId": "tool-1", "state": "output-available", "output": "result" }
    ],
    "metadata": {
      "model": "anthropic:claude-sonnet-4-5",
      "usage": { "inputTokens": 1000, "outputTokens": 500 }
    }
  }
}
```

### Non résolues dans l'API spec:

#### Résolues ✅

1. **Streaming responses** - **SSE confirmé !**
   - `POST /workspace/onChat` → `text/event-stream`
   - Events: `stream-start`, `stream-delta`, `stream-end`, etc.

2. **Tool calls** - **Dans `stream-end` / `parts`**
   - `{ type: "dynamic-tool", toolCallId, toolName, input, state, output }`
   - States: `input-available`, `output-available`, `output-redacted`

#### Encore ouvertes ❓

3. **Tool delegation** - Comment Mux sait-il quels tools sont delegated vs locaux ?
   - `delegatedToolNames` dans `sendMessage` - à tester

4. **Authentication token** - Comment obtenir le bearer token ?
   - `--print-auth-token` au démarrage du server Mux
   - Ou récupérer via config

5. **Workspace path** - Comment obtenir le path du workspace créé ?
   - Via `POST /workspace/getInfo` après création

### Prochaines étapes:

1. Lire `/workspace/activity/subscribe` (ligne 18276) - pour comprendre le streaming
2. Tester l'API avec `curl` pour voir les réponses réelles
3. Vérifier si WebSocket est disponible

---

## Annexe: Endpoints Complets

### Tous les endpoints workspace

| Endpoint | Ligne | Description |
|----------|-------|-------------|
| `/workspace/list` | 9597 | Lister workspaces |
| `/workspace/create` | 9956 | ⭐ Créer workspace |
| `/workspace/createMultiProject` | 10453 | Multi-projets |
| `/workspace/remove` | 10942 | Supprimer |
| `/workspace/updateAgentAISettings` | 10975 | Update AI settings |
| `/workspace/rename` | 11038 | Renommer |
| `/workspace/updateModeAISettings` | 11085 | Mode AI settings |
| `/workspace/updateTitle` | 11147 | Update title |
| `/workspace/regenerateTitle` | 11188 | Regenerer title |
| `/workspace/archive` | 11232 | Archiver |
| `/workspace/unarchive` | 11270 | Désarchiver |
| `/workspace/stopRuntime` | 11308 | Arrêter runtime |
| `/workspace/getRuntimeStatuses` | 11346 | Status runtimes |
| `/workspace/getProjectGitStatuses` | 11377 | Git status |
| `/workspace/fork` | 11511 | Fork workspace |
| `/workspace/sendMessage` | 11898 | ⭐ Envoyer message |
| `/workspace/answerAskUserQuestion` | 12302 | Répondre question |
| `/workspace/answerDelegatedToolCall` | 12351 | ⭐ Répondre tool call |
| `/workspace/resumeStream` | 12394 | Reprendre stream |
| `/workspace/interruptStream` | 12924 | ⭐ Interrompre |
| `/workspace/clearQueue` | 12971 | Vider queue |
| `/workspace/truncateHistory` | 13009 | Tronquer historique |
| `/workspace/replaceChatHistory` | 13049 | Remplacer historique |
| `/workspace/getDevcontainerInfo` | 13391 | Devcontainer info |
| `/workspace/getInfo` | 13425 | ⭐ Info workspace |
| `/workspace/getLastLlmRequest` | 13787 | Dernière requête LLM |
| `/workspace/getFullReplay` | 14128 | Historique complet |
| `/workspace/executeBash` | 15960 | Exécuter bash |
| `/workspace/onChat` | 16202 | Callback chat |
| `/workspace/activity/list` | 18185 | Liste activité |
| `/workspace/history/loadMore` | 18418 | Charger plus |
| `/workspace/getPlanContent` | 19949 | Contenu plan |
| `/workspace/backgroundBashes/*` | 19996+ | Bash background |
| `/workspace/getSessionUsage` | 20324 | Usage session |
| `/workspace/stats/subscribe` | 20872 | Subscribe stats |

### Endpoints NON pertinents pour Symphony

- `/tokenizer/*` - Comptage tokens (interne)
- `/splashScreens/*` - UI splash
- `/browser/*` - Navigation browser
- `/uiLayouts/*` - Layout UI
- `/agents/*` - Agents registry
- `/providers/*` - Config providers
- `/policy/*` - Policy management
- `/mcp/*` - MCP servers
- `/update/*` - Updates app
- `/voice/*` - Voice transcription
- `/onePassword/*` - 1Password
- `/ssh/*` - SSH prompts
