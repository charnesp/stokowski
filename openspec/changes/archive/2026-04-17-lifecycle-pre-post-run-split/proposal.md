## Why

Les agents qui enchaînent une longue session d’implémentation oublient souvent le contexte initial et les contrats de fin de tour (rapport structuré, commandes `git`, informations de commit). Aujourd’hui, ces exigences sont mélangées dans un seul gabarit `lifecycle.md` avec le contexte métier (ticket, transitions, rework), ce qui dilue l’attention au moment où le modèle doit surtout se conformer au protocole de clôture.

## What Changes

- Scinder le **lifecycle** en **pre-run** (contexte d’exécution) et **post-run** (clôture rapport / Git / routage le cas échéant) lorsque l’état a **`post_run: true`** (défaut pour **`agent`** si la clé est omise). Les **`agent-gate`** typiques ont **`post_run: false`** explicite et gardent le contrat dans le prompt de scène (ex. `review-findings-route.md`) ; un gate atypique peut poser **`post_run: true`**.
- Renommer ou repositionner le fichier / la clé de configuration pour refléter le **pre-run** (ex. `lifecycle_pre_run_prompt` ou fichier `lifecycle-pre-run.md`), en conservant une **compatibilité descendante** avec `lifecycle_prompt` mappé sur le pre-run tant que la migration n’est pas obligatoire.
- Introduire un booléen **`post_run`** par état (`agent` / `agent-gate`) : **défaut `true`** si la clé est **absente** sur les états **`agent`** ; second tour post-run lorsque `post_run` est vrai. Les **`agent-gate`** typiques posent **`post_run: false`** explicitement ; la **validation** exige la présence de **`post_run`** sur tout `agent-gate` pour lever toute ambiguïté.
- Mettre à jour les prompts par défaut du dépôt (ex. `.stokowski/prompts/`) et la documentation pour décrire la séquence pre → travail → post.

## Capabilities

### New Capabilities

- `lifecycle-post-run`: Comportement attendu du second gabarit (contenu minimal obligatoire, moment d’injection dans le flux agent, interaction avec la session / reprise de contexte clé).

### Modified Capabilities

- `lifecycle-template`: Le gabarit injecté pendant le **travail** ne porte plus les exigences de rapport/commit ; elles sont déplacées vers le post-run. Variables Jinja2 et contraintes d’externalisation restent alignées avec l’existant.
- `workflow-config`: Extension de `PromptsConfig` pour le gabarit post-run ; extension de **`StateConfig`** avec **`post_run`** (défaut agent / validation agent-gate).

## Impact

- `stokowski/prompt.py` — `assemble_prompt` et/ou nouvelle fonction d’assemblage pour le tour post-run ; contexte Jinja2 éventuellement enrichi pour « rappel » synthétique du ticket.
- `stokowski/config.py` — parsing YAML des prompts workflow / racine et du champ **`post_run`** par état + règles de validation.
- `stokowski/orchestrator.py` (ou couche d’invocation du runner) — enchaînement d’un second message utilisateur / tour dédié post-fin de tâches, avant parsing du `<stokowski:report>`.
- `.stokowski/workflow.yaml`, `.stokowski/prompts/lifecycle*.md` — découpage des fichiers et chemins.
- `tests/test_prompt.py`, tests orchestrateur — couverture des deux assemblages et de l’ordre d’injection.
