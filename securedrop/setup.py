import setuptools

long_description = "The SecureDrop whistleblower platform."

setuptools.setup(
    name="securedrop-app-code",
    version="2.10.0~rc1",
    author="Freedom of the Press Foundation",
    author_email="securedrop@freedom.press",
    description="SecureDrop Server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="AGPLv3+",
    python_requires=">=3.8",
    url="https://github.com/freedomofpress/securedrop",
    classifiers=[
        "Development Status :: 5 - Stable",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
    ],
)
