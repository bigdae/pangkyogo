from django.db import models

# Create your models here.

class Document(models.Model):
    docfile = models.FileField(upload_to='documents/%Y/%m/%d')
    place = models.TextField(blank=True, null=True)
    time  = models.TimeField(blank=True, null=True)