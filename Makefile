doc:
	sphinx-apidoc -ef -o doc/sphinx/ . learning/
	# Regenerates the skeleton files for the documentation
	# then, you need to `cd doc/sphinx`
	# and `make html`

