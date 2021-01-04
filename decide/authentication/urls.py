from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from django.contrib.auth.decorators import login_required

from .views import GetUserView, LogoutView, RegisterView, EmailGenerateTokenView, EmailConfirmTokenView, registro_usuario, inicio, ObtainAuthTokenSecondFactor


urlpatterns = [
    path('login/', ObtainAuthTokenSecondFactor.as_view()), # obtain_auth_token),
    path('logout/', LogoutView.as_view()),
    path('getuser/', GetUserView.as_view()),
    path('register/', RegisterView.as_view()),
    path('email-generate-token/', EmailGenerateTokenView.as_view()),
    path('email-confirm-token/<userId>/<token>/', EmailConfirmTokenView.as_view(), name="email-confirm-token"),
    path('registro/', registro_usuario),
    path('inicio/', login_required(inicio), name="inicio")
]
