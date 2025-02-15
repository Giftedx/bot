"""Package setup script."""
from setuptools import setup  # type: ignore

if __name__ == "__main__":
    setup(
        # All configuration is in setup.cfg
        setup_requires=["setuptools>=45.0", "wheel"]
    )
