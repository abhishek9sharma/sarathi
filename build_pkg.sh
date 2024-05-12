rm -rf dist
python -m pip install wheel twine
python setup.py bdist_wheel sdist