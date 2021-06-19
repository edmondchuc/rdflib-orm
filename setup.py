import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rdflib-orm",
    version="0.1.0",
    author="Edmond Chuc",
    author_email="edmond.chuc@gmail.com",
    description="An ORM-like API for Python's RDFLib.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/edmondchuc/rdflib-orm",
    packages=setuptools.find_packages(),
    classifiers=[
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.6',
    install_requires=[
        'rdflib==5.0.0',
        'rdflib-jsonld==0.5.0',
        'requests==2.25.1',
    ],
)
