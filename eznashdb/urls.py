from django.urls import path

from eznashdb import views

app_name = "eznashdb"

urlpatterns = [
    path("", views.ShulsFilterView.as_view(), name="shuls"),
    path("shuls/create", views.CreateShulView.as_view(), name="create_shul"),
    path("shuls/<pk>/delete", views.DeleteShulView.as_view(), name="delete_shul"),
    path("address-lookup", views.AddressLookupView.as_view(), name="address_lookup"),
]
