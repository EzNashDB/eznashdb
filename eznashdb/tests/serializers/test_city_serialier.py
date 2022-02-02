from eznashdb.models import Country, Region, City
from eznashdb.serializers import CitySerializer

def test_converts_city_to_dict():
    # Arrange
    country = Country.objects.create(name='United States', short_name="US")
    region = Region.objects.create(country=country, name="New Jersey", is_default_region=False)
    city = City.objects.create(region=region, name="Teaneck", latitude="1", longitude="2")

    # Act
    serializer = CitySerializer(city, context={'request': None})
    data = serializer.data

    # Assert
    assert data["id"] == city.id
    assert data["name"] == city.name
    assert data["latitude"] == city.latitude
    assert data["longitude"] == city.longitude

    assert data["region"]["id"] == region.id
    assert data["region"]["name"] == region.name
    assert data["region"]["is_default_region"] == region.is_default_region

    assert data["region"]["country"]["id"] == country.id
    assert data["region"]["country"]["name"] == country.name
    assert data["region"]["country"]["short_name"] == country.short_name
