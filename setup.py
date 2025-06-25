from setuptools import setup, find_packages

setup(
    name="graphfusionai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "networkx",
        "matplotlib",
        "asyncio"
    ],
    entry_points={
        "console_scripts": [
            "graphfusionai=graphfusionai.cli:main",
        ],
    },
)
