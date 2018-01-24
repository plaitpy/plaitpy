#!/usr/bin/env bash

VERSION=`python src/version.py`
sudo pip2 install dist/plaitpy-${VERSION}.tar.gz --upgrade
sudo pip3 install dist/plaitpy-${VERSION}.tar.gz --upgrade
