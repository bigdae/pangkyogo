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
import numpy as np

MONSTER = "MONSTER"
EGG     = "EGG"
KNOWN   = "KNOWN"

def sendMessage():
    my_token = '727599178:AAH_ksTAfbHK7PKt4fJq28Dj91slG3BVPXQ'
    ###
    bot = telegram.Bot(token = my_token)
    bot.sendMessage(chat_id = '@pangkyogo', text=text_message)

def loadDocument():
    return Document.objects.all()
    #return Document.objects.filter(time_original__gte=datetime.datetime.now())#.filter(dup='N')

def resize(file):
    img = Image.open(file)
    new_height = 1280
    new_width  = int(new_height * img.width / img.height)
    return img.resize((new_width, new_height), Image.ANTIALIAS)

def list(request):
    form = DocumentForm()
    documents = loadDocument()
    return render(request, 'list.html', {'documents': documents, 'form': form})

def getTargetTypeByTime(egg_time, monster_time):
    if monster_time.count(":") > 1:
      return MONSTER
    elif egg_time.count(":") > 1:
      return EGG
    return KNOWN


def extractText(request):
    # Handle file upload
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)

        if form.is_valid():
            # variable initial
            place = egg_time = monster_time = monster_name = ""

            # time for file
            time_original = datetime.datetime.strptime(request.POST['lastmodified'], '%Y-%m-%d %H:%M:%S')
            time_calc = time_original

            # image resize
            img = resize(request.FILES['docfile'])

            # extract text
            document = getText(img)

            # find place and time
            place = text_within(document,150,80,1000,166).replace("\n", "")
            egg_time = text_within(document,200,240,1000,333).replace("\n","")
            monster_time = text_within(document,200,690,1000,818).replace("\n","")
            egg_time = re.sub('[^0-9:]', '', egg_time)
            monster_time = re.sub('[^0-9:]', '', monster_time)

            # find target type by time : egg, monster
            target_type = getTargetTypeByTime(egg_time, monster_time)

            # monster name find
            if target_type == MONSTER:
                monster_name = text_within(document,0,150,1200,460)
            elif target_type == EGG:
                monster_name = EGG
            else:
                monster_name = KNOWN


            # calculate minutes
            time_arr = []

            if target_type == MONSTER:
                time_arr =  [int(i) for i in monster_time.split(":")]
            elif target_type == EGG:
                time_arr =  [int(i) for i in egg_time.split(":")]
                time_calc = time_calc + datetime.timedelta(minutes=45)
            time_calc = time_calc + datetime.timedelta(hours=time_arr[0])
            time_calc = time_calc + datetime.timedelta(minutes=time_arr[1])
            time_calc = time_calc + datetime.timedelta(seconds=time_arr[2])

            newdoc = Document(docfile = request.FILES['docfile']
                            , name=monster_name
                            , place=place
                            , time_original=time_original
                            , time_calc=time_calc
                            , time_text=":".join(str(e) for e in time_arr))

            # duplication check
            if len(Document.objects.filter(time_original__gte=datetime.datetime.now()).filter(place=place)) > 0:
                newdoc.dup = "Y"
            else:
                newdoc.dup = "N"

            newdoc.save()
            documents = loadDocument()
            form = DocumentForm() # A empty, unbound form
            return render(request, 'list.html', {'documents': documents, 'form': form, 'newdoc':newdoc})

def update(request, id):
  if request.method == 'POST':
    id = request.POST['id']
    name = request.POST['name'].upper()
    time_calc = Document.objects.get(id=id).time_original
    
    time_text = request.POST['time_text']
    time_arr =  [int(i) for i in time_text.split(":")]
    if name.startswith("EGG"):
      time_calc = time_calc + datetime.timedelta(minutes=45)
    time_calc = time_calc + datetime.timedelta(hours=time_arr[0])
    time_calc = time_calc + datetime.timedelta(minutes=time_arr[1])
    time_calc = time_calc + datetime.timedelta(seconds=time_arr[2])

    document = Document.objects.get(id=id)
    document.name = request.POST['name']
    document.place = request.POST['place']
    document.time_calc = time_calc
    document.time_text = request.POST['time_text']
    print(document.save())
    newdoc = None
  else:
    form = DocumentForm()
    newdoc = Document.objects.get(id=id)
 
  form = DocumentForm()
  documents = loadDocument()
  return render(request, 'list.html', {'documents': documents, 'form': form, 'newdoc':newdoc})


def delete(request, id):
  Document.objects.filter(id=id).delete()
  return HttpResponseRedirect('/myapp/')

def getText(img):
  b = io.BytesIO()
  img.save(b, format="JPEG")
  img_bytes = b.getvalue()
  client = vision.ImageAnnotatorClient()
  image = types.Image(content=img_bytes)
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
