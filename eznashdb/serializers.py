from rest_framework import serializers

from eznashdb.models import Room, Shul


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        exclude = ["shul"]


class ShulSerializer(serializers.ModelSerializer):
    rooms = serializers.SerializerMethodField()

    class Meta:
        model = Shul
        fields = "__all__"

    def get_rooms(self, obj):
        ordered_rooms = obj.rooms.order_by("pk")
        return RoomSerializer(ordered_rooms, many=True).data
