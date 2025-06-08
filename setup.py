from setuptools import setup,find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="MLOPS-PROJECT-TITANIC",
    version="0.1",
    author="Md Kamruzzaman",
    packages=find_packages(),
    install_requires = requirements,
)