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

    def __unicode__(self):
        return self.first_name+u' '+self.last_name

# Papers matching one or more researchers
class Paper(models.Model):
    title = models.CharField(max_length=500)
    doi = models.CharField(max_length=1024, blank=True, null=True) # in theory, there is no limit
    def __unicode__(self):
        return self.title
    
class Author(models.Model):
    paper = models.ForeignKey(Paper)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    researcher = models.ForeignKey(Researcher, blank=True, null=True)
    def __unicode__(self):
        return self.first_name+u' '+self.last_name

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
    about = models.ForeignKey(Paper, blank=True, null=True)
    def __unicode__(self):
        return self.identifier

class OaiStatement(models.Model):
    record = models.ForeignKey(OaiRecord)
    prop = models.CharField(max_length=128)
    value = models.CharField(max_length=8192)
    def __unicode__(self):
        return self.prop+u': '+self.value


