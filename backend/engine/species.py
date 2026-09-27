"""Likely target species for a cell, from its depth and water temperature.

This is a labelling layer, not a prediction. It takes numbers the grid
already carries -- depth, SST, whether the cell sits on a thermal front --
and prints the species a Tutukaka skipper would rig for on that ground. It
deliberately never touches ``hotspot_score``: a mark does not get better
because we can name a fish on it.

The bands below are the working rules of thumb for the Tutukaka Coast and
Poor Knights shelf. They are **not** calibrated against catch data, and
they are seasonal in reality while these are not, so treat a badge as "rig
for this", never as "this is what is there".
"""

from __future__ import annotations

# (label, min depth m, max depth m, min SST C, max SST C, priority)
# Priority is a deliberate editorial ordering, not a computed one: on a 170 m
# pinnacle a skipper says "kingfish", even though kahawai are also there.
BANDS: tuple[tuple[str, float, float, float, float, int], ...] = (
    # Inshore reef and sand: the bread-and-butter snapper ground.
    ("Snapper", 0.0, 60.0, 12.0, 24.0, 2),
    # Mid-shelf foul ground where the workups and kahawai school up.
    ("Kahawai", 10.0, 90.0, 13.0, 24.0, 4),
    # Deeper reef edges: the hapuku/bass country off the Knights.
    ("Hapuku", 180.0, 600.0, 10.0, 19.0, 1),
    # The classic kingfish shelf: pinnacles and drop-offs.
    ("Kingfish", 150.0, 200.0, 15.0, 24.0, 0),
    # Gamefish want warm blue water; the front is what concentrates them.
    ("Marlin/Tuna", 80.0, 2000.0, 18.5, 30.0, 3),
)

# A cell on a temperature break holds bait, so gamefish get named there at a
# slightly lower temperature than they would over flat, featureless water.
FRONT_SST_ALLOWANCE_C = 0.4

MAX_TAGS = 2


def tags_for(
    depth_m: float | None,
    sst_c: float | None,
    is_thermal_front: bool = False,
) -> list[str]:
    """Up to two species labels for a cell, most specific first.

    Returns ``[]`` when depth or temperature is missing rather than guessing
    -- an unlabelled mark is honest, a wrong label sends someone out with the
    wrong gear.
    """
    if depth_m is None or sst_c is None:
        return []

    depth = abs(float(depth_m))
    sst = float(sst_c)

    hits: list[tuple[int, str]] = []
    for label, d_min, d_max, t_min, t_max, priority in BANDS:
        allowance = FRONT_SST_ALLOWANCE_C if is_thermal_front else 0.0
        if not (d_min <= depth <= d_max):
            continue
        if not (t_min - allowance <= sst <= t_max):
            continue
        hits.append((priority, label))

    hits.sort(key=lambda h: h[0])
    return [label for _, label in hits[:MAX_TAGS]]
