"""Print the LP schedule (analysis/day_lp_bound.py) against v10 for one zone and day, by hour."""
import runpy
import sys

import numpy as np

sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2], "1"] + sys.argv[3:]
