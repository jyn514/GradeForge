"""gradeforge URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, re_path
from django.shortcuts import redirect
from django.contrib import admin

from . import views

matches = r'2[0-9]{5}', r'[A-Z]{4}', r'[0-9]{3}', r'[A-Z]?[0-9]{3}[A-Z]?'
combined = r'^(?P<semester>%s)/(?P<department>%s)/(?P<code>%s)/(?P<section>%s)/grades' % matches

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path('^(%s/%s/%s/%s/grades)$' % matches, lambda request, url: redirect('grades.png', permanent=True)),
    re_path(combined + '.png$', views.grade_png),
    re_path(combined + '.csv$', views.grade_csv)
]
