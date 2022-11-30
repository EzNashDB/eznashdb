from eznashdb import views
from django.urls import path

app_name = "eznashdb"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
]