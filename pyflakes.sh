#!/bin/bash
pyflakes . | grep -vP "^./(dissemin|notification|src|\..*)/" > pyflakes.out
cat pyflakes.out
test \! -s pyflakes.out
