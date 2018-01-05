#!/usr/bin/env bash

VERSION=`python src/version.py`
sudo pip install dist/plaitpy-${VERSION}.tar.gz --upgrade
