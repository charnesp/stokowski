## Context

Stokowski assemble aujourd’hui un prompt en trois couches (global, stage, lifecycle) via `assemble_prompt()` ; le fichier `.stokowski/prompts/lifecycle.md` mêle le **contexte d’exécution** (issue, transitions, rework, `investigate`) et le **contrat de fin** (rapport `<stokowski:report>`, `## Commit Information`, commandes `git`, routage agent-gate). Le runner reçoit donc tout en une fois ; en fin de longue session, le modèle dégrade souvent la conformité au protocole de clôture.

## Goals / Non-Goals

**Goals:**

- Séparer clairement **pre-run** (tout ce qui aide pendant le travail) et **post-run** (tout ce qui verrouille la qualité du livrable textuel + Git).
- Faire exécuter au modèle un **second assemblage prompt** (tour de conversation dédié ou message utilisateur additionnel) contenant essentiellement le post-run, **après** le tour où l’agent a mené les tâches principales et **avant** que l’orchestrateur ne considère la sortie comme rapport final parsable.
- Conserver une **migration douce** : `lifecycle_prompt` continue de pointer vers le gabarit **pre-run** ; ajout d’une clé explicite pour le post-run avec défaut embarqué dans le dépôt.

**Non-Goals:**

- Changer le schéma XML du rapport ou les règles de parsing existantes (hors déplacement de texte entre fichiers).
- Réécrire entièrement la politique de session « resumed » (optimize-prompt-assembly) ; on l’étendra seulement si nécessaire pour le second tour.
- Imposer un nouveau moteur de templating (reste Jinja2).

## Decisions

1. **Deux fichiers Markdown, deux moments d’injection**  
   - **Pre-run** : inchangé dans le flux actuel — dernière couche de `assemble_prompt()` pour le tour « travail ».  
   - **Post-run** : nouveau chemin `lifecycle_post_run_prompt` (nom exact aligné sur le parseur YAML) avec défaut `prompts/lifecycle-post-run.md` à la racine du workflow (même règle de résolution relative que `lifecycle_prompt`).  
   - *Alternative écartée* : garder un seul fichier avec ancres Jinja2 et deux appels `render` sur le même fichier avec un flag `mode=pre|post` — rejetée car moins lisible pour les auteurs de prompts et plus fragile.

2. **Enchaînement orchestrateur : contrôlé par `post_run` sur l’état**  
   Après le premier tour runner, si l’état a **`post_run: true`** (valeur par défaut lorsque la clé est **absente** du YAML), l’orchestrateur envoie un **second prompt** minimal (post-run lifecycle + rappel ticket si besoin), sans réinjecter global/stage sauf exception documentée. Si **`post_run: false`**, un seul tour ; la sortie de ce tour sert au parsing canonique (rapport, routage).  
   - *Alternative écartée* : demander au modèle de s’arrêter mid-turn avec un tool — incompatible avec le flux CLI actuel.

3. **Contenu déplacé**  
   Lorsque **`post_run`** est **vrai**, les blocs normatifs « Structured Work Report », `## Commit Information`, exemples XML, checklists `git` et marqueurs agent-gate **quittent** le lifecycle **pre-run** et **vont** dans `lifecycle-post-run.md`. Lorsque **`post_run: false`** (cas typique **`agent-gate`**), ces éléments **restent** dans le **prompt de scène** (ex. `review-findings-route.md`) ; le pre-run reste centré contexte ticket / transitions / rappel compact si besoin.

4. **Compatibilité**  
   - Si `lifecycle_post_run_prompt` absent : utiliser le défaut du package / `.stokowski/prompts/lifecycle-post-run.md`.  
   - `lifecycle_prompt` reste la clé YAML existante pour le pre-run (alias documenté « pre-run » sans casser les dépôts).

5. **Tests**  
   Tests unitaires sur rendu des deux templates + test d’intégration (ou mock orchestrateur) vérifiant l’ordre : tour 1 sans contrat rapport dans le pre-run rendu ; tour 2 contient les chaînes obligatoires du contrat rapport.

6. **Périmètre post-run**  
   Tout état **`agent`** ou **`agent-gate`** invoqué par le runner peut en théorie avoir un second tour ; le défaut YAML est **`post_run` absent ⇒ `true`**. Les états **`gate`**, **`terminal`**, etc., hors runner, ne portent pas `post_run`. Un état comme **`investigate`** (`type: agent`, clé omise) a donc **post-run activé** par défaut.

7. **Images sur le tour post-run**  
   **Non** : le tour post-run **ne ré-ouvre pas** l’intégration des images issues des commentaires (pas de second passage `embed_images_in_prompt` / équivalent sur les pièces jointes commentaires). Le premier tour a déjà porté le contexte riche ; le second ne sert qu’à verrouiller rapport + Git.

8. **`agent-gate` : `post_run: false` explicite dans le YAML**  
   Les runs **`agent-gate`** typiques (ex. `review-findings-route`) restent **un seul** tour : le stage porte déjà rapport + routage + git/MR. Comme le **défaut** de `post_run` est **`true`** si la clé est absente, chaque état **`agent-gate`** du dépôt **doit** inclure **`post_run: false`** explicitement pour éviter un second tour involontaire. Un **`agent-gate` atypique** peut poser **`post_run: true`** pour réutiliser le même mécanisme que les `agent`. La **validation** exige que **`post_run` soit présent** sur tout état `agent-gate` (booléen explicite), afin que l’intention soit toujours lisible dans le fichier (pas d’ambiguïté « défaut true » sur un gate).

## Risks / Trade-offs

- **[Risque] Coût / latence** : deux appels modèle au lieu d’un → **Mitigation** : le second prompt est court (post-run + résumé minimal) ; documenter le surcoût pour les opérateurs.

- **[Risque] Friction auteurs de workflow** : deux fichiers à maintenir → **Mitigation** : défaut post-run fourni ; README et exemples mis à jour.

- **[Risque] Régressions parsing** : si le tour 1 produit déjà un `<stokowski:report>` partiel → **Mitigation** : l’orchestrateur ne parse le rapport définitif qu’à partir de la sortie du **tour post-run** (ou politique explicite dans les specs).

- **[Trade-off] Contexte partiel au tour 2** : le modèle ne revoit pas le stage prompt complet → **Mitigation** : variables Jinja2 de rappel (issue id, titre, objectifs initiaux) dans le gabarit post-run.

## Migration Plan

1. Ajouter `lifecycle-post-run.md` par défaut et la clé optionnelle dans le parseur.  
2. Retirer du `lifecycle.md` existant les sections rapport/Git ; vérifier les tests snapshot / prompt.  
3. Ajouter `post_run` sur `StateConfig`, défaut **`true`** si absent pour les états **`agent`** ; exiger **`post_run` présent** pour **`agent-gate`** et mettre **`post_run: false`** sur les gates typiques du dépôt. Brancher le second tour lorsque `post_run` est vrai.  
4. Documenter dans README / CLAUDE le flux pre → post.  
5. Rollback : feature flag ou revert du second tour si critique (à trancher en implémentation si le code expose déjà des flags).

## Questions résolues (cadrage)

- **Quels états reçoivent le post-run ?** — Tout état runner avec **`post_run: true`** (défaut **`true`** si la clé est omise sur **`agent`**). Les **`agent-gate`** typiques ont **`post_run: false`** écrit dans le YAML ; la validation exige la clé **`post_run`** pour chaque `agent-gate`. Hors périmètre : `gate`, `terminal`, etc.
- **Images dans le post-run ?** — **Non**, par décision produit : le gros du contexte (y compris images si activées au premier tour) est déjà consommé au premier tour ; le post-run reste léger et centré clôture rapport / Git.
