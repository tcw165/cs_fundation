from take_home.causal_chains.agents.http_models.health_response import HealthResponse


def test_health_response_parses():
    report = HealthResponse(status="ok", db="up")
    assert report.status == "ok"
    assert report.db == "up"


def test_health_response_requires_fields():
    try:
        HealthResponse()
        raise AssertionError("expected validation error")
    except Exception as error:
        assert "status" in str(error) or "Field required" in str(error)
