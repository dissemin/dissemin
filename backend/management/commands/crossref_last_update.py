from django.core.management.base import BaseCommand
from papers.models import OaiSource

class Command(BaseCommand):
    help = 'Get the date and time of the last paper harvested from CrossRef API.'

    def handle(self, *args, **options):
        print(OaiSource.objects.get(identifier='crossref').last_update)
