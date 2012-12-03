from setuptools import setup, find_packages

setup(
    name = "Partridge",
    version = "0.1",
    packages = find_packages(),

    #install requirements
    install_requires = ['Flask>=0.9',
            'Flask-SQLAlchemy>=0.16'],

    #program entrypoints
    entry_points ={
     'console_scripts' : [
        'partridged = partridge:run',
        'pdfxconv = partridge.tools.pdfxconv:main'
     ]
    },
    #author details
    author = "James Ravenscroft",
    author_email = "ravenscroftj@gmail.com",
    description = "A toolkit for automated classification and indexing of large documents",
    url="http://wwww.papro.org.uk/"
)

