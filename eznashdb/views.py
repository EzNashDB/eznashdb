from rest_framework import generics
from eznashdb.models import Shul
from eznashdb.serializers import ShulSerializer
from rest_framework import permissions


class ShulDetail(generics.RetrieveDestroyAPIView):
    """
    Retrieve a shul
    """
    queryset = Shul.objects.all()
    serializer_class = ShulSerializer

    def get_permissions(self):
        if self.request.method in ['DELETE']:
            return [permissions.IsAuthenticated()]
        return []


class ShulList(generics.ListAPIView):
    """
    List all shuls
    """
    queryset = Shul.objects.all()
    serializer_class = ShulSerializer
