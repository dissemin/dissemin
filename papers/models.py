from django.db import models
from papers.utils import nstr

# Information about the researchers and their groups
class Department(models.Model):
    name = models.CharField(max_length=300)

    def __unicode__(self):
        return self.name

class ResearchGroup(models.Model):
    name = models.CharField(max_length=300)

    def __unicode__(self):
        return self.name

class Researcher(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    department = models.ForeignKey(Department)
    groups = models.ManyToManyField(ResearchGroup)

    # DOI search
    last_doi_search = models.DateTimeField(null=True,blank=True)
    status = models.CharField(max_length=512)
    last_status_update = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.first_name+u' '+self.last_name

    @property
    def papers_by_year(self):
        return self.author_set.order_by('-paper__year')


# Papers matching one or more researchers
class Paper(models.Model):
    title = models.CharField(max_length=1024)
    fingerprint = models.CharField(max_length=64)
    year = models.IntegerField()
    last_modified = models.DateField(auto_now=True)
    def __unicode__(self):
        return self.title
    
class Author(models.Model):
    paper = models.ForeignKey(Paper)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    researcher = models.ForeignKey(Researcher, blank=True, null=True)
    def __unicode__(self):
        return self.first_name+u' '+self.last_name

# Publication of these papers (in journals or conference proceedings)
class Publication(models.Model):
    paper = models.ForeignKey(Paper)
    title = models.CharField(max_length=256)
    issue = models.CharField(max_length=64, blank=True, null=True)
    volume = models.CharField(max_length=64, blank=True, null=True)
    pages = models.CharField(max_length=64, blank=True, null=True)
    date = models.CharField(max_length=128, blank=True, null=True)
    def __unicode__(self):
        result = self.title
        if self.issue or self.volume or self.pages or self.date:
            result += ', '
        if self.issue:
            result += self.issue
        if self.volume:
            result += '('+self.volume+')'
        if self.issue or self.volume:
            result += ', '
        if self.pages:
            result += self.pages+', '
        if self.date:
            result += self.date
        return result

# Rough data extracted through dx.doi.org
class DoiRecord(models.Model):
    doi = models.CharField(max_length=1024, unique=True) # in theory, there is no limit
    about = models.ForeignKey(Paper)
    def __unicode__(self):
        return self.doi

# Rough data extracted through OAI-PMH
class OaiSource(models.Model):
    url = models.CharField(max_length=300)
    name = models.CharField(max_length=100)
    prefix_identifier = models.CharField(max_length=256)
    prefix_url = models.CharField(max_length=256)

    # Fetching properties
    last_update = models.DateTimeField()
    last_status_update = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=512)
    def __unicode__(self):
        return self.name

class OaiRecord(models.Model):
    source = models.ForeignKey(OaiSource)
    identifier = models.CharField(max_length=512, unique=True)
    url = models.CharField(max_length=1024)
    about = models.ForeignKey(Paper)
    def __unicode__(self):
        return self.identifier



