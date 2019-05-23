from django.db import migrations

def create_standard_licenses(apps, schema_editor):
    """
    Creates a set of standard licenses
    """
    License = apps.get_model('deposit', 'License')

    licenses = [
        {
            'name' : 'Creative Commons 1.0 Universal (CC0 1.0) Public Domain Dedication',
            'uri' : 'https://creativecommons.org/publicdomain/zero/1.0/',
        },
        {
            'name' : 'Creative Commons Attribution 4.0 International (CC BY 4.0)',
            'uri' : 'https://creativecommons.org/licenses/by/4.0/',
        },
        {
            'name' : 'Creative Commons Attribution-ShareAlike 4.0, International (CC BY-SA 4.0)',
            'uri' : 'https://creativecommons.org/licenses/by-sa/4.0/',
        },
        {
            'name' : 'Creative Commons Attribution-NonCommerical 4.0 International (CC BY-NC 4.0)',
            'uri' : 'https://creativecommons.org/licenses/by-nc/4.0/',
        },
        {
            'name' : 'Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0)',
            'uri' : 'http://creativecommons.org/licenses/by-nd/4.0/',
        },
        {
            'name' : 'Free for private use; right holder retains other rights, including distribution',
            'uri' : 'https://dissem.in/deposit/license/zenodo-freetoread-1.0/'
        },
        {
            'name' : 'Other open license',
            'uri' : 'https://dissem.in/deposit/license/other-open/'
        },
        {
            'name' : 'No license',
            'uri' : 'https://dissem.in/deposit/license/no-license/'
        },
    ]

    License.objects.bulk_create([License(**license) for license in licenses])

    # We populate for the existing repos the many2many. That is: Zenodo and OSF

    Repository = apps.get_model('deposit', 'Repository')
    LicenseChooser = apps.get_model('deposit', 'LicenseChooser')

    repos_zenodo = Repository.objects.filter(protocol='ZenodoProtocol')
    for repo in repos_zenodo:
        # Default license
        license = License.objects.get(uri='https://dissem.in/deposit/license/zenodo-freetoread-1.0/')
        LicenseChooser.objects.create(repository=repo, license=license, transmit_id='zenodo-freetoread-1.0', default=True)

        # Non-default licenses
        license_list = [
            ('https://creativecommons.org/publicdomain/zero/1.0/', 'CC0-1.0'),
            ('https://creativecommons.org/licenses/by/4.0/', 'CC-BY-4.0'),
            ('https://creativecommons.org/licenses/by-sa/4.0/', 'CC-BY-SA-4.0'),
            ('https://creativecommons.org/licenses/by-nc/4.0/', 'CC-BY-NC-4.0'),
            ('http://creativecommons.org/licenses/by-nd/4.0/', 'CC-BY-ND-4.0'),
            ('https://dissem.in/deposit/license/other-open/', 'other-open')
        ]
        for license_item in license_list:
            license = License.objects.get(uri=license_item[0])
            LicenseChooser.objects.create(repository=repo, license=license, transmit_id=license_item[1], default=False)

    repos_osf = Repository.objects.filter(protocol='OSFProtocol')
    for repo in repos_osf:
        # Default license
        license = License.objects.get(uri='https://dissem.in/deposit/license/no-license/')
        LicenseChooser.objects.create(repository=repo, license=license, transmit_id='563c1cf88c5e4a3877f9e965', default=True)

        # Non-default licenses
        license_list = [
            ('https://creativecommons.org/publicdomain/zero/1.0/', '563c1cf88c5e4a3877f9e96c'),
            ('https://creativecommons.org/licenses/by/4.0/', '563c1cf88c5e4a3877f9e96a'),
        ]
        for license_item in license_list:
            license = License.objects.get(uri=license_item[0])
            LicenseChooser.objects.create(repository=repo, license=license, transmit_id=license_item[1], default=False)


        

def remove_standard_licenses(apps, schema_editor):
    """
    Removes the licenses
    """
    License = apps.get_model('deposit', 'License')
    License.objects.all().delete()
    LicenseChooser = apps.get_model('deposit', 'LicenseChooser')
    LicenseChooser.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('deposit', '0012_licenses'),
    ]

    operations = [
        migrations.RunPython(create_standard_licenses, remove_standard_licenses)
    ]
