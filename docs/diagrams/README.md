# Diagrams

This directory contains both complete and work-in-progress diagrams
and visual aids for SecureDrop.

When adding a diagram to this directory, please take a moment to add
an entry here:

- `SecureDrop.png`: A high-level overview of the components of and
  data flows through the SecureDrop architecture. Used in the
  [SecureDrop website FAQ][]. Up to date at the time of this writing.
  A symbolic link to the English version of the diagram
  (`SecureDrop-en.png`).
- `SecureDrop-en.svg`: SVG used to generate the English version
- `SecureDrop.vsdx`: The Microsoft Visio source file used to generate
  `SecureDrop-visio.png`. For context, see [#274][].
- `SecureDrop-0.3-DFD.png`: A WIP DFD (data flow diagram) created for
  SecureDrop 0.3. WIP.
- `securedrop-database.png`: A diagram of the tables and columns in the securedrop app's SQLite database.
- `securedrop-database.tex`: TeX used to generate the `securedrop-database.png` figure.
- `SecureDrop_DataFlow.png`: Data flow diagram for SecureDrop.
- `SecureDrop_DataFlow.draw`: XML used to generate with [Draw.io][].
[SecureDrop website FAQ]: https://securedrop.org/faq#how_works
[#274]: https://github.com/freedomofpress/securedrop/issues/274
[Draw.io]: https://www.draw.io/
