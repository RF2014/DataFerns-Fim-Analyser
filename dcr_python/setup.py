from setuptools import setup, find_packages

setup(
    name="dcr-traffic-analysis",
    version="1.0.0",
    description="DCR 2000 - Traffic Data Analysis Application (Python Port)",
    author="Converted from VBA",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "PyQt5>=5.15.9",
        "pandas>=2.1.3",
        "openpyxl>=3.11.0",
        "numpy>=1.24.3",
        "python-dateutil>=2.8.2",
        "pytz>=2023.3",
    ],
    entry_points={
        "console_scripts": [
            "dcr-app=main:main",
        ],
    },
)
