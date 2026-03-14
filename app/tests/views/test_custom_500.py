from app.views import custom_500


def test_it_returns_500_status_without_raising(rf):
    request = rf.get("/")
    response = custom_500(request)
    assert response.status_code == 500
