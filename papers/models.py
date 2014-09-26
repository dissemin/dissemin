from django.db import models

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
    last_doi_search = models.DateTimeField(null=True,blank=True)

    def __unicode__(self):
        return self.first_name+u' '+self.last_name

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
    issue = models.IntegerField(blank=True, null=True)
    volume = models.IntegerField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)

# Rough data extracted through dx.doi.org
class DoiRecord(models.Model):
    doi = models.CharField(max_length=1024, unique=True) # in theory, there is no limit
    about = models.ForeignKey(Paper)
    def __unicode__(self):
        return self.doi

class DoiStatement(models.Model):
    record = models.ForeignKey(DoiRecord)
    prop = models.CharField(max_length=128)
    value = models.CharField(max_length=1024)
    def __unicode__(self):
        return prop+': '+value

# Rough data extracted through OAI-PMH
class OaiSource(models.Model):
    url = models.CharField(max_length=300)
    name = models.CharField(max_length=100)
    last_update = models.DateTimeField()
    def __unicode__(self):
        return self.name

class OaiRecord(models.Model):
    source = models.ForeignKey(OaiSource)
    identifier = models.CharField(max_length=512, unique=True)
    about = models.ForeignKey(Paper)
    def __unicode__(self):
        return self.identifier

class OaiStatement(models.Model):
    record = models.ForeignKey(OaiRecord)
    prop = models.CharField(max_length=128)
    value = models.CharField(max_length=8192)
    def __unicode__(self):
        return self.prop+u': '+self.value


