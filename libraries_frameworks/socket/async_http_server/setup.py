from setuptools import setup, find_packages

setup(
    name="async-http-server",          # PyPI name (must be unique)
    version="0.1.8",
    description="A simple async HTTP server package",
    author="Divya Das",
    author_email="Divya.Das@email.com",
    packages=find_packages(),
    python_requires=">=3.7",
)

