from setuptools import setup, find_packages


with open("requirements.txt") as req, open("README.md") as readme:
    requirements = req.read().split()
    long_description = readme.read()


setup(
    name="blomp_api",
    version="1.0",
    description="Unofficial API to manage the Blomp Cloud.",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3"
        "Programming Language :: Python :: 3.7+",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules"],
    license="MIT",
    keywords=[
        "Python",
        "Web API",
        "Blomp",
        "REST"],
    requires=requirements,
    long_description=long_description,
    long_description_content_type="text/markdown"
)