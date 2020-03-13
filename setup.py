from setuptools import setup, find_packages

pkgs = find_packages()
pkgs.remove("zezere_ignition")
pkgs.remove("tests")

setup(
    name="zezere",
    version="0.1",
    author="Patrick Uiterwijk",
    author_email="patrick@puiterwijk.org",
    description="A provisioning server for Fedora IoT.",
    long_description="README.md",
    license="MPL",
    keywords="provisioning IoT linux",
    url="https://github.com/fedora-iot/zezere",
    packages=pkgs,
    include_package_data=True,
    platforms="any",
    install_requires=list(val.strip() for val in open("requirements.txt")),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    entry_points={"console_scripts": ["zezere-manage = zezere:run_django_management"]},
)
