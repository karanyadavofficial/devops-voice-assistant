import json
import re
import subprocess

# Container names may only contain these characters (blocks tricks like "; rm -rf")
NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
MAX_OUTPUT_CHARS = 2000


def _docker(args):
    """Run ONE docker command safely: fixed arguments, no shell, 10 second limit."""
    try:
        result = subprocess.run(
            ["docker", *args],
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )
    except FileNotFoundError:
        return None, "Docker is not installed on this machine."
    except subprocess.TimeoutExpired:
        return None, "The Docker command timed out."
    if result.returncode != 0:
        return None, f"Docker error: {result.stderr.strip()[:300]}"
    return result.stdout, None


def _parse_json_lines(text):
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def list_docker_containers(include_stopped=False):
    """List containers (running only, or all)."""
    args = ["ps", "--format", "{{json .}}"]
    if include_stopped:
        args.insert(1, "-a")
    out, err = _docker(args)
    if err:
        return {"error": err}
    containers = [
        {
            "name": c.get("Names"),
            "image": c.get("Image"),
            "state": c.get("State"),
            "status": c.get("Status"),
            "ports": c.get("Ports"),
        }
        for c in _parse_json_lines(out)
    ]
    return {"count": len(containers), "containers": containers}


def get_container_logs(container_name, lines=20):
    """Last few log lines of one container."""
    if not isinstance(container_name, str) or not NAME_PATTERN.match(container_name):
        return {"error": "Invalid container name."}
    try:
        lines = max(1, min(int(lines), 50))
    except (TypeError, ValueError):
        lines = 20
    out, err = _docker(["logs", "--tail", str(lines), container_name])
    if err:
        return {"error": err}
    return {"container": container_name, "logs": out[-MAX_OUTPUT_CHARS:]}


def get_docker_stats():
    """CPU and memory use of each running container."""
    out, err = _docker(["stats", "--no-stream", "--format", "{{json .}}"])
    if err:
        return {"error": err}
    stats = [
        {
            "name": s.get("Name"),
            "cpu": s.get("CPUPerc"),
            "memory": s.get("MemUsage"),
            "memory_percent": s.get("MemPerc"),
        }
        for s in _parse_json_lines(out)
    ]
    return {"count": len(stats), "containers": stats}


DOCKER_TOOLS = {
    "list_docker_containers": list_docker_containers,
    "get_container_logs": get_container_logs,
    "get_docker_stats": get_docker_stats,
}

DOCKER_DECLARATIONS = [
    {
        "name": "list_docker_containers",
        "description": "List Docker containers on the server with their name, image, state and ports. By default only running containers are listed.",
        "parameters": {
            "type": "object",
            "properties": {
                "include_stopped": {
                    "type": "boolean",
                    "description": "Set to true to also include stopped or crashed containers.",
                }
            },
        },
    },
    {
        "name": "get_container_logs",
        "description": "Get the most recent log lines of one Docker container, for example to find out why it crashed.",
        "parameters": {
            "type": "object",
            "properties": {
                "container_name": {
                    "type": "string",
                    "description": "The exact name of the container.",
                },
                "lines": {
                    "type": "integer",
                    "description": "How many recent log lines to fetch (default 20, maximum 50).",
                },
            },
            "required": ["container_name"],
        },
    },
    {
        "name": "get_docker_stats",
        "description": "Get the current CPU and memory usage of every running Docker container.",
    },
]
