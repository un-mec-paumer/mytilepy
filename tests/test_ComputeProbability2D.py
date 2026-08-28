"""Regression tests for ComputeProbability2D when no pixel survives the masks.

See PR #134: on numpy >= 2 an empty ``sortcat`` used to raise
``ValueError: The truth value of an empty array is ambiguous`` at
``if P_GW >= minProbcut``. The function must instead return a clean
sentinel and never raise.
"""

import astropy.coordinates as co
import astropy.units as u
import healpy as hp
import pytest

from tilepy.include.CampaignDefinition import (
    ObservationParameters,
    set_gaussian_source,
)
from tilepy.include.MapManagement.MapReader import create_map_reader
from tilepy.include.MapManagement.SkyMap import SkyMap
from tilepy.include.PointingTools import (
    ComputeProbability2D,
    GetRegionPixReduced,
    getdate,
)

CONFIG = """[observatory]
name = CTAO-N
lat = 28.75
lon = -17.5
height = 2200
[visibility]
sunDown = -18
moonDown = -0.5
moonGrey = 65
moonPhase = 60
minMoonSourceSeparation = 30
maxMoonSourceSeparation = 145
[operations]
maxZenith = 70
FOV = 2.0
maxRuns = 5
maxNights = 1
duration = 15
minDuration = 10
useGreytime = False
[tiling]
minimumProbCutforCatalogue = 0.01
minProbcut = 0.002
distCut = 500
doPlot = False
secondRound = False
zenithWeighting = 0.75
percentageMOC = 0.90
reducedNside = 128
HRnside = 512
mangrove = False
algorithm = 2D
strategy = integrated
doRank = False
countPrevious = False
countSubtractedPointingsOutside = False
[general]
downloadMaxRetry = 3
downloadWaitPeriodRetry = 20
"""


@pytest.fixture
def setup(tmp_path):
    """A synthetic Gaussian map (no network) plus the args ComputeProbability2D needs."""
    cfg = tmp_path / "config.ini"
    cfg.write_text(CONFIG)

    obspar = ObservationParameters()
    set_gaussian_source(obspar, ra=240.0, dec=20.0, sigma=5.0)
    obspar.from_configfile(cfg)

    skymap = SkyMap(obspar, create_map_reader(obspar))
    prob = skymap.getMap("prob", obspar.reducedNside)
    highres = skymap.getMap("prob", obspar.HRnside)

    rapix, decpix, _ = GetRegionPixReduced(
        prob, obspar.percentageMOC, obspar.reducedNside, skymap.scheme
    )
    radecs = co.SkyCoord(rapix, decpix, frame="icrs", unit=(u.deg, u.deg))

    return obspar, prob, highres, radecs, skymap.is_nested


def test_returns_scalar_when_pixels_available(setup):
    obspar, prob, highres, radecs, is_nested = setup

    P_GW, targetCoord, _ipixlist, _ipixlistHR = ComputeProbability2D(
        obspar,
        prob,
        is_nested,
        highres,
        radecs,
        getdate("2024-06-16 02:12:17"),
        [],
        [],
        0,
        ".",  # dirName, unused because doPlot=False
    )

    assert isinstance(P_GW, float)
    assert targetCoord is not None
    assert targetCoord.isscalar  # scalar SkyCoord, not shape (1,)


def test_no_crash_when_all_pixels_masked(setup):
    obspar, prob, highres, radecs, is_nested = setup

    all_pixels = list(range(hp.nside2npix(obspar.reducedNside)))

    P_GW, targetCoord, ipixlist, ipixlistHR = ComputeProbability2D(
        obspar,
        prob,
        is_nested,
        highres,
        radecs,
        getdate("2024-06-16 02:12:17"),
        [],
        [],
        0,
        ".",  # dirName, unused because doPlot=False
        all_pixels,
    )

    assert P_GW == 0.0
    assert targetCoord is None
    assert ipixlist == []
    assert ipixlistHR == []
