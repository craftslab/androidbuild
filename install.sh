#!/bin/bash

pip install -U pywin32
pip install -U PyInstaller

pyinstaller --clean --name katicache --upx-dir /path/to/upx -F src/katicache.py
pyinstaller --clean --name ninjabuild --upx-dir /path/to/upx -F src/ninjabuild.py
pyinstaller --clean --name soongcache --upx-dir /path/to/upx -F src/soongcache.py
