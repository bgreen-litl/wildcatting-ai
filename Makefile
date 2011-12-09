.PHONY: all clean_coverage develop virtualenv test

all:
	@echo 'develop  create a development environment'
	@echo 'check    run a full suite of tests'

develop:
	virtualenv virtualenv
	sh virtualenv-run.sh python setup.py develop

check: pep8 pyflakes test

pep8:
	@echo "Checking pep8 compliance..."
	@pep8 wcai wcdata

pyflakes:
	@echo "Running pyflakes..."
	@pyflakes wcai wcdata

test: clean_coverage
	python setup.py nosetests

clean_coverage:
	@rm -f .coverage
