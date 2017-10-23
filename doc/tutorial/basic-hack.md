---
title: Basic Hack of Dissem.in tutorial
...

## Prerequisites

Not that good in programming and still, eager to hack dissem.in?

Here are a few steps with examples :)

All you need is some basic Python programming, but all the hight-level stuff done by Django and other powerful, yet complicated Python things will be left for later.

You should also already have installed Dissem.in (if you didn't already, [follow this tutorial](dev.dissem.in).

## First step: how data flows

Think of dissemin as data staying in a server and a user that clicks here and there.

The clicks of a user on the interface trigger a request to the internal API (which is not the REST API, for which documentation can be found [here](https://dev.dissem.in/api.html)). These requests look like https://dissem.in/my-profile. One has to map a URI pattern to some code to execute (called _views_). This is done in the url.py of each app ([url.py of the _papers_ app](https://github.com/dissemin/dissemin/blob/master/papers/urls.py#L27)).

For example, when a user clicks on "Search" on the homepage or enters the URL https://dissem.in/search/ the view _views.PaperSearchView.as_view()_ is executed.

Views are classes in the views.py file of each app. Let's stay in the same example and have a look at [views.py](https://github.com/dissemin/dissemin/blob/master/papers/views.py) of the papers app.

The view that is executed by the preceding click is [the PaperSearchView](https://github.com/dissemin/dissemin/blob/master/papers/views.py#L106) (which ends [line 192](https://github.com/dissemin/dissemin/blob/master/papers/views.py#L192). The methods (also named functions ;)) that are defined have standard names and their execution is handled by Django (the framework that runs behind the scenes). 

The _get_ method (function) takes arguments that are also managed by Django (and correspond to what the user entered as a search), then tests something about the user that is interacting with dissemin (`if not is_admin(request.user)`) and performs some actions (`request.GET.pop`…), and finally returns an _object_ (in the sense of a Python object) that will again be handled by Django.

## Design of the hack

The data stored in the server is in a SQL database but everything is managed through Python classes.

To add some information about something that already lives on the server (for example add a metadata entry about authors), the models.py of the corresponding app needs to be updated. For example, you can add `nickname = "Géo Trouvetout"` to the [Researcher class](https://github.com/dissemin/dissemin/blob/master/papers/models.py#L350) if you think that all researchers are somehow all _Géo Trouvetouts_.

## Make Django do the work of updating the parts of the code that are affected by your change (aka do the migration)

In the vagrant shell, run `./manage.py migrate`

## A hack is useless if it is not visible to the world…

So let's see if there is anything to do to have anyone know that all researchers are Géo Trouvetouts.

Pages that the user sees are made of HTML chuncks tied together through a template engine. And there is some logics in the way these HTML chuncks are produced, mainly adding a piece of html only if a condition is verified (for example only display the affiliation of a researcher if this data is available.

The chunck of html that displays the list of authors of an article is in [papers/templates/papers/authorList.html](https://github.com/dissemin/dissemin/blob/master/papers/templates/papers/authorList.html).

By adding, right after `data-last="{{ author.name.last }}"` the following line: `data-nickname="{{ author.nickname }}"`, then the nickname of each author will be added.

## Let's see the results!

Run dissemin with `./manage.py` and search for an author and check that there has been some change in the [source of the page](view-source:https://dissem.in/search/?authors=albert+einstein).

That may not be so interesting to have such a nickname visible on the actual page. And anyhow, I – the author of this tutorial — am still learning how dissemin works so for the moment I can't tell you ;).


## Some technical things you need to know

### Apps 

Apps correspond to the division of the code in folders, in the root directory. All contain url.py, views.py and models.py.


## Further hacks of dissemin

You can also hack the url.py files and add actions in the views.py file. Good luck!


## Remerciements

Thanks a lot Antonin for giving me a tour of the code of dissem.in. Here is some feedback :)

Licence: CC-BY
