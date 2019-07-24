from django.db import models

# Create your models here.

class Document(models.Model):
    id = models.AutoField(primary_key=True)
    docfile = models.FileField(upload_to='documents/%Y/%m/%d')
    name  = models.TextField(blank=True, null=True)
    replace_name = models.TextField(blank=True, null=True)
    place = models.TextField(blank=True, null=True)
    time_text = models.TextField(blank=True, null=True)
    time_original  = models.DateTimeField(blank=True, null=True)
    time_calc  = models.DateTimeField(blank=True, null=True)
    dup   = models.TextField(blank=True, null=True)