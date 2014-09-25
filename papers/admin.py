from django.contrib import admin
from papers.models import *

# Register your models here.
admin.site.register(Department)
admin.site.register(ResearchGroup)
admin.site.register(Researcher)
admin.site.register(Paper)
admin.site.register(Author)
admin.site.register(OaiSource)
admin.site.register(OaiRecord)
admin.site.register(OaiStatement)

