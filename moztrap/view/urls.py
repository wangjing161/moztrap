"""
MozTrap root URLconf.

"""
from django.conf.urls.defaults import patterns, url, include
from django.conf.urls.static import static
from django.conf import settings

from django.contrib import admin

admin.autodiscover()

import session_csrf
session_csrf.monkeypatch()


urlpatterns = patterns(
    "",
    url(r"^$", "moztrap.view.views.home", name="home"),

    # runtests ---------------------------------------------------------------
    url(r"^runtests/", include("moztrap.view.runtests.urls")),

    # users ------------------------------------------------------------------
    url(r"^users/", include("moztrap.view.users.urls")),

    # manage -----------------------------------------------------------------
    url(r"^manage/", include("moztrap.view.manage.urls")),

    # results ----------------------------------------------------------------
    url(r"^results/", include("moztrap.view.results.urls")),

    # admin ------------------------------------------------------------------
    url(r"^admin/", include(admin.site.urls)),

    # browserid --------------------------------------------------------------
    url(r"^browserid/", include("moztrap.view.users.browserid_urls")),

) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
