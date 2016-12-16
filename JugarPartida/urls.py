from django.conf.urls import url
from . import views

urlpatterns = [
      url(r'^crearpartida/$', views.crearpartida, name='crearpartida'),
      url(r'^partidacreada/$', views.partidacreada, name='partidacreada'),
      url(r'^ponerpieza/(?P<partidaid>[0-9]+)$', views.ponerpieza, name='ponerpieza'),
      url(r'^rotarpieza/(?P<rotsentido>[a-z]+)/(?P<imagen>[0-9]+)$', views.rotarpieza, name='rotarpieza'),
      url(r'^(?P<partidaid>[0-9]+)/incrustarpieza/(?P<idmapapieza>[a-z]+[0-9]+)/(?P<imagen>[0-9]+)$', views.incrustarpieza, name='incrustarpieza'),
]
