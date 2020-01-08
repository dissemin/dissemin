Configuring Repositories
========================

If a repositories and a suitable protocol is programmed, adding is easy.

Repositories
------------

On the admin site in the section ``Deposit`` you find your repositories. You can add and modify them.

You have the following options:

* ``name``: The name of the repository
* ``description``: The description of the repository. This is shown to the user. You cannot use any markup.
* ``url``: URL of the repository, ex: https://arXiv.org/
* ``logo``: A logo of your repository or it's hosting institution. This is shown to the user.
* ``Protocol``: You can choose a protocol to use for the deposit.
* ``OAISource``: The source with which the OaiRecords associated with the deposits are created
* ``username`` and ``password``: If your repository uses password authentication, fill in these values
* ``ap_key``: If your repository uses an API key, fill it in here
* ``endpoint``: URL to call when depositing
* ``enabled``: Here you can enable or disable the repository. Disabling means that the repository refuses to deposit and is not shown to the user.
* ``abstracts_required``: Define wether the user must enter an abstract. Usually abstracts can be fetched from Zotero. Default is: Yes.
* ``ddc``: Here you can choose some DDC for the repository. If no DDC is selected, the user won't be bothered at all.
* ``license choosers``: Here you can add a list of license that your repository accepts. There is no limit, but you should keep your selection moderate. There are the following options:

  * ``transmit_id``: Value to identify the license in the metadata.
  * ``position``: The position in which the corresponding license shall be shown to the user. The behaviour is as for pythons ``list``. The position is per repository. However, using ``-1`` can lead to a higher number. This is kind of a bug, but does no harm. Also some propulated values might not start with a ``0``.
  * ``default``: Check, if you want to use this as default license. In the resulting list on the deposit page, this license is preselected. If you do not set any check, the first license (in alphabetical order) is used. If you check more than one, thie first of the checked license (in alphabetical order) is used. Both cases lead to a warning.

.. note::
    Our implementation of the HAL protocol does not uses licenses or DDC.
    Our implementation of the Zenodo protocol does not use DDC.


DDC
---

On this site you can define DDC classes.
You can choose any of the classes from ``000`` to ``999``.
Leading zeros are automatically added when calling ``__str__`` of object.
Set parent to make a group.
Parent can be any of the class in ``100*i for i in range(10)``.
This groups the DDC when displayed to the user.

.. note::
    You can localize your DDC name, see :doc:`localization` for further information.


Licenses
--------

On the admin site in the section ``Deposit`` you find your licenses. You can add and modify them.

Each license consists of its name and its URI. If your license does not provide a URI, you can use the namespace ``https://dissem.in/deposit/license/``.

.. note::
    You can localize your licenses name, see :doc:`localization` for further information.
