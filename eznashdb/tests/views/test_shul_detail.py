from eznashdb.views import ShulDetail
from eznashdb.models import Shul
from eznashdb.serializers import ShulSerializer
from eznashdb.testing_utils.model_creators import create_city
from rest_framework.test import force_authenticate

def test_get_returns_serialized_shul_from_id(rf, django_user_model):
    shul = Shul.objects.create(city=create_city(), created_by=django_user_model.objects.create())
    request = rf.get("/")

    response = ShulDetail.as_view()(request, pk=shul.pk)

    assert response.status_code == 200
    assert response.data == ShulSerializer(shul).data


def test_get_returns_404_if_shul_not_found(rf, django_user_model):
    shul = Shul.objects.create(city=create_city(), created_by=django_user_model.objects.create())
    request = rf.get("/")

    response = ShulDetail.as_view()(request, pk=shul.pk+1)

    assert response.status_code == 404

def test_delete_returns_401_if_user_not_authenticated(rf, django_user_model):
    shul = Shul.objects.create(city=create_city(), created_by=django_user_model.objects.create())
    request = rf.delete("/")

    response = ShulDetail.as_view()(request, pk=shul.pk)

    assert response.status_code == 401

def test_delete_returns_404_if_shul_not_found(rf, django_user_model):
    user = django_user_model.objects.create()
    shul = Shul.objects.create(city=create_city(), created_by=user)
    request = rf.delete("/")
    force_authenticate(request, user=user)

    response = ShulDetail.as_view()(request, pk=shul.pk+1)

    assert response.status_code == 404

def test_delete_deletes_shul_if_user_authenticated(rf, django_user_model):
    user = django_user_model.objects.create()
    shul = Shul.objects.create(city=create_city(), created_by=user)
    request = rf.delete("/")
    force_authenticate(request, user=user)

    response = ShulDetail.as_view()(request, pk=shul.pk)

    assert response.status_code == 204
    assert Shul.objects.filter(pk=shul.pk).count() == 0