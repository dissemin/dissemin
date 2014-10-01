from django.conf.urls import patterns, url

from papers import views

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),
        url(r'^researcher/(?P<pk>\d+)/$', views.ResearcherView.as_view(), name='researcher'),
        url(r'^researcher/(?P<pk>\d+)/update/$', views.updateResearcher, name='updateResearcher'),
        url(r'^group/(?P<pk>\d+)/$', views.GroupView.as_view(), name='group'),
        url(r'^department/(?P<pk>\d+)/$', views.DepartmentView.as_view(), name='department'),
        url(r'^source/(?P<pk>\d+)/$', views.SourceView.as_view(), name='source'),
        url(r'^source/(?P<pk>\d+)/update/$', views.updateSource, name='updateSource'),
        url(r'^paper/(?P<pk>\d+)/$', views.PaperView.as_view(), name='paper'),
        url(r'^publication/(?P<pk>\d+)/update/$', views.checkPublicationAvailability, name='updatePublication')
)
