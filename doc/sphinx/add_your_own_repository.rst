=======================
Add your own Repository
=======================

Dissemin not just detects papers behind paywalls, it offers solutions to liberate them.
To achieve this goal with few effort for scientists, they can directly upload a publication into an open repository.
Near the big repositories Zenodo and HAL, they can deposit publications in institutional repositories.
This and the following pages will give you some information at hand how you can add your institutional repository to Dissemin.

As you will learn, this involves not to much effort.
First, we describe the workflow and how the document finds it way into your repository.
Then we explain our metadata, services and give an outline of how we guide you through the integration process.
In a last step we dive into more technical topics, giving precise descriptions of the metadata encoding and how to transfer the file with its metadata.

How a deposit works
===================

Let us assume, that Max Mustermann, a new scientist at your institution, wants to deposit one of his publications in your repository.
He starts by searching for his publications on Dissemin and finds in the list an article namend *A modern view on `God of the Labyrinth`*.
Quickly he finds, that this publicaton is not yet freely available.
Luckily the publisher allows depositing a preprint version into open repositories.
Max decides to make this publication freely available by uploading it in his institutions repository.
He clicks on *Upload*, chooses the right file from his local storage, gives a short subject classification, selects a Creative Commons license and hits finally the upload button.
Dissemin creates a package of metadata and the file Max uploaded and ships it into your repository.
Your repository receives the package, extracts the metadata and the document and creates a new entry in your repository.

Max does not know anything about this, but is happy as he reads, that his publication will soon be available for everyone!
He also reads that he has to sign a letter of declaration.

Meanwhile the repository tells the repository staff that someone created a new entry.
The staff checks the entry.
Everything is fine, except that Max still has to deliver the letter of declaration.
So far, the publication is not yet published, since the repository declared the availability of the document as 'in moderation'.

Max downloads the letter directly from Dissemin.
He reads it carefully and then signs it, as all important information has been filled already.

Some few days pass and the letter arives at the repositoriy staff.
The staff checks the letter, then navigates to the corresponding entry in the repository and changes the availability to 'published'.
The repository sends Max an e-mail that his article *A modern view on `God of the Labyrinth`* is now freely available.

Of course this is just an example with some arbitrary assumptions.
Your local workflow may vary, but we see that you still decide what you publish and what you do not publish.
And it's still you, who defines the requirements.


Metadata
========

Our main data sources are CrossRef and BASE.
Our own data scheme is relatively close to Citeproc / CrossRef.
This gives us the advantage, that---in general---we do not need to ask the user for metadata.
This makes a deposit very little effort.

Basic Metadata
--------------

For a publication we store the following metadata.

.. code::

    abstract
    authors
    date (YYYY-MM-DD)
    document type
    doi
    eissn
    issn
    issue
    journal
    language
    pages
    publisher
    title
    volume

Note however, that we have renamed Citeprocs `container-title` into `journal`.
This has a historical reason, aiming at first at journal articles.

Document types
--------------

We have the following document types:

.. code::

    book
    book-chapter
    dataset
    journal-article
    journal-issue
    poster
    preprint
    proceedings
    proceedings-article
    reference-entry
    report
    thesis
    other

Almost 90 per cent of our deposits are journal articles.

Additional Metadata
--------------------

In addition to the above metadata we can ship out of the box the following:

.. code::

    depositor information (name, email, orcid)
    dewey decimal class
    embargo
    language (with langdetect)
    license
    sherpa romeo id

Services
========

Letter of Declaration
---------------------
Usually institutional repositores require some kind of a letter of declaration from their scientists.
With this letter the scientists declare certain legal statements about the publication and its deposition.

Dissemin does generate these type of letters individually per repositor.
This way the letter fits your needs in terms of design, content and legal character.
We can prefill the letter with all necessary data, so that the depositor just has to sign and send you the letter.

After the deposit the depositors are informed that they need to fill in such a letter and send it to your repository administration.
They can directly download this letter.
Of course they can regenerate this letter at any point in time as long you haven't published the resource.

We provide an :download:`example letter of declaratio n<examples/letter_of_declaration_ulb_darmstadt.pdf>` of ULB Darmstadt, so you have some imagination how it finally looks like.

Green Open Access Service
-------------------------
This means a service where the repository administration supports the researchers, e.g. by publishing on behalf of the researchers, which may include checking the rights, get in contact with the publishers and so on.

Dissemin allows to advertise this service after a successful deposit in your repository. The user will get a notification with a short text and a link that describes your service.


How to add your repository
==========================

If you finally want to connect your repository to Dissemin, then please get in contact with us under `team@dissem.in <mailto:team@dissem.in>`_.

There are a few steps to accomplish this task.

Given our documentation, it is up to you which data you finally ingest in your repository.
Aside from the question, which data you ingest, there is also the question how you ingest the data.
For example, your repository has probably a different granularity when it comes to document types.

We have created a `Workflow <https://github.com/dissemin/dissemin/wiki/Checklist---Add-New-Repository>`_ in our GitHub-Wiki.
It covers the essential steps and is meant to be a guide.
From the template we create an issue that we finally close once the repository has been successfully connected.
In case of need, we add further steps or remove unnessary steps.
