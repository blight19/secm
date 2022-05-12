from django.contrib import admin
from django.urls import path,include
from django.conf.urls import url
from django.views import static
from django.conf import settings
urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^static/(?P<path>.*)$', static.serve,
      {'document_root': settings.STATIC_ROOT}, name='static'),
]
if "debug_toolbar" in settings.INSTALLED_APPS:

    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns