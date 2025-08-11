from django.urls import path
from . import views

urlpatterns = [
    path('', views.core_view, name='core'),
    path('load-set/<int:set_id>/', views.load_flashcard_set, name='load_flashcard_set'),
    path('delete-set/<int:set_id>/', views.delete_flashcard_set, name='delete_flashcard_set'),
]