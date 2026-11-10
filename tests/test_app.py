import os

# The app refuses to start without a key, so give tests a fake one.
# Tests never call Gemini, so the fake key is never used.
os.environ.setdefault("GEMINI_API_KEY", "dummy-key-for-tests")

from fastapi.testclient import TestClient

import docker_tools
import main
import tools


def test_health_endpoint():
    client = TestClient(main.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_tool_is_refused():
    result = tools.run_tool("delete_everything")
    assert "error" in result


def test_system_tools_return_data():
    assert "cpu_percent" in tools.run_tool("get_cpu_usage")
    assert "percent_used" in tools.run_tool("get_memory_usage")
    assert "free_gb" in tools.run_tool("get_disk_usage")
    assert "hostname" in tools.run_tool("get_system_info")


def test_bad_container_name_is_blocked():
    result = docker_tools.get_container_logs("x; rm -rf /")
    assert result == {"error": "Invalid container name."}


def test_every_declared_tool_exists_in_allowlist():
    for declaration in tools.TOOL_DECLARATIONS:
        assert declaration["name"] in tools.TOOLS


def test_allowlist_is_read_only():
    allowed = set(tools.TOOLS)
    assert allowed == {
        "get_cpu_usage",
        "get_memory_usage",
        "get_disk_usage",
        "get_system_info",
        "list_docker_containers",
        "get_container_logs",
        "get_docker_stats",
    }
