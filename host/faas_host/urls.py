from django.contrib import admin
from django.urls import path

from invoker.views import invoke

urlpatterns = [
    path("admin/", admin.site.urls),
    path("invoke/", invoke),
]