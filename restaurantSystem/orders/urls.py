#orders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import CategoryViewSet, MenuItemViewSet, TableViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'menu-items', MenuItemViewSet, basename='menuitem')
router.register(r'tables', TableViewSet, basename='table')


app_name = 'orders'

urlpatterns = [
    path('', include(router.urls)),
    
]