# api/urls.py
from django.urls import path
from .views import (
    PagePluginsAPIView,
    PlaceholderPluginsAPIView,
    AllPagesPluginsAPIView
)

urlpatterns = [
    # Получить все плагины страницы
    path('page/<int:page_id>/plugins/',
         PagePluginsAPIView.as_view(),
         name='api-page-plugins'),

    # Получить плагины конкретного placeholder
    path('page/<int:page_id>/placeholder/<str:slot_name>/plugins/',
         PlaceholderPluginsAPIView.as_view(),
         name='api-placeholder-plugins'),

    # Получить плагины всех страниц
    path('pages/plugins/',
         AllPagesPluginsAPIView.as_view(),
         name='api-all-pages-plugins'),
]
