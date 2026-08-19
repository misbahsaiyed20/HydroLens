def test_create_report_success(client, sample_image_bytes):
    response = client.post(
        "/api/reports",
        data={
            "latitude": "23.0225",
            "longitude": "72.5714",
            "stream_name": "Sabarmati",
            "description": "Greenish tint near the ghat steps.",
        },
        files={"image": ("stream.png", sample_image_bytes, "image/png")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "SUBMITTED"
    assert body["description"] == "Greenish tint near the ghat steps."
    assert body["location"]["stream_name"] == "Sabarmati"
    assert body["observation"] is None  # not populated until AI service runs (later sprint)


def test_create_report_rejects_bad_content_type(client):
    response = client.post(
        "/api/reports",
        data={"latitude": "23.0", "longitude": "72.5"},
        files={"image": ("notes.txt", b"just text", "text/plain")},
    )
    assert response.status_code == 400


def test_create_report_rejects_invalid_latitude(client, sample_image_bytes):
    response = client.post(
        "/api/reports",
        data={"latitude": "200", "longitude": "72.5"},
        files={"image": ("stream.png", sample_image_bytes, "image/png")},
    )
    assert response.status_code == 422


def test_get_report_by_id(client, sample_image_bytes):
    create_resp = client.post(
        "/api/reports",
        data={"latitude": "23.0225", "longitude": "72.5714"},
        files={"image": ("stream.png", sample_image_bytes, "image/png")},
    )
    report_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/reports/{report_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == report_id


def test_get_report_not_found(client):
    import uuid
    response = client.get(f"/api/reports/{uuid.uuid4()}")
    assert response.status_code == 404


def test_list_reports(client, sample_image_bytes):
    for _ in range(3):
        client.post(
            "/api/reports",
            data={"latitude": "23.0225", "longitude": "72.5714"},
            files={"image": ("stream.png", sample_image_bytes, "image/png")},
        )

    response = client.get("/api/reports")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
