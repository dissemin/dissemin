from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from papers.utils import nstr, iunaccent
from django.utils.translation import ugettext_lazy as _

OA_STATUS_CHOICES = (
        ('OA', _('Open Access')),
        ('OK', _('Allows pre/post prints')),
        ('NOK', _('Forbids pre/post prints')),
        ('UNK', _('Policy unclear')),
   )

PDF_STATUS_CHOICES = [('OK', _('Available')),
                      ('NOK', _('Unavailable'))]

VISIBILITY_CHOICES = [('VISIBLE', _('Visible')),
                      ('CANDIDATE', _('Candidate')),
                      ('DELETED', _('Deleted')),
                      ]

# Information about the researchers and their groups
class Department(models.Model):
    name = models.CharField(max_length=300)

    @property
    def sorted_researchers(self):
        return self.researcher_set.order_by('name')

    def __unicode__(self):
        return self.name

class ResearchGroup(models.Model):
    name = models.CharField(max_length=300)

    def __unicode__(self):
        return self.name

class Researcher(models.Model):
    department = models.ForeignKey(Department)
    groups = models.ManyToManyField(ResearchGroup,blank=True,null=True)
    email = models.EmailField(blank=True,null=True)
    homepage = models.URLField(blank=True, null=True)
    role = models.CharField(max_length=128, null=True, blank=True)

    # DOI search
    last_doi_search = models.DateTimeField(null=True,blank=True)
    status = models.CharField(max_length=512, blank=True, null=True)
    last_status_update = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        first_name = Name.objects.filter(researcher_id=self.id).order_by('id').first()
        if first_name:
            return unicode(first_name)
        return _("Anonymous researcher")

    @property
    def authors_by_year(self):
        return Author.objects.filter(name__researcher_id=self.id).order_by('-paper__year')
    @property
    def names(self):
        return self.name_set.order_by('id')
    @property
    def name(self):
        name = self.names[0]
        if name:
            return name
        else:
            return _("Anonymous researcher")
    @property
    def aka(self):
        return self.names[:2]

MAX_NAME_LENGTH = 256
class Name(models.Model):
    researcher = models.ForeignKey(Researcher, blank=True, null=True, on_delete=models.SET_NULL)
    first = models.CharField(max_length=MAX_NAME_LENGTH)
    last = models.CharField(max_length=MAX_NAME_LENGTH)
    full = models.CharField(max_length=MAX_NAME_LENGTH*2+1, db_index=True)

    unique_together = ('first','last')# TODO Two researchers with the same name is not supported
    
    class Meta:
        ordering = ['last','first']

    @classmethod
    def create(cls, first, last):
        full = iunaccent(first+' '+last)
        return cls(first=first,last=last,full=full)
    def __unicode__(self):
        return '%s %s' % (self.first,self.last)
    @property
    def is_known(self):
        return self.researcher != None

# Papers matching one or more researchers
class Paper(models.Model):
    title = models.CharField(max_length=1024)
    fingerprint = models.CharField(max_length=64)
    year = models.IntegerField()
    last_modified = models.DateField(auto_now=True)
    visibility = models.CharField(max_length=32, default='VISIBLE')

    def __unicode__(self):
        return self.title

    # The two following fields need to be updated after the relevant changes
    # using the methods below.
    oa_status = models.CharField(max_length=32, null=True, blank=True, default='UNK')
    pdf_url = models.URLField(max_length=2048, null=True, blank=True)

    @property
    def prioritary_oai_records(self):
        return self.sorted_oai_records.filter(priority__gt=0)

    @property
    def sorted_oai_records(self):
        return self.oairecord_set.order_by('-priority')

    def update_oa_status(self):
        # Look for publications
        qs = list(self.publication_set.all()[:1])
        if qs:
            self.oa_status = qs[0].oa_status()
        else:
            self.oa_status = 'UNK'
        # Look for automatic OA OAI sources
        records = list(self.oairecord_set.filter(source__oa=True,pdf_url__isnull=False)[:1])
        if records:
            self.oa_status = 'OA'
        self.save()

    # TODO merge these two functions !

    def update_pdf_url(self):
        # TODO: create an oa_status field in each publication so that we optimize queries
        # and can deal with hybrid OA

        # If it is an open access publisher, keep the publisher version
        if self.oa_status == 'OA':
            publications = self.publication_set.filter(journal__publisher__oa_status='OA')[:1]
            if publications:
                self.pdf_url = publications[0].splash_url()
                self.save()
                return
        # otherwise try the OAI sources
        matches = OaiRecord.objects.filter(about=self.id,pdf_url__isnull=False)[:1]
        if matches:
            self.pdf_url = matches[0].pdf_url
        self.save()

# Researcher / Paper binary relation
# TODO: it could be a ManyToMany field...
class Author(models.Model):
    paper = models.ForeignKey(Paper)
    name = models.ForeignKey(Name)
    def __unicode__(self):
        return unicode(self.name)

# Publisher associated with a journal
class Publisher(models.Model):
    romeo_id = models.CharField(max_length=64)
    name = models.CharField(max_length=256)
    alias = models.CharField(max_length=256,null=True,blank=True)
    url = models.URLField(null=True,blank=True)
    preprint = models.CharField(max_length=32)
    postprint = models.CharField(max_length=32)
    pdfversion = models.CharField(max_length=32)
    oa_status = models.CharField(max_length=32, choices=OA_STATUS_CHOICES, default='UNK')
    def __unicode__(self):
        if not self.alias:
            return self.name
        else:
            return self.name+' ('+self.alias+')'
    @property
    def publi_count(self):
        # TODO compute this with aggregates
        # and cache the number of papers for each journal
        count = 0
        for journal in self.journal_set.all():
            count += journal.publication_set.filter(paper__visibility='VISIBLE').count()
        return count
    @property
    def sorted_journals(self):
        return self.journal_set.all().order_by('title')
    @property
    def preprint_conditions(self):
        return self.publisherrestrictiondetail_set.filter(applies_to='preprint')
    @property
    def postprint_conditions(self):
        return self.publisherrestrictiondetail_set.filter(applies_to='postprint')
    @property
    def pdfversion_conditions(self):
        return self.publisherrestrictiondetail_set.filter(applies_to='pdfversion')
    def change_oa_status(self, new_oa_status):
        self.oa_status = new_oa_status
        self.save()
        papers = Paper.objects.filter(publication__journal__publisher=self.pk)
        for p in papers:
            p.update_oa_status()

# Journal data retrieved from RoMEO
class Journal(models.Model):
    title = models.CharField(max_length=256)
    last_updated = models.DateTimeField(auto_now=True)
    issn = models.CharField(max_length=10, blank=True, null=True, unique=True)
    publisher = models.ForeignKey(Publisher)
    def __unicode__(self):
        return self.title
    class Meta:
        ordering = ['title']

class PublisherCondition(models.Model):
    publisher = models.ForeignKey(Publisher)
    text = models.CharField(max_length=1024)
    def __unicode__(self):
        return self.text

class PublisherCopyrightLink(models.Model):
    publisher = models.ForeignKey(Publisher)
    text = models.CharField(max_length=256)
    url = models.URLField()
    def __unicode__(self):
        return self.text

class PublisherRestrictionDetail(models.Model):
    publisher = models.ForeignKey(Publisher)
    text = models.CharField(max_length=256)
    applies_to = models.CharField(max_length=32)
    def __unicode__(self):
        return self.text

class Disambiguation(models.Model):
    publications = models.ManyToManyField('Publication')
    title = models.CharField(max_length=512)
    issn = models.CharField(max_length=128)
    unique_together = ('title', 'issn')

class DisambiguationChoice(models.Model):
    about = models.ForeignKey(Disambiguation)
    title = models.CharField(max_length=512)
    issn = models.CharField(max_length=128)

# Publication of these papers (in journals or conference proceedings)
class Publication(models.Model):
    paper = models.ForeignKey(Paper)
    pubtype = models.CharField(max_length=64)
    title = models.CharField(max_length=256) # this is actually the *journal* title
    journal = models.ForeignKey(Journal, blank=True, null=True)
    issue = models.CharField(max_length=64, blank=True, null=True)
    volume = models.CharField(max_length=64, blank=True, null=True)
    pages = models.CharField(max_length=64, blank=True, null=True)
    date = models.CharField(max_length=128, blank=True, null=True)
    publisher = models.CharField(max_length=256, blank=True, null=True)
    doi = models.CharField(max_length=1024, unique=True, blank=True, null=True) # in theory, there is no limit
    def oa_status(self):
        if self.journal:
            return self.journal.publisher.oa_status
        else:
            return 'UNK'

    def splash_url(self):
        if self.doi:
            return 'http://dx.doi.org/'+self.doi

    def details_to_str(self):
        result = ''
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

    def __unicode__(self):
        return self.title+self.details_to_str()

# Rough data extracted through OAI-PMH
class OaiSource(models.Model):
    identifier = models.CharField(max_length=300)
    name = models.CharField(max_length=100)
    oa = models.BooleanField(default=False)
    priority = models.IntegerField(default=1)

    # Fetching properties
    last_status_update = models.DateTimeField(auto_now=True)
    def __unicode__(self):
        return self.name

class OaiRecord(models.Model):
    source = models.ForeignKey(OaiSource)
    about = models.ForeignKey(Paper)

    identifier = models.CharField(max_length=512, unique=True)
    splash_url = models.URLField(max_length=1024, null=True, blank=True)
    pdf_url = models.URLField(max_length=1024, null=True, blank=True)
    description = models.TextField(null=True,blank=True)

    # Cached version of source.priority
    priority = models.IntegerField(default=1)
    def update_priority(self):
        self.priority = self.source.priority
        self.save(update_fields=['priority'])

    last_update = models.DateTimeField(auto_now=True)
    def __unicode__(self):
        return self.identifier


