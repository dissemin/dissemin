from haystack import indexes

from .models import Publisher


class PublisherIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    num_papers = indexes.IntegerField(model_attr='stats__num_tot')
    oa_status = indexes.CharField(model_attr='oa_status')
    name = indexes.CharField(model_attr='name')

    def get_model(self):
        return Publisher

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(stats__isnull=False)
