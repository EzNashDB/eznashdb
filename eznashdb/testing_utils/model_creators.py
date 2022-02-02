from eznashdb.models import City, Region, Country

def create_city() -> City:
    country = Country.objects.create(name="test country")
    region = Region.objects.create(country=country, name="test region")
    city = City.objects.create(region=region, name="test city")
    return city