from rest_framework import serializers

from eznashdb.models import ChildcareProgram, Room, Shul, ShulLink


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        exclude = ["shul"]


class ChildcareSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildcareProgram
        exclude = ["shul"]


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShulLink
        exclude = ["shul"]


class ShulSerializer(serializers.ModelSerializer):
    rooms = serializers.SerializerMethodField()
    childcare_programs = serializers.SerializerMethodField()
    links = LinkSerializer(many=True)

    class Meta:
        model = Shul
        fields = "__all__"

    def get_rooms(self, obj):
        ordered_rooms = obj.rooms.order_by("pk")
        return RoomSerializer(ordered_rooms, many=True).data

    def get_childcare_programs(self, obj):
        ordered_programs = obj.childcare_programs.order_by("pk")
        return ChildcareSerializer(ordered_programs, many=True).data
