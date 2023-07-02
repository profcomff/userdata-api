def test_openapi_json(dbsession, param, client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    _param = param()

    dbsession.commit()

    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert _param.category.name in response.text
    assert _param.name in response.text


def test_dev_docs_available(client):
    response = client.get("/docs")
    assert response.status_code == 200
