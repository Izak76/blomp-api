from setuptools import setup, find_packages


with open("requirements.txt") as req, open("README.md", encoding='utf-8') as readme:
    requirements = req.read().split()
    long_description = readme.read()


setup(
    name="blomp_api",
    version="1.0.4",
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
    python_requires=">=3.8",
    project_urls={
        "Documentation": "https://github.com/Izak76/blomp-api/blob/main/README.md",
        "Source Code": "https://github.com/Izak76/blomp-api",
        "Bug Reports": "https://github.com/Izak76/blomp-api/issues",
        "Changes": "https://github.com/Izak76/blomp-api/blob/main/CHANGELOG"
    }
)
