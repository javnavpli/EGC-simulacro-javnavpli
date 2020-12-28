from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from .views import GetUserView, LogoutView, registro_usuario, RegisterView, inicio
from django.contrib.auth.decorators import login_required



urlpatterns = [
    path('login/', obtain_auth_token),
    path('logout/', LogoutView.as_view()),
    path('getuser/', GetUserView.as_view()),
    path('register/', RegisterView.as_view()),
    path('registro/', registro_usuario),
    path('inicio/', login_required(inicio), name="inicio"),
    path('social-auth/', include('social_django.urls', namespace='social'))
    
]
