import json
import logging

logger = logging.getLogger(__name__)


def rollback(project_id: str, version: str = "previous"):
    logger.info(
        json.dumps({"mock": "orchestrator", "action": "rollback", "project_id": project_id, "version": version})
    )
    return {"status": "ok", "message": f"Rolled back {project_id} to {version}"}


def restart(project_id: str):
    logger.info(json.dumps({"mock": "orchestrator", "action": "restart", "project_id": project_id}))
    return {"status": "ok", "message": f"Restarted {project_id}"}


def scale_up(project_id: str, replicas: int = 1):
    logger.info(
        json.dumps({"mock": "orchestrator", "action": "scale_up", "project_id": project_id, "replicas": replicas})
    )
    return {"status": "ok", "message": f"Scaled up {project_id} by {replicas} replica(s)"}
