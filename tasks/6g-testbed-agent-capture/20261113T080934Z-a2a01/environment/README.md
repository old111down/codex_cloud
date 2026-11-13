# Environment declarations

Python 3.12.16 in an independent Conda environment. `conda-explicit.txt` declares base packages; `requirements-runtime.txt` pins the observed scoped runtime packages. `environment.yml` is a convenient declaration. These are declarations, not a bundled environment, and do not assert the historical full testbed lock was reproduced.

The original pip-freeze output contained a local Conda build reference for packaging. It is retained privately. The public requirements and YAML normalize that entry to `packaging==26.3`, matching the observed installed version in `versions.json`; no scientific measurement was altered. The upstream custom aiortc is imported from the pinned private source checkout through PYTHONPATH and is not falsely represented as a published wheel. Torch was not installed.

`scenario_snapshot.json` withholds the literal task and retains its hash. Synthetic loopback addresses and configured ports 9001/9009 in original audit scripts are public test configuration, not captured endpoint identities.
