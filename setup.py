from setuptools import setup

with open("README.md", "r") as me:
    long_description = me.read()

setup(
    name="onbogo",
    version="0.0.1",
    description="Get notified when your favorite groceries go on sale",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wijabu/OnBoGo",
    package_dir={"": "onbogo"},
    author="wijabu",
    author_email="williamjamesbuchanan@gmail.com",
    license="MIT",
)
