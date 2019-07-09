import os
from django.core.management.base import BaseCommand

from deposit.conftest import metadata_publications
from deposit.forms import BaseMetadataForm
from deposit.models import DDC
from deposit.sword.protocol import SWORDMETSMODSProtocol
from dissemin.settings import BASE_DIR
from dissemin.settings import DEBUG
from conftest import LoadJSON


class Command(BaseCommand):
    help = 'Creates MODS XML example files and moves them to sphinx documentation and creates a new sphinx file with download links. Never run this method on a production system as it might severly change your data! Ideally run this method on an empty database.'

    def handle(self, *args, **options):
        # Prevent from running in production mode
        if DEBUG is False:
            print("This method can not be run on production systems.")
            return

        l = LoadJSON()
        s = SWORDMETSMODSProtocol(None)
        ddcs = DDC.objects.all()
        data = dict()
        
        rst = ''
        f_path = os.path.join(BASE_DIR, 'doc', 'sphinx', 'examples', 'mods')
        os.makedirs(f_path, exist_ok=True)

        for metadata in metadata_publications:
            load = l.load_upload(metadata)
            p = load['paper']
            o = load['oairecord']
            s.paper = p
            if o.description is None:
                data['abstract'] = load['abstract']
            else:
                data['abstract'] = o.description
            data['ddc'] = [ddc for ddc in DDC.objects.filter(number__in=load['ddc'])]
            f = BaseMetadataForm(paper=p, ddcs=ddcs, data=data)
            f.is_valid()
            mods = s._get_xml_metadata(form=f)
            mets = SWORDMETSMODSProtocol._get_mets(mods)
            f_name =os.path.join(f_path, metadata + '.xml')
            with open(f_name, 'w') as fout:
                fout.write(mets)
            rst += '* :download:`' + metadata + ' <examples/mods/' + metadata + '.xml>`\n'

        with open(os.path.join(f_path, 'examples_mods.rst'), 'w') as fout:
            fout.write(rst)
            




