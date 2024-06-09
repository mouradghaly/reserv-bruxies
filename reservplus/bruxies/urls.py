from . import views
from django.urls import path
urlpatterns = [
    path("reservation", views.reservation, name="reservation"), 
    path("check", views.checkavailability, name='cds'),
    path("admin", views.admin, name='admin'),
    path("authn", views.authn, name='authn'),
    path("confirm", views.confirm_reservation, name= 'confirm'),
    path('', views.home, ),
    path("generate", views.generate_report)
    #path('', views.home, 'home')
]