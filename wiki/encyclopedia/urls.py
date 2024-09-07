from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("wiki/search", views.search, name="search"),
    path("wiki/create", views.create, name="create"),
    path("wiki/edit/<str:title>", views.save_edit, name="save_edit"),
    path("wiki/random", views.random_page, name="random_page"),
    path("wiki/<str:title>", views.entry, name="entry")
]
