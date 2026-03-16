"""Setup script for StoryMaker."""

from setuptools import setup, find_packages

setup(
    name="storymaker",
    version="0.2.0",
    description="Interactive AI-powered stories with pictograms for reading comprehension training",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="StoryMaker Team",
    url="https://github.com/yeager/StoryMaker",
    license="GPL-3.0",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "PyGObject>=3.42",
        "pycairo>=1.20",
    ],
    extras_require={
        "openai": ["openai>=1.0"],
        "anthropic": ["anthropic>=0.20"],
        "all": ["openai>=1.0", "anthropic>=0.20"],
    },
    entry_points={
        "gui_scripts": [
            "storymaker = storymaker.__main__:main",
        ],
    },
    data_files=[
        ("share/applications", ["data/org.github.storymaker.desktop"]),
        ("share/icons/hicolor/scalable/apps", ["data/icons/hicolor/scalable/apps/org.github.storymaker.svg"]),
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: Education",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: Swedish",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Education",
    ],
)
