from eznashdb import views
from django.urls import path

app_name = "eznashdb"

urlpatterns = [
    path("shuls/", views.ShulList.as_view(), name="shul_list"),
    path("shuls/<int:pk>/", views.ShulDetail.as_view(), name="shul_detail"),
]