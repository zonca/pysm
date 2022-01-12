import numpy as np
from .. import units as u
from numba import njit
from .. import utils

from .template import Model


class PowerLaw(Model):
    """ This is a model for a simple power law synchrotron model.
    """

    def __init__(
        self,
        map_I,
        freq_ref_I,
        map_pl_index,
        nside,
        map_Q=None,
        map_U=None,
        freq_ref_P=None,
        unit_I=None,
        unit_Q=None,
        unit_U=None,
        map_dist=None,
    ):
        """ This function initialzes the power law model of synchrotron
        emission.

        The initialization of this model consists of reading in emission
        templates from file, reading in spectral parameter maps from
        file.

        Parameters
        ----------
        map_I, map_Q, map_U: `pathlib.Path` object
            Paths to the maps to be used as I, Q, U templates.
        unit_* : string or Unit
            Unit string or Unit object for all input FITS maps, if None, the input file
            should have a unit defined in the FITS header.
        freq_ref_I, freq_ref_P: Quantity or string
            Reference frequencies at which the intensity and polarization
            templates are defined.  They should be a astropy Quantity object
            or a string (e.g. "1500 MHz") compatible with GHz.
        map_pl_index: `pathlib.Path` object
            Path to the map to be used as the power law index.
        nside: int
            Resolution parameter at which this model is to be calculated.
        """
        super().__init__(nside, map_dist=map_dist)
        # do model setup
        self.I_ref = self.read_map(map_I, unit=unit_I)
        # This does unit conversion in place so we do not copy the data
        # we do not keep the original unit because otherwise we would need
        # to make a copy of the array when we run the model
        self.I_ref <<= u.uK_RJ
        self.freq_ref_I = u.Quantity(freq_ref_I).to(u.GHz)
        self.has_polarization = map_Q is not None
        if self.has_polarization:
            self.Q_ref = self.read_map(map_Q, unit=unit_Q)
            self.Q_ref <<= u.uK_RJ
            self.U_ref = self.read_map(map_U, unit=unit_U)
            self.U_ref <<= u.uK_RJ
            self.freq_ref_P = u.Quantity(freq_ref_P).to(u.GHz)
        try:  # input is a number
            self.pl_index = u.Quantity(map_pl_index, unit="")
        except TypeError:  # input is a path
            self.pl_index = self.read_map(map_pl_index, unit="")
        return

    @u.quantity_input
    def get_emission(self, freqs: u.GHz, weights=None):
        freqs = utils.check_freq_input(freqs)
        weights = utils.normalize_weights(freqs, weights)
        if not self.has_polarization:
            outputs = (
                get_emission_numba_IQU(
                    freqs,
                    weights,
                    self.I_ref.value,
                    None,
                    None,
                    self.freq_ref_I.value,
                    None,
                    self.pl_index.value,
                )
                << u.uK_RJ
            )
        else:
            outputs = (
                get_emission_numba_IQU(
                    freqs,
                    weights,
                    self.I_ref.value,
                    self.Q_ref.value,
                    self.U_ref.value,
                    self.freq_ref_I.value,
                    self.freq_ref_P.value,
                    self.pl_index.value,
                )
                << u.uK_RJ
            )
        return outputs


@njit(parallel=True)
def get_emission_numba_IQU(
    freqs, weights, I_ref, Q_ref, U_ref, freq_ref_I, freq_ref_P, pl_index
):
    has_pol = Q_ref is not None
    output = np.zeros((3, len(I_ref)), dtype=I_ref.dtype)
    I, Q, U = 0, 1, 2
    for i, (freq, weight) in enumerate(zip(freqs, weights)):
        utils.trapz_step_inplace(
            freqs, weights, i, I_ref * (freq / freq_ref_I) ** pl_index, output[I]
        )
        if has_pol:
            pol_scaling = (freq / freq_ref_P) ** pl_index
            utils.trapz_step_inplace(freqs, weights, i, Q_ref * pol_scaling, output[Q])
            utils.trapz_step_inplace(freqs, weights, i, U_ref * pol_scaling, output[U])
    return output


class CurvedPowerLaw(PowerLaw):
    def __init__(
        self,
        map_I,
        freq_ref_I,
        map_pl_index,
        nside,
        spectral_curvature,
        freq_curve,
        map_Q=None,
        map_U=None,
        freq_ref_P=None,
        unit_I=None,
        unit_Q=None,
        unit_U=None,
        map_dist=None,
    ):
        super().__init__(
            map_I=map_I,
            freq_ref_I=freq_ref_I,
            map_pl_index=map_pl_index,
            nside=nside,
            map_Q=map_Q,
            map_U=map_U,
            freq_ref_P=freq_ref_P,
            unit_I=unit_I,
            unit_Q=unit_Q,
            unit_U=unit_U,
            map_dist=map_dist,
        )
        try:  # input is a number
            self.spectral_curvature = u.Quantity(spectral_curvature, unit="")
        except TypeError:  # input is a path
            self.spectral_curvature = self.read_map(spectral_curvature, unit="")
        self.freq_curve = u.Quantity(freq_curve).to(u.GHz)

    @u.quantity_input
    def get_emission(self, freqs: u.GHz, weights=None):
        freqs = utils.check_freq_input(freqs)
        weights = utils.normalize_weights(freqs, weights)
        if not self.has_polarization:
            outputs = (
                get_emission_numba_IQU_curved(
                    freqs,
                    weights,
                    self.I_ref.value,
                    None,
                    None,
                    self.freq_ref_I.value,
                    None,
                    self.pl_index.value,
                    self.freq_curve.value,
                    self.spectral_curvature.value,
                )
                << u.uK_RJ
            )
        else:
            outputs = (
                get_emission_numba_IQU_curved(
                    freqs,
                    weights,
                    self.I_ref.value,
                    self.Q_ref.value,
                    self.U_ref.value,
                    self.freq_ref_I.value,
                    self.freq_ref_P.value,
                    self.pl_index.value,
                    self.freq_curve.value,
                    self.spectral_curvature.value,
                )
                << u.uK_RJ
            )
        return outputs


@njit(parallel=True)
def get_emission_numba_IQU_curved(
    freqs,
    weights,
    I_ref,
    Q_ref,
    U_ref,
    freq_ref_I,
    freq_ref_P,
    pl_index,
    freq_curve,
    curvature,
):
    has_pol = Q_ref is not None
    output = np.zeros((3, len(I_ref)), dtype=I_ref.dtype)
    I, Q, U = 0, 1, 2
    for i, (freq, weight) in enumerate(zip(freqs, weights)):
        curvature_term = np.log((freq / freq_curve) ** curvature)
        utils.trapz_step_inplace(
            freqs,
            weights,
            i,
            I_ref * (freq / freq_ref_I) ** (pl_index + curvature_term),
            output[I],
        )
        if has_pol:
            pol_scaling = (freq / freq_ref_P) ** (pl_index + curvature_term)
            utils.trapz_step_inplace(freqs, weights, i, Q_ref * pol_scaling, output[Q])
            utils.trapz_step_inplace(freqs, weights, i, U_ref * pol_scaling, output[U])
    return output
