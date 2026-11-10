# MLOps Multi-Agents

Pipeline MLOps autonome orchestré par **LangGraph**, intégrant le stockage d'artefacts sous **MinIO** (compatible S3) et le suivi des expérimentations avec **MLflow**, appliqué au jeu de données *Adult Census Income*.

---

## 🏛️ Architecture

Le pipeline repose sur un graphe d'état (`orchestrator/state.py` et `orchestrator/graph.py`) exécutant séquentiellement des agents spécialisés avec arrêt immédiat en cas d'erreur (*fail-fast*) :

1. **Data Agent** (`agents/data/`) : Télécharge les données brutes, valide la qualité, nettoie et versionne le dataset dans MinIO (`s3://datasets/adult/v<N>_<hash8>.csv`).
2. **Training Agent** (`agents/training/`) : Vérifie l'empreinte SHA256 du dataset, entraîne une régression logistique scikit-learn, sauvegarde le modèle sur MinIO (`s3://models/adult_logreg/v<N>/model.pkl`) et journalise métriques et paramètres dans MLflow.
3. **QA Agent** (`agents/qa/`) : Valide les métriques de non-régression et le fairness gap.
4. **Release Agent** (`agents/release/`) : Gère le déploiement en production.

Chaque exécution est journalisée de manière structurée dans `logs/runs/<run_id>.jsonl` via le décorateur `@traced`.

---

## 🚀 Démarrage rapide

### 1. Prérequis et installation

```bash
# Créer et activer l'environnement virtuel
python -m venv .venv
# Linux / macOS :
source .venv/bin/activate
# Windows :
.venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
```

### 2. Démarrage de l'infrastructure locale

Lancez MinIO et MLflow avec Docker Compose :

```bash
docker compose -f infra/docker-compose.yml up -d
```

- **MinIO Console** : [http://localhost:9001](http://localhost:9001) (identifiants par défaut : `minioadmin` / `change-me-12345`)
- **MLflow Tracking Server** : [http://localhost:5000](http://localhost:5000)

### 3. Initialisation des buckets et du dataset

```bash
# Création des buckets MinIO (datasets, models, mlflow)
python scripts/create_buckets.py

# Ingestion du jeu de données brut depuis OpenML vers MinIO
python scripts/upload_raw_dataset.py
```

---

## 🧪 Tests et Exécution

### Exécuter les tests unitaires

Les tests unitaires utilisent des mocks pour s'exécuter sans dépendre de l'infrastructure externe :

```bash
pytest -v
```

### Lancer la baseline

Exécute le pipeline en mode séquentiel direct :

```bash
python -m baseline.run
```

### Lancer le pipeline multi-agents orchestré

```bash
python -m orchestrator.graph
```
