from setuptools import setup, find_packages

setup(
    name="sensor_master",
    version="0.1.0",
    description="Master‐side Python package for RS-485 sensor hubs",
    packages=find_packages(),               # finds sensor_master/ under master/
    install_requires=[
        "pyserial>=3.5",
        "flask>=2.0",
        "click>=8.0",
        "PyQt5>=5.15",
        "tqdm>=4.0",
        "jsonschema>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0",
            "pytest-cov>=6.0",
            "jsonschema>=4.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "sensor-cli=sensor_master.cli.click:cli"
        ],
    },
)
