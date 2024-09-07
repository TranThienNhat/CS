from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("creating", views.create_listing, name="create_listing"),
    path("listing/<int:listing_id>", views.listing, name="listing"),
    path("watchlist/<int:listing_id>/", views.watchlist, name="watchlist"),
    path("watchlisting", views.watchlisting, name="watchlisting"),
    path("comment/<int:listing_id>", views.comment, name="comment"),
    path("categories/", views.categories, name="categories"),
    path("categories/<str:category_name>/", views.category_listings, name="category_listings"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)