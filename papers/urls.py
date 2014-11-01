from django.conf.urls import patterns, url

from papers import views

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),
        url(r'^researcher/(?P<pk>\d+)/$', views.ResearcherView.as_view(), name='researcher'),
        url(r'^researcher/(?P<pk>\d+)/update/$', views.updateResearcher, name='updateResearcher'),
        url(r'^researcher/(?P<pk>\d+)/updateoai/$', views.updateResearcherOAI, name='updateResearcherOAI'),
        url(r'^group/(?P<pk>\d+)/$', views.GroupView.as_view(), name='group'),
        url(r'^department/(?P<pk>\d+)/$', views.DepartmentView.as_view(), name='department'),
        url(r'^source/(?P<pk>\d+)/$', views.SourceView.as_view(), name='source'),
        url(r'^paper/(?P<pk>\d+)/$', views.PaperView.as_view(), name='paper'),
        url(r'^journal/(?P<pk>\d+)/$', views.JournalView.as_view(), name='journal'),
        url(r'^publisher/(?P<pk>\d+)/$', views.PublisherView.as_view(), name='publisher')
)
