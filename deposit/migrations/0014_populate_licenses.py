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
        ('deposit', '0013_licensechooser_position'),
    ]

    operations = [
        migrations.RunPython(create_standard_licenses, remove_standard_licenses)
    ]
