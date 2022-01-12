import pytest
import pysm3
import astropy.units as units
from astropy.tests.helper import assert_quantity_allclose


@pytest.mark.parametrize("freq", [100, 353, 900])
@pytest.mark.parametrize("model_tag", ["d7", "d5", "d8"])
def test_highfreq_dust_model(model_tag, freq):

    model = pysm3.Sky(preset_strings=[model_tag], nside=64)

    expected_output = pysm3.read_map(
        "pysm_2_test_data/check_{}_{}_uK_RJ_64.fits".format(model_tag, freq),
        64,
        unit="uK_RJ",
        field=(0, 1, 2),
    )

    rtol = 1e-5

    assert_quantity_allclose(
        expected_output, model.get_emission(freq * units.GHz), rtol=rtol
    )
