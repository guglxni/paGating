from setuptools import setup, find_packages

setup(
    name="paGating",
    version="0.1.0",
    author="Aaryan Guglani",
    author_email="aaryanguglani@example.com",
    description="Parameterized Activation Gating Framework",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "torch>=1.9.0",
        "matplotlib>=3.4.0",
        "numpy>=1.19.0",
    ],
)