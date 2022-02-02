from rest_framework import serializers
from eznashdb.models import City, Region, Country, Shul, Room
from app import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class CountrySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Country
        fields = [
            "id",
            "name",
            "short_name",
        ]

class RegionSerializer(serializers.ModelSerializer):
    country = CountrySerializer()
    
    class Meta:
        model = Region
        fields = [
            "id",
            "name",
            "is_default_region",
            "country",
        ]

class CitySerializer(serializers.ModelSerializer):
    region = RegionSerializer()

    class Meta:
        model = City
        fields = [
            "id",
            "name",
            "latitude",
            "longitude",
            "region",
        ]

class UserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=100)


class UserFromIDField(serializers.PrimaryKeyRelatedField):

    def get_queryset(self):
        return self.queryset

    def to_representation(self, value):
        user = User.objects.get(pk=value)
        return UserSerializer(user).data

class ShulSerializer(serializers.ModelSerializer):
    city = CitySerializer()
    created_by = UserSerializer()
    editted_by = UserFromIDField(many=True)

    class Meta:
        model = Shul
        fields = [
            "id",
            "name",
            "created_by",
            "editted_by",
            "has_female_leadership",
            "has_childcare",
            "has_kaddish_with_men",
            "enum_has_kaddish_alone",
            "city",
        ]


class RoomSerializer(serializers.ModelSerializer):

    class Meta:
        model = Room
        fields = [
            "id",
            "shul",
            "name",
            "relative_size", 
            "see_hear_score", 
            "is_centered", 
            "is_same_floor_side", 
            "is_same_floor_back", 
            "is_same_floor_elevated", 
            "is_same_floor_level", 
            "is_balcony_side",
            "is_balcony_back", 
            "is_only_men", 
            "is_mixed_seating", 
            "is_wheelchair_accessible", 
        ]

class ShulSerializer(serializers.ModelSerializer):
    city = CitySerializer()
    created_by = UserSerializer()
    editted_by = UserFromIDField(many=True)
    rooms = RoomSerializer(many=True)

    class Meta:
        model = Shul
        fields = [
            "id",
            "name",
            "created_by",
            "editted_by",
            "has_female_leadership",
            "has_childcare",
            "has_kaddish_with_men",
            "enum_has_kaddish_alone",
            "city",
            "rooms",
        ]

