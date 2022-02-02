from eznashdb.views import ShulDetail
from eznashdb.models import Shul, City, Region, Country
from eznashdb.serializers import ShulSerializer

def create_city() -> City:
    country = Country.objects.create()
    region = Region.objects.create(country=country)
    city = City.objects.create(region=region)
    return city

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
