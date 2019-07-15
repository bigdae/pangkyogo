from django.urls import path
from . import views

urlpatterns = [
	path('', views.list, name='list'),
	path('/delete/<int:id>', views.delete, name='delete')
]