from rest_framework import serializers

from eznashdb.models import Room, Shul


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "relative_size"]


class ShulSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True)

    class Meta:
        model = Shul
        fields = "__all__"
