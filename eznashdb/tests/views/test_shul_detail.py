from eznashdb.views import ShulDetail
from eznashdb.models import Shul
from eznashdb.serializers import ShulSerializer
from eznashdb.testing_utils.model_creators import create_city

def test_returns_serialized_shul_from_id(rf, django_user_model):
    shul = Shul.objects.create(city=create_city(), created_by=django_user_model.objects.create())
    request = rf.get("/")

    response = ShulDetail.as_view()(request, pk=shul.pk)

    assert response.status_code == 200
    assert response.data == ShulSerializer(shul).data


def test_returns_404_if_shul_not_found(rf, django_user_model):
    shul = Shul.objects.create(city=create_city(), created_by=django_user_model.objects.create())
    request = rf.get("/")

    response = ShulDetail.as_view()(request, pk=shul.pk+1)

    assert response.status_code == 404
