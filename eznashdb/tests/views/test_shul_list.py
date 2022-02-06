from eznashdb.views import ShulList
from eznashdb.models import Room, Shul
from eznashdb.serializers import ShulSerializer
from eznashdb.testing_utils.model_creators import create_city

def test_returns_all_shuls(rf, django_user_model):
    # Arrange
    test_user = django_user_model.objects.create()
    shul1 = Shul.objects.create(city=create_city(), created_by=test_user)
    shul2 = Shul.objects.create(city=create_city(), created_by=test_user)
    Room.objects.create(shul=shul1)
    Room.objects.create(shul=shul1)
    request = rf.get("/")

    # Act
    response = ShulList.as_view()(request)

    # Assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert ShulSerializer(shul1).data in response.data
    assert ShulSerializer(shul2).data in response.data
    shul1_data = [shul for shul in response.data if shul.get('id')==shul1.pk][0]
    assert len(shul1_data.get('rooms')) == 2
