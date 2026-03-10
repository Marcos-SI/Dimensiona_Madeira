from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
# from .views import (
#     MadeiraViewSet, 
#     ProjetoViewSet, 
#     PecaDimensionadaViewSet, 
#     LigacaoViewSet,
#     page_catalogo,
#     page_home,
#     page_calculadora,
#     page_projeto
# )


router = DefaultRouter()
router.register(r'madeiras', views.MadeiraViewSet, basename='madeira')
router.register(r'projetos', views.ProjetoViewSet, basename='projeto')
router.register(r'pecas', views.PecaDimensionadaViewSet, basename='peca')
router.register(r'ligacoes', views.LigacaoViewSet, basename='ligacao')


urlpatterns = [
    
    path('', views.page_home, name='home'),
    path('calculadora/', views.page_calculadora, name='calculadora'),
    path('catalogo/', views.page_catalogo, name='catalogo'),
    path('projetos/', views.page_projeto, name='projeto'),

    
    path('api/', include(router.urls)),
]