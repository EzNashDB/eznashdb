from rest_framework import generics
from eznashdb.models import Shul
from eznashdb.serializers import ShulSerializer


class ShulDetail(generics.RetrieveAPIView):
    """
    Retrieve a shul
    """
    queryset = Shul.objects.all()
    serializer_class = ShulSerializer

class ShulList(generics.ListAPIView):
    """
    List all code snippets, or create a new snippet
    """
    queryset = Shul.objects.all()
    serializer_class = ShulSerializer
