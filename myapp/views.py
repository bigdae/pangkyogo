from django.shortcuts import render

from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.urls import reverse

from myapp.models import Document
from myapp.forms import DocumentForm
from PIL import Image
import telegram
import io
import os
from google.cloud import vision
from google.cloud.vision import types
import datetime
import re
from django.core.files.storage import FileSystemStorage
import time

def list(request):
    # Handle file upload
    my_token = '727599178:AAH_ksTAfbHK7PKt4fJq28Dj91slG3BVPXQ'
    bot = telegram.Bot(token = my_token)


    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():

            # extract text
            location, egg_time, monster_time, monster_name = "", "", "", ""
            time_arr = []
            now_datetime = datetime.datetime.now()
            # image resize
            img = Image.open(request.FILES['docfile'])
            new_height = 1280
            new_width  = int(new_height * img.width / img.height)
            img = img.resize((new_width, new_height), Image.ANTIALIAS)
            # extract text
            document = getText(img)

            location = text_within(document,150,80,1000,166).replace("\n", "")
            egg_time = text_within(document,200,240,1000,333).replace("\n","")
            monster_time = text_within(document,200,690,1000,818).replace("\n","")

            if monster_time:
                monster_name = text_within(document,0,150,1200,460)
                if monster_time.count(":") > 1 :
                  time_arr =  [int(i) for i in monster_time.split(":")]
                  now_datetime = now_datetime + datetime.timedelta(minutes=time_arr[1])
                  now_datetime = now_datetime + datetime.timedelta(seconds=time_arr[2])
            else:
                if egg_time.count(":") > 1 :
                  time_arr =  [int(i) for i in egg_time.split(":")]
                  now_datetime = now_datetime + datetime.timedelta(minutes=45)
                  now_datetime = now_datetime + datetime.timedelta(minutes=time_arr[1])
                  now_datetime = now_datetime + datetime.timedelta(seconds=time_arr[2])
           
            if monster_name == "":
                monster_name = "unknown"
                
            newdoc = Document(docfile = request.FILES['docfile'], name=monster_name, place=location, time=now_datetime)

            if len(Document.objects.filter(time__gte=datetime.datetime.now()).filter(place=location)) > 0:
                newdoc.dup = "Y"
            else:
                newdoc.dup = "N"
            newdoc.save()
            #if newdoc.dup == "N" :
            #    bot.sendMessage(chat_id = '@pangkyogo', text=text_message)
            # Redirect to the document list after POST
            documents = Document.objects.filter(time__gte=datetime.datetime.now()).filter(dup='N')
            form = DocumentForm() # A empty, unbound form
            return render(request, 'list.html', {'documents': documents, 'form': form, 'dup': newdoc.dup})
    else:
        form = DocumentForm() # A empty, unbound form

    # Load documents for the list page
    documents = Document.objects.all()
    #documents = Document.objects.filter(time__gte=datetime.datetime.now())#.filter(dup='N')

    # Render list page with the documents and the form
    return render(request, 'list.html', {'documents': documents, 'form': form})

def extractText(request):
    # Handle file upload
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)

        if form.is_valid():

            # extract text
            location, egg_time, monster_time, monster_name = "", "", "", ""
            time_arr = []
            time = datetime.datetime.strptime(request.POST['lastmodified'], '%Y-%m-%d %H:%M:%S')
            time_calc = time
            # image resize
            img = Image.open(request.FILES['docfile'])
            new_height = 1280
            new_width  = int(new_height * img.width / img.height)
            img = img.resize((new_width, new_height), Image.ANTIALIAS)
            # extract text
            document = getText(img)

            location = text_within(document,150,80,1000,166).replace("\n", "")
            egg_time = text_within(document,200,240,1000,333).replace("\n","")
            monster_time = text_within(document,200,690,1000,818).replace("\n","")

            if monster_time:
                monster_name = text_within(document,0,150,1200,460)
                if monster_time.count(":") > 1 :
                  time_arr =  [int(i) for i in monster_time.split(":")]
                  time_calc = time_calc + datetime.timedelta(hours=time_arr[0])
                  time_calc = time_calc + datetime.timedelta(minutes=time_arr[1])
                  time_calc = time_calc + datetime.timedelta(seconds=time_arr[2])
            else:
                if egg_time.count(":") > 1 :
                  time_arr =  [int(i) for i in egg_time.split(":")]
                  time_calc = time_calc + datetime.timedelta(minutes=45)
                  time_calc = time_calc + datetime.timedelta(hours=time_arr[0])
                  time_calc = time_calc + datetime.timedelta(minutes=time_arr[1])
                  time_calc = time_calc + datetime.timedelta(seconds=time_arr[2])
           
            if monster_name == "":
                monster_name = "EGG"
            newdoc = Document(docfile = request.FILES['docfile'], name=monster_name, place=location, time=time, time_calc=time_calc, time_text=":".join(str(e) for e in time_arr))

            if len(Document.objects.filter(time__gte=datetime.datetime.now()).filter(place=location)) > 0:
                newdoc.dup = "Y"
            else:
                newdoc.dup = "N"

            newdoc.save()
            documents = Document.objects.all()
            #documents = Document.objects.filter(time__gte=datetime.datetime.now()).filter(dup='N')
            form = DocumentForm() # A empty, unbound form
            return render(request, 'list.html', {'documents': documents, 'form': form, 'newdoc':newdoc})

def update(request, id):
  if request.method == 'POST':
    id = request.POST['id']
    name = request.POST['name'].upper()
    time = Document.objects.get(id=id).time
    
    time_text = request.POST['time_text']
    time_arr =  [int(i) for i in time_text.split(":")]
    if name.startswith("EGG"):
      time = time + datetime.timedelta(minutes=45)
    time = time + datetime.timedelta(hours=time_arr[0])
    time = time + datetime.timedelta(minutes=time_arr[1])
    time = time + datetime.timedelta(seconds=time_arr[2])

    document = Document.objects.get(id=id)
    document.name = request.POST['name']
    document.place = request.POST['place']
    document.time_calc = time
    document.time_text = request.POST['time_text']
    print(document.save())
    newdoc = None
  else:
    form = DocumentForm()
    newdoc = Document.objects.get(id=id)
 
  form = DocumentForm()
  #documents = Document.objects.filter(time__gte=datetime.datetime.now()).filter(dup='N')
  documents = Document.objects.all()
  return render(request, 'list.html', {'documents': documents, 'form': form, 'newdoc':newdoc})

'''
def update(request, id):
  newdoc = Document.objects.get(id=id)
  form = DocumentForm()
  documents = Document.objects.all()
  return render(request, 'list.html', {'documents': documents, 'form': form, 'newdoc':newdoc})
'''

def delete(request, id):
  # Handle file upload
  Document.objects.filter(id=id).delete()
  return HttpResponseRedirect('/myapp/')

def getText(img):
  b = io.BytesIO()
  img.save(b, format="JPEG")
  #img.show()
  img_bytes = b.getvalue()
  # Instantiates a client
  client = vision.ImageAnnotatorClient()
  image = types.Image(content=img_bytes)
  # Performs label detection on the image file
  response = client.document_text_detection(image=image)
  return response.full_text_annotation 


def text_within(document,x1,y1,x2,y2): 
  text=""
  for page in document.pages:
    for block in page.blocks:
      for paragraph in block.paragraphs:
        for word in paragraph.words:
          for symbol in word.symbols:
            min_x=min(symbol.bounding_box.vertices[0].x,symbol.bounding_box.vertices[1].x,symbol.bounding_box.vertices[2].x,symbol.bounding_box.vertices[3].x)
            max_x=max(symbol.bounding_box.vertices[0].x,symbol.bounding_box.vertices[1].x,symbol.bounding_box.vertices[2].x,symbol.bounding_box.vertices[3].x)
            min_y=min(symbol.bounding_box.vertices[0].y,symbol.bounding_box.vertices[1].y,symbol.bounding_box.vertices[2].y,symbol.bounding_box.vertices[3].y)
            max_y=max(symbol.bounding_box.vertices[0].y,symbol.bounding_box.vertices[1].y,symbol.bounding_box.vertices[2].y,symbol.bounding_box.vertices[3].y)
            if(min_x >= x1 and max_x <= x2 and min_y >= y1 and max_y <= y2):
              text+=symbol.text
              if(symbol.property.detected_break.type==1 or 
                symbol.property.detected_break.type==3):
                text+=' '
              if(symbol.property.detected_break.type==2):
                text+='\t'
              if(symbol.property.detected_break.type==5):
                text+='\n'
  return text    