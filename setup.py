from setuptools import setup, find_packages


with open("requirements.txt") as req, open("README.md") as readme:
    requirements = req.read().split()
    long_description = readme.read()


setup(
    name="blomp_api",
    version="1.0.1",
    author="Izak76",
    url="https://pypi.org/project/blomp-api",
    description="A unofficial Python API client to the Blomp cloud.",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules"],
    license="MIT",
    keywords=[
        "Python",
        "Web API",
        "Blomp",
        "REST"],
    install_requires=requirements,
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.8"
)