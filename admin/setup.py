#
# Copyright (C) 2013-2018 Freedom of the Press Foundation & al
# Copyright (C) 2018 Loic Dachary <loic@dachary.org>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import setuptools

setuptools.setup(
    name="securedrop-admin",
    version="0.1.0",
    author="Freedom of the Press Foundation",
    author_email="securedrop@freedom.press",
    description="SecureDrop Admin Toolkit",
    url="https://securedrop.org",
    packages=setuptools.find_packages(),
    scripts=['bin/securedrop-admin'],
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
    python_requires='>=3.11',
)
