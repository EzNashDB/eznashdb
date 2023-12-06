from rest_framework import serializers

from eznashdb.models import Room, Shul, ShulLink


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        exclude = ["shul"]


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShulLink
        exclude = ["shul"]


class ShulSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True)
    links = LinkSerializer(many=True)

    class Meta:
        model = Shul
        fields = "__all__"
