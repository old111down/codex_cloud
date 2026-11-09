# LINC environment deviations

The original README `pip install -r requirements.txt` was actually attempted and failed: pinned `swanlab==0.3.16` was not available at the configured index; the official PyPI exact-version JSON endpoint also returned404. The dependency resolution dry-run failure is retained separately. No complete original dependency installation is claimed.

The experiment logger is optional (`LINC_LAB_UTIL` unset by default), so the audit omitted that inactive package rather than substituting a different remote logging client. No experiment data was sent to SwANLab/W&B. All remaining original versions were installed, with PyTorch2.0.1's official CPU wheel (`2.0.1+cpu`) to avoid unused CUDA downloads. The initial declared NumPy2.0.1 plus this wheel was actually tested: `torch.from_numpy` failed with `RuntimeError: Numpy is not available` and `_ARRAY_API` compatibility warning. The original environment freeze is retained in `pip-freeze-original-numpy.txt`.

NumPy1.26.4 was then installed as a disclosed compatibility fix; the final freeze, exact Conda URLs and runtime versions describe the actual environment. The paper reports Python3.9/PyTorch1.12.0/TeslaM60; this Python3.10/PyTorch2.0.1+cpu environment is not the paper environment. Its synthetic tests support only R1.

`requirements-original.txt` preserves the upstream pins. `requirements-runtime-original-numpy.txt` omits only unavailable/inactive SwANLab and separately installed Torch, for testing the declared NumPy ABI. `requirements-cpu-compat.txt` and `environment.yml` declare the final compatible CPU environment. Conda explicit lists lock only Conda packages; pip freeze and installation reports record pip packages separately.
