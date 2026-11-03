import json, time, functools, traceback
from datetime import datetime, timezone
from pathlib import Path
from orchestrator.notify import notify

LOG_DIR = Path("logs/runs")

def log_event(run_id, agent, event, details=None):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id, "agent": agent,
        "event": event, "details": details or {},
    }
    with open(LOG_DIR / f"{run_id}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def traced(agent_name):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(state):
            run_id = state["run_id"]
            log_event(run_id, agent_name, "start")
            t0 = time.time()
            try:
                update = fn(state)
                log_event(run_id, agent_name, "success",
                          {"duration_s": round(time.time() - t0, 3),
                           "outputs": list(update.keys())})
                return update
            except Exception as e:
                log_event(run_id, agent_name, "error",
                          {"error": str(e), "trace": traceback.format_exc()})
                notify(run_id, agent_name, str(e))
                return {"status": "failed",
                        "errors": state.get("errors", []) + [f"{agent_name}: {e}"]}
        return wrapper
    return deco