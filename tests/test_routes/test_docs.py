def test_openapi_json(dbsession, param, client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    _param = param()

    dbsession.commit()

    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert _param.category.name in response.text
