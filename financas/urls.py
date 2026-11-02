"""Rotas do app. A tela inicial é a raiz e exige login (D5: duas pessoas)."""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "financas"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
]
