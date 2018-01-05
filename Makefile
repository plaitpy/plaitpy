default: test

test: unit
fulltest: unit e2e

unit:
				python tests/test_fields.py

e2e:
				bash scripts/run_tests.sh

package:
				python setup.py sdist

install: package
				bash scripts/install_package.sh

upload:
				bash scripts/publish_package.sh
