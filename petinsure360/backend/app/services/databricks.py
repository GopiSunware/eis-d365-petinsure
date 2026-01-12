"""
Azure Databricks Integration Service

Provides functions to invoke Databricks notebooks and monitor job status.
Used by the Rule Engine pipeline to execute Bronze/Silver/Gold ETL in Databricks.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

# Databricks Configuration
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")
DATABRICKS_JOB_ID = os.getenv("DATABRICKS_JOB_ID", "591500457291311")

# Task keys matching the Databricks job configuration
TASK_KEYS = {
    "bronze": "bronze_ingestion",
    "silver": "silver_transform",
    "gold": "gold_aggregations"
}


def is_databricks_configured() -> bool:
    """Check if Databricks credentials are configured."""
    return bool(DATABRICKS_HOST and DATABRICKS_TOKEN)


def get_databricks_job_url(run_id: int) -> str:
    """Get the URL to view a job run in Databricks UI."""
    host = DATABRICKS_HOST.rstrip('/')
    return f"{host}/#job/{DATABRICKS_JOB_ID}/run/{run_id}"


async def run_job_tasks(task_keys: List[str], parameters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Run specific tasks within the PetInsure360 ETL job.

    Args:
        task_keys: List of task keys to run (e.g., ["bronze_ingestion", "silver_transform"])
        parameters: Optional notebook parameters to pass

    Returns:
        Dict with run_id, job_url, and status
    """
    if not is_databricks_configured():
        return {
            "success": False,
            "error": "Databricks not configured. Set DATABRICKS_HOST and DATABRICKS_TOKEN.",
            "run_id": None
        }

    url = f"{DATABRICKS_HOST.rstrip('/')}/api/2.1/jobs/run-now"
    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Build request payload
    payload = {
        "job_id": int(DATABRICKS_JOB_ID)
    }

    # Filter to specific tasks if provided
    if task_keys:
        payload["only_tasks"] = task_keys

    # Add notebook parameters if provided
    if parameters:
        payload["notebook_params"] = parameters

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            run_id = result.get("run_id")
            job_url = get_databricks_job_url(run_id) if run_id else None

            logger.info(f"Databricks job triggered: run_id={run_id}, tasks={task_keys}")

            return {
                "success": True,
                "run_id": run_id,
                "job_url": job_url,
                "number_in_job": result.get("number_in_job"),
                "tasks_triggered": task_keys
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"Databricks API error: {e.response.status_code} - {e.response.text}")
        return {
            "success": False,
            "error": f"Databricks API error: {e.response.status_code}",
            "details": e.response.text,
            "run_id": None
        }
    except httpx.RequestError as e:
        logger.error(f"Databricks connection error: {e}")
        return {
            "success": False,
            "error": f"Failed to connect to Databricks: {str(e)}",
            "run_id": None
        }


async def get_run_status(run_id: int) -> Dict[str, Any]:
    """
    Get the status of a Databricks job run.

    Args:
        run_id: The run ID to check

    Returns:
        Dict with state, life_cycle_state, result_state, tasks status
    """
    if not is_databricks_configured():
        return {"error": "Databricks not configured"}

    url = f"{DATABRICKS_HOST.rstrip('/')}/api/2.1/jobs/runs/get"
    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}"
    }
    params = {"run_id": run_id}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()

            state = result.get("state", {})
            tasks = result.get("tasks", [])

            # Parse task statuses
            task_statuses = []
            for task in tasks:
                task_statuses.append({
                    "task_key": task.get("task_key"),
                    "state": task.get("state", {}).get("life_cycle_state"),
                    "result_state": task.get("state", {}).get("result_state"),
                    "start_time": task.get("start_time"),
                    "end_time": task.get("end_time"),
                    "execution_duration": task.get("execution_duration")
                })

            return {
                "run_id": run_id,
                "job_url": get_databricks_job_url(run_id),
                "life_cycle_state": state.get("life_cycle_state"),
                "result_state": state.get("result_state"),
                "state_message": state.get("state_message"),
                "start_time": result.get("start_time"),
                "end_time": result.get("end_time"),
                "execution_duration": result.get("execution_duration"),
                "run_duration": result.get("run_duration"),
                "tasks": task_statuses,
                "is_complete": state.get("life_cycle_state") in ["TERMINATED", "SKIPPED", "INTERNAL_ERROR"],
                "is_success": state.get("result_state") == "SUCCESS"
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to get run status: {e.response.status_code}")
        return {"error": f"API error: {e.response.status_code}", "run_id": run_id}
    except httpx.RequestError as e:
        logger.error(f"Connection error getting run status: {e}")
        return {"error": f"Connection error: {str(e)}", "run_id": run_id}


async def run_bronze_silver() -> Dict[str, Any]:
    """
    Run Bronze and Silver layer notebooks.
    Called when user triggers "Bronze → Silver" processing.
    """
    return await run_job_tasks([TASK_KEYS["bronze"], TASK_KEYS["silver"]])


async def run_gold() -> Dict[str, Any]:
    """
    Run Gold layer notebook.
    Called when user triggers "Silver → Gold" processing.
    """
    return await run_job_tasks([TASK_KEYS["gold"]])


async def run_full_pipeline() -> Dict[str, Any]:
    """
    Run the complete ETL pipeline (Bronze → Silver → Gold).
    """
    return await run_job_tasks([TASK_KEYS["bronze"], TASK_KEYS["silver"], TASK_KEYS["gold"]])


async def get_recent_runs(limit: int = 10) -> Dict[str, Any]:
    """
    Get recent job runs for the PetInsure360 ETL job.
    """
    if not is_databricks_configured():
        return {"error": "Databricks not configured", "runs": []}

    url = f"{DATABRICKS_HOST.rstrip('/')}/api/2.1/jobs/runs/list"
    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}"
    }
    params = {
        "job_id": int(DATABRICKS_JOB_ID),
        "limit": limit
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()

            runs = []
            for run in result.get("runs", []):
                state = run.get("state", {})
                runs.append({
                    "run_id": run.get("run_id"),
                    "job_url": get_databricks_job_url(run.get("run_id")),
                    "life_cycle_state": state.get("life_cycle_state"),
                    "result_state": state.get("result_state"),
                    "start_time": run.get("start_time"),
                    "end_time": run.get("end_time"),
                    "run_duration": run.get("run_duration")
                })

            return {"runs": runs, "has_more": result.get("has_more", False)}

    except Exception as e:
        logger.error(f"Failed to get recent runs: {e}")
        return {"error": str(e), "runs": []}
