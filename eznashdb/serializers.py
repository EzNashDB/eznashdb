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
    rooms = serializers.SerializerMethodField()
    links = LinkSerializer(many=True)

    class Meta:
        model = Shul
        fields = "__all__"

    def get_rooms(self, obj):
        ordered_rooms = obj.rooms.order_by("pk")
        return RoomSerializer(ordered_rooms, many=True).data
