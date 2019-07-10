from django.db import models

# Create your models here.

class Document(models.Model):
    docfile = models.FileField(upload_to='documents/%Y/%m/%d')
    name  = models.TextField(blank=True, null=True)
    replace_name = models.TextField(blank=True, null=True)
    place = models.TextField(blank=True, null=True)
    time  = models.DateTimeField(blank=True, null=True)
    dup   = models.TextField(blank=True, null=True)