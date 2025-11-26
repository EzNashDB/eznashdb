from django.urls import path

from eznashdb import views

app_name = "eznashdb"

urlpatterns = [
    path("", views.ShulsFilterView.as_view(), name="shuls"),
    path("shuls/create", views.CreateUpdateShulView.as_view(), name="create_shul"),
    path("shuls/<pk>/update", views.CreateUpdateShulView.as_view(), name="update_shul"),
    path("shuls/<pk>/delete", views.DeleteShulView.as_view(), name="delete_shul"),
    path("address-lookup", views.AddressLookupView.as_view(), name="address_lookup"),
    path("contact-us", views.ContactUsView.as_view(), name="contact_us"),
    path("gmaps-proxy", views.GoogleMapsProxyView.as_view(), name="google_maps_proxy"),
]
