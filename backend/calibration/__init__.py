"""Catch logging and weight calibration.

The score's weights came from the spec, not from data. Nothing here changes
that on its own -- it is the plumbing that lets it change, once there are
enough logged trips to fit against.
"""

from backend.calibration.catch_log import CatchEntry, append_entry, load_entries

__all__ = ["CatchEntry", "append_entry", "load_entries"]
