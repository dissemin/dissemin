..  _institution:

========================
Configuring Institutions
========================

Configuring institutions is rarely necessary, because their are maintained by the backend, i.e. the institutions are created, merged and deleted automatically.

Identifiers
===========

Each institution has a list of identifiers.
The identifiers with the prefix ``shib:`` are usually added manually.
We use this identifier to match a shibboleth authenticated user with a institution without saving the user institution in the database.
The identifier itself is usually the IdP of the institution and extracted from ``eduPersonTargetedID`` that has the format ``IdP!SP!user_identifier``.

Repositories
============

If a repository is associated to an institution, it will be preselected in case of a deposit and the user has a relation to the institute.
