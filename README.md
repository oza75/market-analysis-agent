# Market Analyst Agent

Agent d'analyse de marché utilisant Google ADK. Pour un produit donné, il recherche les prix sur plusieurs plateformes, analyse les avis clients et les tendances, puis génère un rapport structuré en markdown.

---

## Setup

### 1. Configurer les variables d'environnement

Copiez le fichier `analyst_agent/.env.example` et renommez-le `analyst_agent/.env`. L'application utilise 2 variables d'environnement. Vous recevrez les clés d'API par email, mais vous pouvez également utiliser les vôtres.

```dotenv
OPENROUTER_API_KEY=...
TAVILY_API_KEY=...
```

### 2. Démarrer l'application

**Interface web**

```bash
docker compose up
```

L'interface web de Google ADK est accessible sur [http://localhost:8000](http://localhost:8000).

**Serveur API (FastAPI)**

```bash
docker compose run --rm --service-ports app adk api_server analyst_agent
```

Le serveur FastAPI est accessible sur [http://localhost:8000](http://localhost:8000) et expose les endpoints REST d'ADK pour interagir avec l'agent de manière programmatique.

Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Architecture

L'architecture repose sur Google ADK avec OpenRouter pour les modèles. 

Le choix de Google ADK est principalement motivé par la facilité de déployer en production par rapport à d'autres outils comme LangGraph. Google ADK offre également une expérience de développement plus agréable, avec une API moins verbeuse.

Pour ce qui est d'OpenRouter, il fournit une API unifiée donnant accès à l'ensemble des modèles LLM, qu'ils soient propriétaires ou open source. Cela offre une flexibilité en développement (possibilité de changer de modèle rapidement) ainsi qu'une pérennité à long terme (à la sortie d'un nouveau modèle plus performant, le basculement est simple, sans modification d'infrastructure).

### Agents & Outils

L'architecture repose sur un orchestrateur principal, trois sous-agents spécialisés exposés comme outils (`AgentTool`), et trois outils fonctionnels.

#### Agents

**`market_analyst_agent`** est l'orchestrateur. Il vérifie que la demande concerne bien une analyse de marché, coordonne les recherches de prix, délègue l'analyse des avis et des tendances aux autres sous-agents, puis transfère l'ensemble du contexte au `report_generator` pour générer le rapport final.

**`review_analyst`** recherche sur le web des avis clients (Reddit, forums, acheteurs vérifiés) et produit deux types d'insights : ceux liés au produit (points forts et points faibles) et ceux liés à la plateforme (fiabilité, livraison, retours).

**`trend_analyzer`** analyse l'évolution du prix et de la popularité du produit sur les douze dernières semaines et formule une recommandation d'achat.

**`report_generator`** lit le contexte de la conversation (prix, avis, tendances déjà collectés) et le met en forme dans un rapport structuré.

### Outils

| Outil | Type | Description |
|---|---|---|
| `web_search` | Tavily Search API | Recherche web généraliste utilisée par l'orchestrateur et le `review_analyst` |
| `get_price_trend` | Mock déterministe | Série temporelle de prix sur N semaines, seedée par le nom du produit |
| `get_popularity_trend` | Mock déterministe | Score d'intérêt hebdomadaire (0–100) sur N semaines, seedé par le nom du produit |

J'ai choisi Tavily car elle est conçue pour être intégrée avec des agents LLM. Contrairement à une recherche web classique, elle renvoie directement un **extrait de contenu ciblé et contextuel**, ce qui évite de télécharger les pages HTML, de les analyser, ou d'injecter de larges blocs de contenu brut dans le contexte du modèle. Au final : moins de tokens consommés et une information plus exploitable.

---

## Architecture de données et stockage

| Donnée | Stockage |
|---|---|
| Résultats d'analyse | PostgreSQL |
| Rapports générés | Fichiers Markdown |
| Cache | Redis |
| Traçabilité des exécutions | Arize AX |
| Configuration des agents | Fichiers YAML |

**Résultats d'analyse :** PostgreSQL serait idéal pour ce type de données. La table pourrait être structurée comme suit :

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID | Identifiant unique de l'analyse |
| `user_id` | TEXT | Identifiant de l'utilisateur |
| `product_name` | TEXT | Produit analysé |
| `report_path` | TEXT | Chemin vers le fichier Markdown |
| `created_at` | TIMESTAMPTZ | Horodatage de la création |

**Rapports d'analyse :** Le rapport est un document texte long. Le stocker séparément de la base de données permettrait d'alléger celle-ci. Si un besoin de recherche textuelle sur les rapports émergeait, il serait toujours possible de les rapatrier dans PostgreSQL via une colonne `TEXT`.

**Cache :** Les appels aux outils externes (example: Tavily) sont les opérations les plus lentes et les plus coûteuses du workflow. Redis permettrait de les mettre en cache avec un TTL, de sorte que deux analyses du même produit à quelques minutes d'intervalle ne déclencheraient pas deux séries d'appels API identiques.

**Traçabilité :** Cet agent est plus un workflow, qu'un chatbot. Une fois le rapport généré, la session est terminée et il n'y a pas de conversation à reprendre. En revanche, pouvoir rejouer une exécution pour comprendre pourquoi un rapport est incorrect est essentiel. Arize AX pourrait jouer ce rôle en traçant et analysant les différents runs.

**Configuration :** Le modèle, le prompt, la température et les autres paramètres de chaque agent pourraient être définis dans des fichiers YAML versionnés dans le dépôt Git. Ces fichiers seraient chargés au démarrage et transmis aux différents agents. Tout changement passerait par une pull request et pourrait être annulé via un simple revert en cas de régression.

---

## Monitoring et observabilité

| Métrique | Description |
|---|---|
| Latence end-to-end par run | Détecte les dégradations globales du workflow |
| Latence par outil | Identifie quel outil est le goulot d'étranglement |
| Taux d'erreur par outil | Détecte les pannes ou dégradations des dépendances externes |
| Token usage (input + output) | Permet de suivre et anticiper les coûts LLM |
| Hallucination | Les prix, URLs et données du rapport sont-ils ancrés dans les sources collectées, ou inventés par le LLM ? |
| Groundedness | Chaque affirmation du rapport peut-elle être tracée jusqu'à un résultat de recherche ou une donnée d'outil réelle ? |
| Completeness | Le rapport contient-il toutes les sections attendues (prix, tendances, avis, recommandation d'achat) ? |
| Coherence | Le trend déclaré dans le texte est-il cohérent avec les données numériques retournées par `trend_analyzer` ? |

[**Arize AX**](https://arize.com/docs/ax) serait l'outil de monitoring et d'observabilité. Il couvre nativement les quatre dimensions du monitoring d'un système d'agents : le tracing des exécutions, la collecte de métriques de performance, l'alerting en cas de dysfonctionnement, et l'évaluation de la qualité des outputs via ses *online evaluators*, qui analysent automatiquement chaque rapport généré à chaque run. C'est ce dernier point qui justifie le choix d'Arize AX plutôt qu'un outil de monitoring généraliste comme MLFlow.

Il s'intègre aussi nativement avec Google ADK, ce qui signifie que chaque run, chaque appel d'outil et chaque sous-agent est tracé automatiquement sans instrumentation manuelle.

---

## Scaling et optimisation

**Pics de charge:** Vue que la génération d'un rapport peut être vue comme une tâche asynchrone (on ne s'attend pas à une réponse en temps réel), nous pourrions utiliser une architecture par queue. Sur GCP, **Cloud Tasks** permettrait d'enfiler chaque demande d'analyse, qui serait consommée par des workers **Cloud Run**. Le nombre de workers pourrait être scalé dynamiquement en fonction de la profondeur de la queue, ce qui absorberait les pics de charge sans saturer les APIs externes.

**Optimisation des coûts LLM:** Les instructions de chaque agent (system prompt + fichier de prompt Markdown) sont statiques et représentent une part importante des tokens envoyés à chaque appel. Ça fait donc un cas d'usage idéal pour le **prompt caching**, qui permettrait de mettre en cache cette partie fixe côté provider et de réduire les coûts à chaque run.

**Cache des résultats:** Si un utilisateur demande une analyse d'un produit déjà traité récemment, il n'est pas nécessaire de relancer le workflow complet. En vérifiant en base si une entrée récente existe pour le même `product_name`, on pourrait retourner directement le fichier Markdown existant, ce qui optimiserait encore plus les coûts.

**Parallélisation:** ADK supporte par défaut la parallélisation des outils et des sous-agents. `review_analyst`, `trend_analyzer` et les recherches de prix s'exécutent déjà en parallèle au sein d'un même run, sans infrastructure supplémentaire.

---

## Amélioration continue et A/B testing

**Évaluation automatique:** Arize AX joue ce rôle via ses online evaluators déjà décrits dans la section monitoring. Les scores de qualité accumulés à chaque run constituent une base historique qui permet de détecter si une modification de prompt ou de modèle dégrade les résultats.

**A/B testing:** Nous pourrions utiliser **PostHog** pour gérer les variantes : une portion des utilisateurs serait exposée à une configuration v2 (prompt, modèle, température) tandis que le reste continuerait sur v1. Arize AX tracerait les deux variantes séparément, permettant de comparer les métriques de qualité et de performance entre les deux groupes. Quand v2 se montre supérieure, la configuration YAML est mise à jour via une pull request.

**Feedback utilisateur:** Nous pourrions ajouter une table `report_feedbacks` en base pour capturer les retours utilisateurs :

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID | Identifiant unique du feedback |
| `report_id` | UUID | Référence vers `analysis_reports` |
| `user_id` | TEXT | Identifiant de l'utilisateur |
| `feedback` | TEXT | Retour utilisateur (ex: `positive`, `negative`) |
| `created_at` | TIMESTAMPTZ | Horodatage de la création |

Un endpoint supplémentaire sur le serveur FastAPI d'ADK permettrait de recevoir ces feedbacks. Ce signal est précieux pour calibrer les évaluateurs automatiques : si Arize AX attribue un bon score à un rapport que les utilisateurs notent négativement, c'est que l'évaluateur est mal calibré.

**Évolution des capacités:** La façon la plus naturelle de faire évoluer l'agent serait d'ajouter de nouveaux outils et sous-agents : un `price_predictor` pour modéliser l'évolution des prix, un `competitor_analyst` pour comparer le produit à ses alternatives, ou de nouvelles sources de données. ADK est conçu pour ça — chaque nouvel outil enrichit les rapports sans toucher à l'architecture existante.

---

## Tests

Les tests sont organisés en deux niveaux : **tests unitaires** et **tests d'intégration** (requièrent une clé API active).

```bash
# Tests unitaires uniquement
docker compose run --rm app uv run pytest tests/ -v -m "not integration"

# Tous les tests (unitaires + intégration)
docker compose run --rm app uv run pytest tests/ -v
```

### Ce qui est testé

**`test_utils.py`** — Utilitaires de base

- Test que `load_prompt` soulève une exception si un fichier de prompt n'existe pas.
- Test le formatage de la date par `iso_week_label`, notamment le passage d'année.

**`test_trends.py`** — Outils de tendances

- Test que les outils de tendances sont déterministes : le même nom de produit produit toujours les mêmes données.
- Test que le paramètre `weeks` contrôle exactement le nombre de points retournés.

**`test_search.py`** — Outil de recherche web

- Test que le cache évite les appels redondants à Tavily : un deuxième appel identique ne doit pas déclencher une nouvelle requête.
- Test que `include_domains` est transmis tel quel à Tavily.
- Test que `tenacity` effectue exactement 3 tentatives en cas d'échec consécutif.

**`test_review_analyst.py`** — Agent d'analyse des avis

- Test que `web_search` est bien enregistré comme outil.
- Test que l'agent appelle `web_search` au moins une fois avec une requête non vide. Les appels sont interceptés via `before_tool_callback` : aucun appel Tavily réel n'est effectué lors du test.
- Test que l'agent produit une réponse même quand `web_search` retourne une erreur.

**`test_trend_analyzer.py`** — Agent d'analyse des tendances

- Test que les deux outils (`get_price_trend` et `get_popularity_trend`) sont bien enregistrés.
- Test que les deux sont invoqués lors d'une analyse.
- Test que l'agent produit une réponse même en cas d'échec des outils.

**`test_market_analyst.py`** — Agent orchestrateur

- Test que tous les outils et sous-agents sont bien enregistrés (`web_search`, `review_analyst`, `trend_analyzer`, `report_generator`).
- Test que les requêtes sans lien avec une analyse de marché ne déclenchent aucun appel d'outil.
- Test qu'une requête de pricing déclenche bien `web_search`. Les outils sont mockés via `before_tool_callback` : aucune dépendance externe lors du test.
