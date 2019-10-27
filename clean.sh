#!/bin/bash

chmod 644 .gitignore
chmod 644 LICENSE README.md

find . -name "*.py" -exec chmod 644 {} \;
find . -name "*.pyc" -exec rm -rf {} \;
find . -name "*.sh" -exec chmod 755 {} \;
find . -name "__pycache__" -exec rm -rf {} \;
