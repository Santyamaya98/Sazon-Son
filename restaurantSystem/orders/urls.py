from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import CategoryViewSet, MenuItemViewSet, OrderViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'menu-items', MenuItemViewSet, basename='menuitem')
router.register(r'orders', OrderViewSet, basename='order')

app_name = 'orders'

urlpatterns = [
    path('api/', include(router.urls)),
]