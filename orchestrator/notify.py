import os, json, urllib.request

def notify(run_id, agent, message):
    text = f"[PIPELINE ECHEC] run={run_id} agent={agent} : {message}"
    print(text)
    url = os.getenv("NOTIFY_WEBHOOK_URL")  # Slack/Discord, optionnel
    if url:
        req = urllib.request.Request(
            url, data=json.dumps({"text": text}).encode(),
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)