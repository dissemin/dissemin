python manage.py dumpdata --natural-foreign -e papers.OaiSource \
        -e contenttypes \
	-e auth.Permission \
	-o papers/fixtures/test_dump.json
