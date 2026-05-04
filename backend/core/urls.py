from django.contrib import admin
from django.urls import include, path
from marketplace.frontend_views import (
    CatalogueView, CartView, OrdersView, ProducerHubView, LoginPageView,
)
 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('marketplace.urls')),
 
    # Frontend pages
    path('market/',           CatalogueView.as_view(),   name='catalogue'),
    path('market/cart/',      CartView.as_view(),         name='cart'),
    path('market/orders/',    OrdersView.as_view(),       name='orders'),
    path('market/producer/',  ProducerHubView.as_view(),  name='producer'),
    path('market/login/',     LoginPageView.as_view(),    name='login'),
]
 