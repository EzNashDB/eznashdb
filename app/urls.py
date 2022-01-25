from django.contrib import admin
from django.urls import include, path
from app.views import GoogleLogin, GoogleConnect
from dj_rest_auth.registration.views import (
    SocialAccountListView, SocialAccountDisconnectView
)

dj_rest_auth_urls = [
    path('', include('dj_rest_auth.urls')),
    path('registration/', include('dj_rest_auth.registration.urls')),
    path('google/', GoogleLogin.as_view(), name='google_login'),
    path('google/connect/', GoogleConnect.as_view(), name='google_connect'),
]

social_account_urls = [
    path('', SocialAccountListView.as_view(), name='social_account_list'),
    path('<int:pk>/disconnect/', SocialAccountDisconnectView.as_view(), name='social_account_disconnect'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dj-rest-auth/', include(dj_rest_auth_urls)),
    path('socialaccounts/', include(social_account_urls)),
    path('accounts/', include('allauth.urls'), name='socialaccount_signup'),
]
