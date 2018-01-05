VERSION=`python src/version.py`
twine upload dist/plaitpy-${VERSION}.tar.gz
