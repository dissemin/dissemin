# -*- encoding: utf-8 -*-


from django import template

from papers.bibtex import format_paper_citation_dict

register = template.Library()


@register.filter(is_safe=True)
def bibtex(results_or_paper):
    if isinstance(results_or_paper, list):
        return format_paper_citation_dict(
            [
                r.object.citation_dict()
                for r in sorted(
                    results_or_paper,
                    key=lambda x: (x.object.pubdate, x.object.title)
                )
            ],
            indent='  '
        )
    else:
        return format_paper_citation_dict(results_or_paper.citation_dict())
