from setuptools import setup, find_packages

setup(
    name="tabscript",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'reportlab<3.6.0',  # 古いバージョンを指定
        'Pillow<9.0.0',     # Python 3.7向けに古いバージョンを指定
        # TODO: Add dependencies as needed
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A parser and renderer for TabScript notation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tabscript",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        'console_scripts': [
            'tab2pdf=tabscript.cli:main',
            'tab2txt=tabscript.cli:main',
        ],
    },
) 