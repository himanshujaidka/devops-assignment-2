def test_homepage_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"ACEest Fitness" in response.data


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_programs_endpoint_lists_supported_programs(client):
    response = client.get("/api/programs")

    assert response.status_code == 200
    assert {"Fat Loss", "Muscle Gain", "Beginner"} == set(response.json)


def test_client_can_be_created_and_listed(client):
    created = client.post(
        "/api/clients",
        json={"name": "Avery", "age": 31, "program": "Muscle Gain"},
    )

    assert created.status_code == 201
    assert created.json == {
        "id": 1,
        "name": "Avery",
        "age": 31,
        "program": "Muscle Gain",
    }

    listed = client.get("/api/clients")
    assert listed.status_code == 200
    assert listed.json == [created.json]


def test_client_requires_a_non_empty_name(client):
    response = client.post("/api/clients", json={"name": "  "})

    assert response.status_code == 400
    assert "name" in response.json["error"]


def test_client_rejects_invalid_age(client):
    response = client.post("/api/clients", json={"name": "Avery", "age": 0})

    assert response.status_code == 400
    assert "Age" in response.json["error"]


def test_client_rejects_unknown_program(client):
    response = client.post(
        "/api/clients", json={"name": "Avery", "program": "Unknown"}
    )

    assert response.status_code == 400


def test_client_rejects_non_string_program(client):
    response = client.post("/api/clients", json={"name": "Avery", "program": []})

    assert response.status_code == 400


def test_duplicate_client_returns_conflict(client):
    client.post("/api/clients", json={"name": "Avery"})

    response = client.post("/api/clients", json={"name": "Avery"})

    assert response.status_code == 409
