from django.urls import path

from eznashdb import views

app_name = "eznashdb"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("shuls/create", views.CreateUpdateShulView.as_view(), name="create_shul"),
    path("shuls/<pk>/delete", views.DeleteShulView.as_view(), name="delete_shul"),
]
