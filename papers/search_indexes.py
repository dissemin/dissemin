from haystack import indexes
from papers.utils import remove_diacritics

from .models import Paper


class PaperIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='title')
    pubdate = indexes.DateField(model_attr='pubdate')
    combined_status = indexes.CharField(model_attr='combined_status')
    doctype = indexes.CharField(model_attr='doctype')
    visible = indexes.BooleanField(model_attr='visible')
    oa_status = indexes.CharField(model_attr='oa_status')
    availability = indexes.CharField()

    #: Names of the authors
    authors_full = indexes.MultiValueField()
    authors_last = indexes.MultiValueField()

    #: IDs of researchers
    researchers = indexes.MultiValueField()

    #: IDs of departments of researchers
    departments = indexes.MultiValueField()

    #: ID of publisher
    publisher = indexes.IntegerField(null=True)

    #: ID of journal
    journal = indexes.IntegerField(null=True)

    def get_model(self):
        return Paper

    def get_updated_field(self):
        return "last_modified"

    def prepare_text(self, obj):
        return remove_diacritics(obj.title+' '+(' '.join(
            self.prepare_authors_full(obj))))

    def prepare_authors_full(self, obj):
        # the 'full' field is already clean (no diacritics)
        return [a['name']['full'] for a in obj.authors_list]

    def prepare_authors_last(self, obj):
        return [remove_diacritics(a['name']['last']) for a in obj.authors_list]

    def prepare_availability(self, obj):
        return 'OK' if obj.pdf_url else 'NOK'

    def prepare_researchers(self, obj):
        return [a['researcher_id'] for a in obj.authors_list
                if 'researcher_id' in a]

    def prepare_departments(self, obj):
        return list(obj.researchers.filter(department__isnull=False)
                    .values_list('department', flat=True))

    def prepare_publisher(self, obj):
        for r in obj.oairecords:
            if r.publisher_id:
                return r.publisher_id

    def prepare_journal(self, obj):
        for r in obj.oairecords:
            if r.journal_id:
                return r.journal_id
