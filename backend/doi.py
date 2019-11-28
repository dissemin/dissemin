# This module is the successor of the old crossref.py which mixed some things up.
# The module will provide essentially two ways to retrieve metadata from a DOI.
# 1. single DOI with content negotiation via dx.doi.org
# 2. mass import from CrossRef, i.e. get all DOI that they have.
# The strategy in the first case will be to check wether we have the DOI in our system and if the last update is not to long ago, we just skip.
# This has the reason, that a users might wait if they refresh their profile.


class CiteprocError(Exception):
    pass

class CiteprocTitleError(Exception):
    pass

class Citeproc():
    """
    This class is a citeproc parser.
    """

    @staticmethod
    def to_paper(data):
        """
        Call this function to convert citeproc metadata into a paper object
        Our strategy is as follows:
        We collect first all data necessary, if me miss something, then we raise CiteprocError.
        If we have collected everything, we pass that to the corresponding baremodels.
        :param data: citeproc metadata. Note that CrossRef does put its citeproc into a message block
        :returns: Paper object or None if no paper was created
        :raises: CiteprocError
        """
        if not isinstance(data, dict):
            raise CiteprocError('Invalid metadaformat, expecting dict')


    @classmethod
    def _get_paper_data(cls, data):
        """
        :param data: citeproc metadata
        :returns: Returns a dict, ready to passed to a BarePaper instance
        :raises: CiteprocError
        """
        bare_paper_data = {
            'title' : cls._title()
        }
        
        return bare_paper_data

    @classmethod
    def _get_title(cls, data):
        """
        :param: citeproc metadata
        :returns: title
        :raises: CiteprocError
        """
        # Check for a title
        title = data.get('title')
        if title is None:
            raise CiteprocTitleError('No title in metadata')
        return title
        
        
class CrossRef(Citeproc):
    """
    This class can parse CrossRef metadata, which is similar to citeproc and has functionality to fetch from CrossRef API
    """

    @classmethod
    def _get_title(cls, data):
        """
        The title in CrossRef citeproc is in a list
        :param: citeproc metadata
        :returns: title
        :raises: CiteprocError
        """
        title = super()._get_title(data)
        try:
            return title[0]
        except IndexError:
            raise CiteprocTitleError('No title in metadata')
