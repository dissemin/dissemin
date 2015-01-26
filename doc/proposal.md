> *For reviewers: This template is using markdown, plain text formatting syntax. For more information, please contact us at or15-program-chairs@googlegroups.com*

This proposal can be viewed with proper formatting here:
https://github.com/wetneb/dissemin/blob/master/doc/proposal.md

## **Dissem.in: Towards One-Click Deposits for Green Open Access**

Antonin Delpeuch, University of Cambridge, Trinity College and École Normale Supérieure (Paris), antonin@delpeuch.eu

### **Session Type (select one)**

>* ~~Panel~~
* **Presentation**

### **Abstract**
> Summary of your proposal; maximum 200 words. The abstract should be a concise statement of the problem, approach and conclusions of the work described. You can copy and paste this into the submission system later.

Many researchers do not upload their papers to any open repository, for instance because the deposit process is too
complicated or because they are not sure to be allowed to do so by their publishers.
We present a new web platform designed to help researchers upload their papers to an open repository. Based on various metadata sources,
we create a publications list that can be filtered by publisher policy and full text availability in major repositories.
This enables us to get a list of publications that are not available
in any repository yet, but that could safely be uploaded according to the publisher's policy.
The metadata gathered by our system could then be reused to speed up the deposit of these papers, using the SWORD protocol.
We discuss the technical challenges behind the project and demonstrate the system itself.

### **Conference Themes**
> Select the conference theme(s) your proposal best addresses:

* **Supporting Open Scholarship, Open Science, and Cultural Heritage**
* ~~Managing Research (and Open) Data~~
* **Integrating with External Systems**
* **Re-using Repository Content**
* ~~Exploring Metrics and Assessment~~
* **Managing Rights**
* ~~Developing and Training Staff~~
* ~~Building the Perfect Repository~~

### **Keywords**
> List 3-4 key terms or phrases that describe the subject of the proposal.}

green open access, open access policy enforcement, open access statistics, institutional repositories

### **Audience**
> Tell us in a sentence or two who is the likely audience for this (Some examples might be repository managers, developers, data producers, librarians, etc.)

**Repository managers** can be interested in this tool to populate their repository.
**Libriarians and open access officers** in universities or funders could use it to enforce their own open access policy.
**Developpers** can be interested in the technical challenges behind the project.

### Background
> How does your submission address the conference themes or the overarching topic of open repositories?

Our web platform is designed to help researchers populate open repositories faster, by reusing existing metadata.
Although it is not a repository in itself, it uses the protocols
(OAI-PMH, SWORD, and various other APIs) and the technology
(author disambiguation, metadata cleaning) of open repositories and harvesters.

### **Presentation content**
> Tell us what you will (and won't) cover in the presentation. Why will your topic be of interest to the intended audience? Include figures and images if they will help reviewers evaluate the proposal content. If you are proposing a panel, outline how you envision each panelist contributing to the overall discussion. Proposals should be 2-4 pages in length and in English.


#### 1. Introduction to the problem.

Green open access is less expensive than gold open access, but the time it costs researchers to
upload their papers to repositories is far from negligible. In the case where administrative staff
is available to help them complete their submissions, these costs are estimated to 33 GBP per
paper according to a recent study [1]. But the time required is not the only hurdle: researchers
need to understand the policies of their publishers and find the repository that suits their needs.

Universities adopt open access policies to foster green open access, but lack tools to enforce them.
When a university runs an institutional repository, it is easy to get the list of publications in the
repository, but it is much harder to find the missing ones without requiring the researchers to
report them manually. Neither researchers nor universities have a simple way to get the list of
their publications that are not available in any repository.

Our aim is to solve this problem, by building a system that leverages various metadata sources
to get the publications list of researchers. The tool helps researchers to upload their
papers and universities to measure the availability of their research output in open repositories.
We first give a quick tour of the tool, implemented as a web platform. Then, we review the technical
and administrative challenges behind the project. Finally, we hope that the questions and reactions
of the audience will help us to improve the tool and to adapt it to the needs of the community.

#### 2. Overview of the system

Our web platform allows to browse the publications of researchers within a university. These
publications can be filtered using two criteria: publisher policy and full text availability.

##### 2.1 Publisher policy

We use the SHERPA/RoMEO API to fetch publisher policies.

We divide the policies into four categories:
* Open access: when the paper is published in an open access journal. Note that this
  does not include hybrid open access schemes: a paper published in a traditional
  journal and for which a paid open access option has been purchased will not fall
  into this category.
  The reason for this choice is mainly technical: we have no simple way to detect
  if one particular publication in a closed journal is freely available.
* Pre/post-prints allowed: when the publisher allows the author to upload
  some version of the paper to a repository. SHERPA/RoMEO makes a distinction
  between three versions of a paper: the paper as it was submitted to the journal,
  after revisions suggested by the reviewers and after proper publication.
  A journal falls in this category when any of the three versions can be uploaded.
* Pre/post-prints forbidden: when all of the three versions mentionned above
  cannot be uploaded. This is rather rare.
* Unknown policy: in all other cases.

These classes can be easily identified using the following symbols:

![Screenshot of the search criteria](https://raw.githubusercontent.com/wetneb/dissemin/master/doc/img/policy.png)

##### 2.2 Full text availability

Full text availability is detected by searching for the articles in open repositories.
Our goal is to detect only copies present in open repositories, and not on personal
homepages, to foster the use of repositories. Incidentally, it is also much easier
to discover automatically a preprint when it is stored in an open repository.

The full text availability is presented with a symbol:

![Screenshot of the availability criteria](https://raw.githubusercontent.com/wetneb/dissemin/master/doc/img/availability.png)

##### 2.3. Combination of the two criteria

These two criteria can be visually combined to help researchers grasp instantly
the status of their publications, as in the following example:

![Screenshot of the publications list](https://raw.githubusercontent.com/wetneb/dissemin/master/doc/img/publist.png)

The two first papers were not found in any repository, but their publisher's policy indicates that they could be made available. They would then be marked as the third paper. The fourth paper is published in an open access journal and
is hence considered available. The last paper is also available and the publisher policy is marked as unknown.

#### 3. Demo

A prototype is running and encompasses some departments of the École Normale Supérieure (ENS), a french university.
It is online here:

http://ens.dissem.in/

The source code is released under the GNU General Public License version 2 or later, and can be found at:

http://github.com/wetneb/dissemin

#### 3. Technical details

##### 3.1. Metadata sources

We use two different tools to discover preprints:
* Our own OAI-PMH harvester, covering 8 millions of papers from the major open repositories
  such as arXiv, HAL and PubMed Central. The harvester acts as a proxy: it exposes
  the metadata it harvests as an OAI-PMH source, with additional metadata (OAI sets) to enable
  a search by author name.
  Papers discovered using OAI-PMH are added to the publications list and marked as
  available if the full text is also available from the OAI-PMH provider.
* Bielefeld Academic Search Engine (through its API): this service covers a large
  collection of preprints, but the metadata it serves is not always very reliable,
  so we cannot afford to import systematically all the search results matching a given
  author in our database.
  However, if we have discovered a publication from another source and BASE can find
  a preprint for it, we mark this publication as available.
* A CORE interface is being implemented.

Policies are fetched from SHERPA/RoMEO, through its API. We also plan to use Heloise, a similar service
run by CCSD.

##### 3.2. Author disambiguation

We perform automatic author name disambiguation to get accurate publications list for each researcher.
The problem can be formulated as follows. Given a list of researchers for each department in a university,
and given a list of millions of papers fetched from various sources, find the papers corresponding to our
known researchers.
Our approach is a two-stage algorithm, similar to the AuthorMagic heuristics used in the Invenio platform [2].

* First, papers sharing a similar author name are grouped by similarity, so that two papers in the same
  group have most likely be authored by the same researcher.
* Second, the relevance of each group of papers for our target researcher is estimated, and a cluster
  of similar papers is added to the publications list if the majority of these papers are considered
  relevant to the researcher.

###### 3.2.1. Similarity prediction

The similarity between two papers is estimated using a linear Support Vector Machine with the following features:
* Number of common authors
* Similarity between the affiliations of the authors, if they are available
* Similarity between the titles
* Similarity between the journal titles
For the last three features, the similarity of two strings is measured by the score of the common words
for a unigram language model.

###### 3.2.2. Relevance prediction

The relevance of a paper relative to a target researcher is also estimated using a Support Vector Machine.
Its features are computed using a topic model built for each department: it is a unigram language model trained
on the papers of this department only.
The topic relevance of the title, the journal title, the keywords and the institution are used as features, as well
as the number of author that could refer to a researcher in the university.

### **Conclusion**
> Summarize the take-home message from the presentation. What are the main points? It would be great if this were a part of the conversation around the conference theme.

A very large amount of metadata is already available through various sources, and we can use it to get a clear picture
of the publications practices of researchers. This should help researchers to upload their papers and universities
to enforce open access policies. What feature would *you* need?

### **References**
> This is not compulsory but may help. Use any clear unambiguous reference style you like.

[1] : Counting the Costs of Open Access. The estimated cost to UK research organisations of achieving compliance with open access mandates in 2013/14. Research Consulting, November 2014.

[2] : Weiler, H., Meyer-Wegener, K., & Mele, S. (2011, October). Authormagic: an approach to author disambiguation in large-scale digital libraries. In Proceedings of the 20th ACM international conference on Information and knowledge management (pp. 2293-2296). ACM.
