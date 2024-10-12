<p align="center">
  <img src="/securedrop/static/i/logo.png" alt="SecureDrop" width="350" height="314">
</p>

> [There are many ways to contribute to SecureDrop, and we welcome your help!](CONTRIBUTING.md) By contributing to this project, you agree to abide by our [Code of Conduct](https://github.com/freedomofpress/.github/blob/main/CODE_OF_CONDUCT.md).

[![CircleCI branch](https://img.shields.io/circleci/project/github/freedomofpress/securedrop/develop.svg)](https://circleci.com/gh/freedomofpress/workflows/securedrop/tree/develop)
[![codecov](https://codecov.io/gh/freedomofpress/securedrop/branch/develop/graph/badge.svg)](https://codecov.io/gh/freedomofpress/securedrop)
[![Translation status](https://weblate.securedrop.org/widgets/securedrop/-/svg-badge.svg)](https://weblate.securedrop.org)
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/freedomofpress/securedrop)


SecureDrop is an open-source whistleblower submission system that media organizations can use to securely accept documents from, and communicate with anonymous sources. It was originally created by the late Aaron Swartz and is currently managed by the [Freedom of the Press Foundation](https://freedom.press).

## Documentation

SecureDrop's end user documentation is hosted at https://docs.securedrop.org. It is maintained in a standalone repository: https://github.com/freedomofpress/securedrop-docs.

By default, the documentation describes the most recent SecureDrop release. This is known as the **stable** version and is recommended for end users (Sources, Journalists, or Administrators). The **latest** documentation is automatically built from the most recent commit to the SecureDrop documentation repository. It is most useful for developers and contributors to the project. You can switch between versions of the documentation by using the toolbar in the bottom left corner of the Read the Docs screen.

Developer documentation can be found at https://developers.securedrop.org/, maintained in
https://github.com/freedomofpress/securedrop-dev-docs/.

## Found an issue?

If you're here because you want to report an issue in SecureDrop, please observe the following protocol to do so responsibly:

* If you want to report a **_security issue_**, please use our [bug bounty hosted by Bugcrowd](https://bugcrowd.com/freedomofpress).
* If filing the issue does not impact security, just create a [GitHub Issue](https://github.com/freedomofpress/securedrop/issues/new).

## How to Install SecureDrop

See the [Installation Guide](https://docs.securedrop.org/en/stable/#installtoc).

## How to Use SecureDrop

* [As a source](https://docs.securedrop.org/en/stable/source.html)
* [As a journalist](https://docs.securedrop.org/en/stable/journalist.html)

## How to Contribute to SecureDrop

See our [contribution page](CONTRIBUTING.md).

## Developer Quickstart

Ensure you have Docker installed and:

```
make dev
```

This will start the source interface on `127.0.0.1:8080` and the journalist interface on `127.0.0.1:8081`. The credentials to login are printed in the Terminal. To login to the journalist interface, you must also [generate a two-factor code](https://developers.securedrop.org/en/latest/setup_development.html#using-the-docker-environment).

## License

SecureDrop is open source and released under the [GNU Affero General Public License v3](/LICENSE).

## Wordlists

The wordlist we use to generate source passphrases come from various sources:

* [en.txt](/securedrop/wordlists/en.txt) is based off a new [Diceware wordlist](https://www.eff.org/deeplinks/2016/07/new-wordlists-random-passphrases) from the EFF.
* [fr.txt](/securedrop/wordlists/fr.txt) is based off Matthieu Weber's [translated diceware list](http://weber.fi.eu.org/index.shtml.en) and the French word list found in [trezor/python-mnemonic](https://github.com/trezor/python-mnemonic/blob/161bec3351dce9c439cd00dc0beaaf09e7906ff8/src/mnemonic/wordlist/french.txt) (MIT licensed).


## Acknowledgments

A huge thank you to all SecureDrop contributors! You can find a list of 
code and documentation contributors in the ["Contributors"](https://github.com/freedomofpress/securedrop/graphs/contributors)
tab on GitHub, and or a comprehensive view of code, documentation and translation contributors , check out the combined list [here](https://github.com/freedomofpress/securedrop-i18n/graphs/contributors). Thanks to our friends at PyUp for sponsoring a subscription to their [Python security database](https://pyup.io).
