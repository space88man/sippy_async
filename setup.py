from setuptools import setup, find_packages

setup(
    name="sippy-async",
    version="2021.4.0",
    py_modules=["sippy_async"],
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=[
    ],
    entry_points={
    }
)
