# Contrats des agents

L'état partagé est défini dans `orchestrator/state.py`. Chaque agent est une
fonction `node(state) -> dict` qui renvoie uniquement les clés qu'il écrit.
Il doit être décoré avec `@traced("nom")` pour la traçabilité.

| Agent    | Lit dans l'état                                   | Écrit dans l'état |
|----------|---------------------------------------------------|-------------------|
| Data     | (aucun)                                           | `dataset_uri`, `dataset_hash`, `data_report` |
| Training | `dataset_uri`, `dataset_hash`                     | `model_uri`, `metrics` |
| QA       | `dataset_uri`, `dataset_hash`, `model_uri`        | `qa_report` |
| Gate     | `qa_report`                                       | `gate_decision` (et `status` = "rejected" si refus) |
| Approval | `model_uri`, `qa_report`, `gate_decision`         | `approved` (et `status` = "rejected" si refus humain) |
| Release  | `model_uri`, `qa_report`                          | `status` (= "done") |

## Formats

- `dataset_uri` : URI MinIO, ex. `s3://datasets/<nom>/v<N>_<hash8>.csv`
- `dataset_hash` : `sha256:<empreinte>`
- `data_report` : rapport qualité (`n_rows`, `duplicates`, `missing_ratio_total`, ...), `rows_after_cleaning` (`int`), `version` (`int`), `reused` (`bool`)
- `model_uri` : ex. `s3://models/<nom>/<version>/model.pkl`
- `metrics` : `{"accuracy": float, "f1": float}`
- `qa_report` : `{"accuracy", "f1", "prod_accuracy" (ou null), "regression_vs_prod" (ou null),
  "fairness_gap", "fairness_by_attr": {"sex": float, "race": float}, "robustness_drop"}`.
  `regression_vs_prod` > 0 signifie que le candidat est moins bon que la production ;
  null signifie qu'il n'y a pas encore de modèle en production.
- `gate_decision` : `{"decision": "reject" | "auto_approve" | "needs_human", "risk": "low" | "high", "reasons": [str]}`
- `status` : `running` | `failed` | `rejected` | `done`

## Règles

- Un agent qui échoue lève simplement une exception : le décorateur
  `@traced` journalise l'erreur, notifie et arrête le pipeline (`status` = "failed").
- Un refus du quality gate ou de l'approbation humaine arrête aussi le pipeline,
  avec `status` = "rejected" (ce n'est pas une panne, donc pas de notification d'échec).
- Les seuils du quality gate sont dans `quality_gate/gate.yaml`.
- Le modèle « en production » est désigné par `s3://models/production/current.json`.
- Un agent n'écrit jamais une clé qui ne lui appartient pas.
- Seul l'agent Release peut toucher au cluster Kubernetes.
