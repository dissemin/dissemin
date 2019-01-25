doc:
	sphinx-apidoc -ef -o doc/sphinx/modules/ . */migrations/*
	# Regenerates the skeleton files for the documentation
	# then, you need to `cd doc/sphinx`
	# and `make html`

coverage:
	# Requires the pip "coverage" package
	python -m coverage run --source='.' manage.py test
	python -m coverage html

