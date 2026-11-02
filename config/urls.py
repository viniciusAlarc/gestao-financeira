"""Rotas do projeto: a raiz é o app `financas`, o admin fica em `/admin/`."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("financas.urls")),
    path("admin/", admin.site.urls),
]
