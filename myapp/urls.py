from django.urls import path
from . import views

urlpatterns = [
	path('', views.list, name='list'),
	path('extract', views.extractText, name='extract'),
	path('delete/<int:id>', views.delete, name='delete'),
	path('update/<int:id>', views.update, name='update')
]