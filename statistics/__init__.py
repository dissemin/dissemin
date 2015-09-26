"""
This module provides models and templates to display accessibility statistics for
a set of papers.

Computing these statistics on the fly from the database is expensive, hence they
are cached in a dedicated model, :class:`.AccessStatistics`. This cache is also helpful
to cache the number of papers related to a given object.

A d3.js visualization of these statistics is provided in the template
``statistics/pie.html``.
"""
