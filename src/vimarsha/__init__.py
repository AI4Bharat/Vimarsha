"""Tools for variation-aware ASR evaluation."""

from .lattice import build_lattice
from .metric import OIWERResult, compute_oiwer

__all__ = ["OIWERResult", "build_lattice", "compute_oiwer"]
__version__ = "0.1.0"
