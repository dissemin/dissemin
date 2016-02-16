"""
This module provides the deposit features of dissemin.
It is built around two central classes: :class:`~models.Repository`
and :class:`~protocol.RepositoryProtocol`.

A :class:`~models.Repository` represents some place where we can deposit
papers. A :class:`~models.Repository` stores
all the information we need to push papers to that place, such
as the endpoint of its API, the username and password to use,
as well as information about how to display it to users (logo,
name, description).
The :class:`~models.Repository` class is a Django model, which means that we can manage
repositories directly from dissemin's web admin interface.

Each :class:`~models.Repository` is tied to a :class:`~protocol.RepositoryProtocol`, which
describes how to send the paper to the repository. Each protocol
implementation should be done as a subclass of :class:`~protocol.RepositoryProtocol`.
"""
