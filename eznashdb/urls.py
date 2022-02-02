from eznashdb import views
from django.urls import path

app_name = "eznashdb"

urlpatterns = [
    path("shul/<int:pk>", views.ShulDetail.as_view(), name="shul_detail"),
]