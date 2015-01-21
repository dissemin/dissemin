> *For reviewers: This template is using markdown, plain text formatting syntax. For more information, please contact us at or15-program-chairs@googlegroups.com*

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

developers, repository managers, open access officers in universities or funders

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
report them manualvly. Neither researchers nor universities have a simple way to get the list of
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

We use the SHERPA/RoMEO API to fetch publisher policies. They provide their own
policy classification, but for our purpose a simpler classification is sufficient.

We divide the policies into four categories:
* Open access: when the paper is published in an open access journal. Note that this
  does not include hybrid open access schemes: a paper published in a traditional
  journal and for which a paid open access option has been purchased will not fall
  into this category.
  The reason for this choice is mainly technical: there is no simple way to detect
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

These two criteria can be visually combined to help researchers to grasp instantly
the status of their publications, as in the following example:

![Screenshot of the publications list](https://raw.githubusercontent.com/wetneb/dissemin/master/doc/img/publist.png)

The two first papers were not found in any repository, but their publisher's policy indicates that they could be made available. They would then be marked as the third paper. The fourth paper is published in an open access journal and
is hence considered available. The last paper is also available and the publisher policy is marked as unknown.

#### 3. Technical details

##### 3.1. Metadata sources

We use two different tools to discover preprints:
* Bielefeld Academic Search Engine (through its API): this service covers a large
  collection of preprints, but the metadata it serves is not always very reliable,
  so we cannot afford to import systematically all the search results matching a given
  author in our database.
  However, if we have discovered a publication from another source and BASE can find
  a preprint for it, we mark this publication as available.
* Our own OAI-PMH harvester, covering 8 millions of papers from the major open repositories
  such as arXiv, HAL and PubMed Central.
  Papers discovered using OAI-PMH are added to the publications list and marked as
  available if the full text is also available from the OAI-PMH provider.

Policies are fetched from SHERPA/RoMEO.
this service does not provide a criterion to distinguish the "Open access"
class from the "Pre/post-prints allowed" class: we use the Directory of 
Open Access Journals for that purpose.

##### 3.2. Author disambiguation



### **Conclusion**
> Summarize the take-home message from the presentation. What are the main points? It would be great if this were a part of the conversation around the conference theme.

### **References**
> This is not compulsory but may help. Use any clear unambiguous reference style you like.

[1] : Research Consulting
