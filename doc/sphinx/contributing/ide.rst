.. _page-ide:

Setting up Dissemin for Development in an IDE
==============================================

This page lists some possible ways to set up Dissemin locally for development, including setting up an IDE to edit Dissemin conveniently.
First, you need to install Dissemin locally: see :ref:`page-installation` for that.
In particular, you will need to have postgres, redis and elasticsearch instanced running during development, as these services are required to run the tests.

Eclipse and PyDev
-----------------

Although it is primarily designed to work on Java programs, Eclipse can be used to work on Python projects thanks to its PyDev extension.
This includes a Python editor, debugger and importantly, the ability to run tests selectively from the editor. Moreover PyDev comes with
a Django integration too.

To install Eclipse, simply `download it <https://www.eclipse.org/downloads/>`_ and unzip it in your favourite location.
Fire up Eclipse and click *Help*, *Eclipse Marketplace*. In the field to search for new software, type *PyDev* and install it.

You will then need point Eclipse to your copy of Dissemin, so that it can be opened as a project. To do so, click *File*, *Open Projects from File System*, and select the directory where you have cloned Dissemin. Click *Finish*: this will create your
project. The project might not be recognized as a Python project, so enable PyDev on it with a right click on the project (in the Project Explorer), click *PyDev*, *Set as PyDev Project*. Do the same to enable it as a Django project too.

Assuming you have installed Dissemin's Python dependencies in a Virtualenv, you will need to configure that too (otherwise Eclipse will try to run
Dissemin with the system's own Python installation). To do so, right click on the project, select *Properties* and go to the *PyDev - Interpreter/Grammar* pane. Then click the *Click here to configure an interpreter not listed*, choose
*Open interpreter preference pages*. Then *Browse for python/pypy exe*, and select the Python executable in your virtualenv (it normally lives at `my_virtualenv/bin/python`). Give it a name such as `Dissemin virtualenv`. When prompted to add entries to
PYTHONPATH, select them all and validate. Finally, click *Apply and close*. Once you are back to the project's own interpreter configuration page, do not forget to select the newly-created interpreter configuration.

Finally, you will need to configure PyDev so that it uses `pytest` to run the tests. This will have the benefit of handling Django's initialization for you. This setting is not stored at project level, you need to go in PyDev's general preferences to
change this. Click *Window*, *Preferences*, select the *PyUnit* pane in the *PyDev* group and choose the *Py.test runner*. Finally, click *Apply and Close*.

You can now easily run individual tests from the editor. Go to a test file, use *Ctrl-Shift* and the up and down arrows to navigate to the test method or test class that you want to run. Then press *Ctrl-F9* and validate with *Enter*. This will run your
tests and display their results in the dedicated pane below. You can also set up breakpoints and run the tests in the debugger.

PyCharm
-------

PyCharm's Django integration is not available in the Community edition.
However, because we use Pytest to run tests, it might be possible to use the Community edition anyway.
If you try, please let us know how it goes so that we can update this documentation.

Using a standard text editor
----------------------------

That works too, of course. In that case you might want to make sure you run `./pyflakes.sh` to check
for import errors and other syntactical issues before you commit or push. This can easily done by
adding a git hook::

    ln -s pyflakes.sh .git/hooks/pre-commit

