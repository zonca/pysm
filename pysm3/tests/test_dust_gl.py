import healpy as hp
from astropy.tests.helper import assert_quantity_allclose

import pysm3
from pysm3 import utils
from pysm3 import units as u

import pytest


@pytest.mark.parametrize("freq", [353 * u.GHz, 545 * u.GHz, 857 * u.GHz])
def test_d11gl_lownside(freq):
    nside = 512

    beamwidth = 14 * u.arcmin  # 2 pixels per beam

    d11_configuration = pysm3.sky.PRESET_MODELS["d11"].copy()
    d11_configuration["fwhm"] = beamwidth
    del d11_configuration["class"]
    del d11_configuration["galplane_fix"]
    output_healpix = pysm3.models.ModifiedBlackBodyRealization(
        nside=nside, seeds=[8192, 777, 888], **d11_configuration
    ).get_emission(freq)
    output_gl = pysm3.models.ModifiedBlackBodyRealizationGL(
        nside=nside, seeds=[8192, 777, 888], **d11_configuration
    ).get_emission(freq)
    lmax = 3 * nside - 1
    alm_dx11gl = utils.gl_map2alm(output_gl.value, lmax)
    output_gl_to_healpix = hp.alm2map(alm_dx11gl, nside=nside) * output_gl.unit

    rtol = 1e-4
    atol = {353: 20 * u.uK_RJ, 545: 60 * u.uK_RJ, 857: 150 * u.uK_RJ}
    assert_quantity_allclose(
        output_healpix[0], output_gl_to_healpix[0], rtol=rtol, atol=atol[freq.value]
    )
    assert_quantity_allclose(
        output_healpix[1:],
        output_gl_to_healpix[1:],
        rtol=rtol,
        atol=atol[freq.value] / 10,
    )


# @pytest.mark.skipif(
#     psutil.virtual_memory().total * u.byte < 20 * u.GB,
#     reason="Running d11 at high lmax requires 20 GB of RAM",
# )
# def test_d10_vs_d11():
#     nside = 2048
#
#     freq = 857 * u.GHz
#
#     output_d10 = pysm3.Sky(preset_strings=["d10"], nside=nside).get_emission(freq)
#     d11_configuration = pysm3.sky.PRESET_MODELS["d11"].copy()
#     del d11_configuration["class"]
#     d11 = pysm3.models.ModifiedBlackBodyRealization(
#         nside=nside, seeds=[8192, 777, 888], synalm_lmax=16384, **d11_configuration
#     )
#     output_d11 = d11.get_emission(freq)
#
#     rtol = 1e-5
#
#     assert_quantity_allclose(output_d10, output_d11, rtol=rtol, atol=0.05 * u.uK_RJ)
