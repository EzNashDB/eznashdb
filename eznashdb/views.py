from rest_framework import generics
from eznashdb.models import Shul
from eznashdb.serializers import ShulSerializer


class ShulDetail(generics.RetrieveAPIView):
    """
    Retrieve a shul
    """
    queryset = Shul.objects.all()
    serializer_class = ShulSerializer
