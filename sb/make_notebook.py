"""Write the Kaggle submission notebook from policies/zonal.py.

The notebook embeds the policy file verbatim and wraps it in the gateway's
Policy class, following the organisers' TransferPolicy notebook.

    python -m sb.make_notebook --params '{"lead_h": 1.0}' --out submission.ipynb
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

HEADER = '''import sys
sys.path.append('/kaggle/input/competitions/neurips-2026-smart-buildings/kaggle_evaluation')
import numpy as np
from kaggle_evaluation import smart_buildings_inference_server
COMPETITION_DATA_FOLDER = '/kaggle/input/competitions/neurips-2026-smart-buildings/'
'''

WRAPPER = '''
ZonalPolicy = TransferPolicy  # the class defined above
PARAMS = {params}


class SubmissionPolicy(smart_buildings_inference_server.Policy):
    """Gateway wrapper around the zonal controller."""

    def __init__(self, building_meta_data, action_spec):
        super().__init__(building_meta_data, action_spec)
        self.inner = ZonalPolicy(building_meta_data, action_spec, **PARAMS)
        c, d = action_spec["continuous_action"], action_spec["discrete_action"]
        self.c_lo, self.c_hi = c.low, c.high
        self.d_lo, self.d_hi = d.low, d.high

    def get_action(self, obs):
        a = self.inner.get_action(obs)
        return {
            "continuous_action": np.clip(a["continuous_action"], self.c_lo, self.c_hi).astype(np.float32),
            "discrete_action": np.clip(a["discrete_action"], self.d_lo, self.d_hi).astype(np.int32),
        }


smart_buildings_inference_server.SmartBuildingsInferenceServer(SubmissionPolicy).run(
    competition_data_folder=COMPETITION_DATA_FOLDER,
)
'''


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="policies/zonal.py")
    ap.add_argument("--params", default="{}")
    ap.add_argument("--out", default="submission/submission.ipynb")
    ap.add_argument("--title", default="Zonal controller: one-step MPC with online zone identification")
    a = ap.parse_args(argv)
    src = Path(a.policy).read_text(encoding="utf-8")
    src = "\n".join(line for line in src.splitlines() if line.strip() != "from __future__ import annotations")
    params = json.loads(a.params)
    cells = [
        {"cell_type": "markdown", "metadata": {},
         "source": [f"# {a.title}\n",
                    "Source and paper: see the repository README. AI assistance (Claude, Anthropic) "
                    "was used to write the code; it is disclosed in the paper.\n"]},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
         "source": (HEADER + "\n" + src).splitlines(keepends=True)},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
         "source": WRAPPER.replace("{params}", repr(params)).splitlines(keepends=True)},
    ]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                                       "name": "python3"},
                                        "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 5}
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
