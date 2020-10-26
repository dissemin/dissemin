========================
Configuring Repositories
========================

Configuring a repository involves not just the repository itself, but other settings related.

Repositories
============

On the admin site in the section ``Deposit`` you find your repositories. You can add and modify them.

You have the following options:

Name
    The name of the repository
Description
    The description of the repository.
    This is shown to the user.
    You cannot use any markup.
URL
    URL of the repository, ex: https://arXiv.org/
Logo
    A logo of your repository or it's hosting institution.
    This is shown to the user.
Protocol
    You can choose a protocol to use for the deposit.
OAISource
    The source with which the OaiRecords associated with the deposits are created
Username and Password
    If your repository uses password authentication, fill in these values
Api_key
    If your repository uses an API key, fill it in here
Endpoint
    URL to call when depositing
Enabled
    Here you can enable or disable the repository.
    Disabling means that the repository refuses to deposit and is not shown to the user.
Abstract required
    Define wether the user must enter an abstract.
    Usually abstracts can be fetched from Zotero.
    Default is: Yes.
Embargo
    Defines wether an embargo is required, optional or not used by the repository.
Green open access service
    Set a custom text shown to the user after depositing in this repository.
    Leave this empty if you do not want a message shown to the user.
    See `Green Open Access Service`_
DDC
    Here you can choose some DDC for the repository.
    If no DDC is selected, the user won't be bothered at all.
    See also: DDC_
License chooser
    Here you can add a list of license that your repository accepts.
    There is no limit, but you should keep your selection moderate
    There are the following options:

    Transmit id
        Value to identify the license in the metadata.
    Position
        The position in which the corresponding license shall be shown to the user.
        The behaviour is as for pythons ``list``.
        The position is per repository. However, using ``-1`` can lead to a higher number.
        This is kind of a bug, but does no harm.
        Also some propulated values might not start with a ``0``.
    Default
        Check, if you want to use this as default license.
        In the resulting list on the deposit page, this license is preselected.
        If you do not set any check, the first license (in alphabetical order) is used.
        If you check more than one, thie first of the checked license (in alphabetical order) is used.
        Both cases lead to a warning.

    See also: Licenses_

.. note::
   Our implementation of the HAL protocol does not uses licenses or DDC.
   Our implementation of the Zenodo protocol does not use DDC.


DDC
===

On this site you can define DDC classes.
You can choose any of the classes from ``000`` to ``999``.
Leading zeros are automatically added when calling ``__str__`` of object.
Set parent to make a group.
Parent can be any of the class in ``100*i for i in range(10)``.
This groups the DDC when displayed to the user.

.. note::
    You can localize your DDC name, see :doc:`../contributing/localization` for further information.


Green Open Access Service
=========================

Here you can set a text about a possible alert after the user deposits into a repository.
The GOAS object requires

* ``heading`` - Heading, e.g. the name of the service.
* ``text`` - A short text displayed to the user.
* ``learn_more_url`` - URL to the webpage with more information about this service

.. note::
    You can localize your Green Open Access Service alerts, see :doc:`../contributing/localization` for further information.

See also :ref:`libraries-services-goa`.

Licenses
========

On the admin site in the section ``Deposit`` you find the licenses. You can add and modify them.

Each license consists of its name and its URI. If your license does not provide a URI, you can use the namespace ``https://dissem.in/deposit/license/``.

.. note::
    You can localize your licenses name, see :doc:`../contributing/localization` for further information.

Creating a Letter of Declaration
================================

The letter of declaration is a sensitive document since it has a legal character.

To maintain the legal character, Dissemin does ship to letter of declaration as it is designed by the repository administration.

There are three ways to handle this:

1. Serve the user the letter and let him fill in everything
2. Fill in the letter with forms
3. Set the letter in python using ``reportlab``

The second way is the least effort and keeps the corporate design easily.

First, inspect the pdf forms with ``pdftk`` using ``pdftk <pdf> dump_data_fields > fields.txt``. Then in ``fields.txt`` you can see the form fields and their names. Identify the names and values.

Next, place the file with a meaningful name in ``deposit/declarations/pdf_templates/``.

Now, some things need to be coded in Python.
In ``deposit/declaration.py`` add a new function.
Let it create a ``list`` of ``(Field name, Value)`` with the necessary values and pass it together with the path to the file to the function ``fill_forms``.
By default, all forms will be replaced with plain text.
If you want to keep the forms, pass ``flatten=False`` als additional parameter.
The return value of ``fill_forms`` is a ``io.BytesIO`` that you just return.

In order to make your new function available to the repository, add the function with a meaningful key to ``REGISTERED_DECLARATION_FUNCTIONS``.

In the admin section you can then add a new letter of declaration.

Here you can set a text about a possible alert after the user deposits into a repository.
The object requires

* ``heading`` - Heading, e.g. 'Contract required!'.
* ``text`` - A short text displayed to the user.
* ``url_text`` - Text of the download button.
* ``url`` - The URL to an online form
* ``function key`` - The function that generates the letter.

.. note::
    You can localize your letter of declaration alerts, see :doc:`../contributing/localization` for further information.

See also :ref:`libraries-services-lod`.

After this is done, you can choose a letter od declaration object for your repository and it will display!
