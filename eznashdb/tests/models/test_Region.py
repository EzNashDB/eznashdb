from eznashdb.models import Country, Region


def test_is_default_region_defaults_to_False():
    country = Country.objects.create(
        name="United States",
        short_name="US"
    )
    region = Region.objects.create(
        country=country,
        name="New York",
    )

    assert region.is_default_region == False
