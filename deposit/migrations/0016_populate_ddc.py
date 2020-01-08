from django.db import migrations

def create_ddc(apps, schema_editor):
    """
    Creates a set of standard licenses
    """
    DDC = apps.get_model('deposit', 'DDC')

    ddcs = [
        {
            'number': 0,
            'name': 'Computer science, knowledge & systems',
        },
        {
            'number': 10,
            'name': 'Bibliographies',
        },
        {
            'number': 20,
            'name': 'Library & information sciences',
        },
        {
            'number': 30,
            'name': 'Encyclopedias & books of facts',
        },
        # 40 is unassigned, hence left out
        {
            'number': 50,
            'name': 'Magazines, journals & serials',
        },
        {
            'number': 60,
            'name': 'Associations, organizations & museums',
        },
        {
            'number': 70,
            'name': 'News media, journalism & publishing',
        },
        {
            'number': 80,
            'name': 'Quotations',
        },
        {
            'number': 90,
            'name': 'Manuscripts & rare books',
        },
        {
            'number': 100,
            'name': 'Philosophy',
        },
        {
            'number': 110,
            'name': 'Metaphysics',
        },
        {
            'number': 120,
            'name': 'Epistemology',
        },
        {
            'number': 130,
            'name': 'Parapsychology & occultism',
        },
        {
            'number': 140,
            'name': 'Philosophical schools of thought',
        },
        {
            'number': 150,
            'name': 'Psychology',
        },
        {
            'number': 160,
            'name': 'Philosophical logic',
        },
        {
            'number': 170,
            'name': 'Ethics',
        },
        {
            'number': 180,
            'name': 'Ancient, medieval & eastern philosophy',
        },
        {
            'number': 190,
            'name': 'Modern western philosophy',
        },
        {
            'number': 200,
            'name': 'Religion',
        },
        {
            'number': 210,
            'name': 'Philosophy & theory of religion',
        },
        {
            'number': 220,
            'name': 'The Bible',
        },
        {
            'number': 230,
            'name': 'Christianity',
        },
        {
            'number': 240,
            'name': 'Christian practice & observance',
        },
        {
            'number': 250,
            'name': 'Christian pastoral practice & religious orders',
        },
        {
            'number': 260,
            'name': 'Christian organization, social work & worship',
        },
        {
            'number': 270,
            'name': 'History of Christianity',
        },
        {
            'number': 280,
            'name': 'Christian denominations',
        },
        {
            'number': 290,
            'name': 'Other religions',
        },
        {
            'number': 300,
            'name': 'Social sciences, sociology & anthropology',
        },
        {
            'number': 310,
            'name': 'Statistics',
        },
        {
            'number': 320,
            'name': 'Political science',
        },
        {
            'number': 330,
            'name': 'Economics',
        },
        {
            'number': 340,
            'name': 'Law',
        },
        {
            'number': 350,
            'name': 'Public administration & military science',
        },
        {
            'number': 360,
            'name': 'Social problems & social services',
        },
        {
            'number': 370,
            'name': 'Education',
        },
        {
            'number': 380,
            'name': 'Commerce, communications & transportation',
        },
        {
            'number': 390,
            'name': 'Customs, etiquette & folklore',
        },
        {
            'number': 400,
            'name': 'Language',
        },
        {
            'number': 410,
            'name': 'Linguistics',
        },
        {
            'number': 420,
            'name': 'English & Old English languages',
        },
        {
            'number': 430,
            'name': 'German & related languages',
        },
        {
            'number': 440,
            'name': 'French & related languages',
        },
        {
            'number': 450,
            'name': 'Italian, Romanian & related languages',
        },
        {
            'number': 460,
            'name': 'Spanish, Portuguese, Galician',
        },
        {
            'number': 470,
            'name': 'Latin & Italic languages',
        },
        {
            'number': 480,
            'name': 'Classical & modern Greek languages',
        },
        {
            'number': 490,
            'name': 'Other languages',
        },
        {
            'number': 500,
            'name': 'Science',
        },
        {
            'number': 510,
            'name': 'Mathematics',
        },
        {
            'number': 520,
            'name': 'Astronomy',
        },
        {
            'number': 530,
            'name': 'Physics',
        },
        {
            'number': 540,
            'name': 'Chemistry',
        },
        {
            'number': 550,
            'name': 'Earth sciences & geology',
        },
        {
            'number': 560,
            'name': 'Fossils & prehistoric life',
        },
        {
            'number': 570,
            'name': 'Biology',
        },
        {
            'number': 580,
            'name': 'Plants (Botany)',
        },
        {
            'number': 590,
            'name': 'Animals (Zoology)',
        },
        {
            'number': 600,
            'name': 'Technology',
        },
        {
            'number': 610,
            'name': 'Medicine & health',
        },
        {
            'number': 620,
            'name': 'Engineering',
        },
        {
            'number': 630,
            'name': 'Agriculture',
        },
        {
            'number': 640,
            'name': 'Home & family management',
        },
        {
            'number': 650,
            'name': 'Management & public relations',
        },
        {
            'number': 660,
            'name': 'Chemical engineering',
        },
        {
            'number': 670,
            'name': 'Manufacturing',
        },
        {
            'number': 680,
            'name': 'Manufacture for specific uses',
        },
        {
            'number': 690,
            'name': 'Construction of buildings',
        },
        {
            'number': 700,
            'name': 'Arts',
        },
        {
            'number': 710,
            'name': 'Area planning & landscape architecture',
        },
        {
            'number': 720,
            'name': 'Architecture',
        },
        {
            'number': 730,
            'name': 'Sculpture, ceramics & metalwork',
        },
        {
            'number': 740,
            'name': 'Graphic arts & decorative arts',
        },
        {
            'number': 750,
            'name': 'Painting',
        },
        {
            'number': 760,
            'name': 'Printmaking & prints',
        },
        {
            'number': 770,
            'name': 'Photography, computer art, film, video',
        },
        {
            'number': 780,
            'name': 'Music',
        },
        {
            'number': 790,
            'name': 'Sports, games & entertainment',
        },
        {
            'number': 800,
            'name': 'Literature, rhetoric & criticism',
        },
        {
            'number': 810,
            'name': 'American literature in English',
        },
        {
            'number': 820,
            'name': 'English & Old English literatures',
        },
        {
            'number': 830,
            'name': 'German & related literatures',
        },
        {
            'number': 840,
            'name': 'French & related literatures',
        },
        {
            'number': 850,
            'name': 'Italian, Romanian & related literatures',
        },
        {
            'number': 860,
            'name': 'Spanish, Portuguese, Galician literatures',
        },
        {
            'number': 870,
            'name': 'Latin & Italic literatures',
        },
        {
            'number': 880,
            'name': 'Classical & modern Greek literatures',
        },
        {
            'number': 890,
            'name': 'Other literatures',
        },
        {
            'number': 900,
            'name': 'History',
        },
        {
            'number': 910,
            'name': 'Geography & travel',
        },
        {
            'number': 920,
            'name': 'Biography & genealogy',
        },
        {
            'number': 930,
            'name': 'History of ancient world (to ca. 499)',
        },
        {
            'number': 940,
            'name': 'History of Europe',
        },
        {
            'number': 950,
            'name': 'History of Asia',
        },
        {
            'number': 960,
            'name': 'History of Africa',
        },
        {
            'number': 970,
            'name': 'History of North America',
        },
        {
            'number': 980,
            'name': 'History of South America',
        },
        {
            'number': 990,
            'name': 'History of other areas',
        },
    ]
    DDC.objects.bulk_create([DDC(**ddc) for ddc in ddcs])
    # Next we set the FK to make grouping
    parents = DDC.objects.filter(number__in=range(0, 1000, 100))
    ddcs = DDC.objects.all()
    for ddc in ddcs:
        ddc.parent = parents[ddc.number//100]
    DDC.objects.bulk_update(ddcs, ['parent'])


def remove_ddc(apps, schema_editor):
    """
    Removes the prefilled ddc
    """
    DDC= apps.get_model('deposit', 'DDC')
    DDC.objects.filter(number__in=[i for i in range(0, 1000, 10)]).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('deposit', '0015_ddc'),
    ]

    operations = [
        migrations.RunPython(create_ddc, remove_ddc)
    ]
