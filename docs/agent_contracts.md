# Contrats des agents

L'état partagé est défini dans `orchestrator/state.py`. Chaque agent est une
fonction `node(state) -> dict` qui renvoie uniquement les clés qu'il écrit.
Il doit être décoré avec `@traced("nom")` pour la traçabilité.

| Agent    | Lit dans l'état                 | Écrit dans l'état               |
|----------|---------------------------------|---------------------------------|
| Data     | (aucun)                         | `dataset_uri`, `dataset_hash`   |
| Training | `dataset_uri`, `dataset_hash`   | `model_uri`, `metrics`          |
| QA       | `model_uri`, `metrics`          | `qa_report`                     |
| Release  | `model_uri`, `qa_report`        | `status` (= "done")             |

## Formats

- `dataset_uri` : URI MinIO, ex. `s3://datasets/<nom>/v<N>.csv`
- `dataset_hash` : `sha256:<empreinte>`
- `model_uri` : ex. `s3://models/<nom>/<version>/model.pkl`
- `metrics` : `{"accuracy": float, "f1": float}`
- `qa_report` : `{"non_regression": "ok" | "fail", "fairness_gap": float}`

## Règles

- Un agent qui échoue lève simplement une exception : le décorateur
  `@traced` journalise l'erreur, notifie et arrête le pipeline.
- Un agent n'écrit jamais une clé qui ne lui appartient pas.
- Seul l'agent Release peut toucher au cluster Kubernetes.