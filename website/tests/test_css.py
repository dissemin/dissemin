import os
import pytest

from sass_processor.processor import SassProcessor

from django.conf import settings

class TestCSS():
    """
    Class that tests our (two) css files
    """
    @pytest.mark.parametrize('scss_file', ['custom.scss', 'dissemin.scss',])
    def test_scss(self, scss_file, check_css):
        """
        Tests the css files.
        """
        s = SassProcessor()
        check_css(os.path.join(settings.SASS_PROCESSOR_ROOT, s(os.path.join('scss', scss_file))))

