"""Rotas do app. A tela inicial é a raiz e exige login (D5: duas pessoas)."""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "financas"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("lancamentos/", views.lancamentos, name="lancamentos"),
    path(
        "lancamentos/<int:pk>/editar/",
        views.editar_movimento,
        name="editar_movimento",
    ),
    path(
        "lancamentos/<int:pk>/desfazer/",
        views.desfazer_movimento,
        name="desfazer_movimento",
    ),
    path("previstos/", views.previstos, name="previstos"),
    path(
        "previstos/fixos/<int:pk>/editar/",
        views.editar_gasto_fixo,
        name="editar_gasto_fixo",
    ),
    path("relatorio/", views.relatorio, name="relatorio"),
    path("categorias/", views.categorias, name="categorias"),
    path(
        "categorias/<int:pk>/editar/",
        views.editar_categoria,
        name="editar_categoria",
    ),
    path(
        "previstos/<int:pk>/paguei/",
        views.pagar_previsto,
        name="pagar_previsto",
    ),
    path(
        "previstos/<int:pk>/ignorar/",
        views.ignorar_previsto,
        name="ignorar_previsto",
    ),
    path(
        "previstos/<int:pk>/reabrir/",
        views.reabrir_previsto,
        name="reabrir_previsto",
    ),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
