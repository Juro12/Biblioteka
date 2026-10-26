from django.urls import path

from . import views

urlpatterns = [
    path('', views.lista, name='lista'),
    path('dodaj/', views.dodaj, name='dodaj'),
    path('<int:pk>/edytuj/', views.edytuj, name='edytuj'),
    path('<int:pk>/usun/', views.usun, name='usun'),
    path('czytelnicy/', views.lista_czytelnikow, name='czytelnicy'),
    path('czytelnicy/dodaj/', views.dodaj_czytelnika, name='dodaj_czytelnika'),
    path('czytelnicy/<int:pk>/', views.szczegoly_czytelnika, name='szczegoly_czytelnika'),
    path('czytelnicy/<int:pk>/edytuj/', views.edytuj_czytelnika, name='edytuj_czytelnika'),
    path('czytelnicy/<int:pk>/usun/', views.usun_czytelnika, name='usun_czytelnika'),
    path('wypozycz/', views.wypozycz, name='wypozycz'),
    path('wypozyczenia/', views.lista_wypozyczen, name='wypozyczenia'),
    path('wypozyczenia/<int:pk>/zwroc/', views.zwroc, name='zwroc'),
]
