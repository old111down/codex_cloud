"""Audit-only compatibility aliases. Does not edit upstream or installed packages."""
import collections.abc
import distutils.version  # torch1.9 SummaryWriter expects distutils.version attribute
import torch._six

# timm0.3.2 imports this name, removed from torch._six by declared torch1.9.
torch._six.container_abcs = collections.abc
