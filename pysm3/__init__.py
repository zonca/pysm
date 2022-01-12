# flake8: noqa
from ._astropy_init import *   # noqa

try:
    from importlib.metadata import version, PackageNotFoundError  # type: ignore
except ImportError:  # pragma: no cover
    from importlib_metadata import version, PackageNotFoundError  # type: ignore

try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"

import sys
from .models import *
from .sky import Sky
from . import units
from .distribution import MapDistribution
from .mpi import mpi_smoothing
from .utils import normalize_weights, bandpass_unit_conversion, check_freq_input
