# LiM audit environment

Recreate the declared README-compatible environment with:

```sh
conda env create -f environment/lim/environment.yml
```

For the exact observed Conda package set, use `conda-explicit.txt` and then install the pip overlay in `pip-requirements-installed.txt`. Raw `pip-freeze.txt` is retained unchanged. Its packaging file URL refers to the Conda builder's source path, so that line is deliberately omitted only from the portable overlay; the exact Conda package is already pinned by the explicit manifest. The resolved export retains its original absolute prefix as evidence. Package availability at a later date is Unknown until recreation is tested.

Python3.11 was selected to satisfy the upstream README NumPy1.26.4 dependency. The paper claims Python3.13.0/XGBoost2.1.2; this environment uses Python3.11.18/XGBoost2.1.1 and is not an equivalent paper environment. TShark is absent; no PCAP parser success is claimed. See the reproduction report and runtime_versions.json.
