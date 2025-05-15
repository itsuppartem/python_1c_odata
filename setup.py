from setuptools import setup, find_packages

setup(
    name="python-1c-odata",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
    ],
    author="Artem Guliaev",
    author_email="itsuppartem@yandex.ri",
    description="Библиотека для работы с 1С через OData",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/itsuppartem/python-1c-odata",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 