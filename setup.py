from setuptools import setup, find_packages

setup(
    name="sippy-async",
    version="2021.4.1.post2",
    py_modules=["sippy_async"],
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=[
        "anyio==3.0.1"
    ],
    entry_points={
    }
)
