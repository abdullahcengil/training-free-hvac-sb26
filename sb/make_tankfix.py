"""A patched copy of the shipped simulator with an energy-balanced hot-water tank (docs/TANKFIX.md).

Forum threads 749531 and 751998 report that the shipped boiler bills gas from the supply-water setpoint while the tank
temperature follows the setpoint at a fixed rate, so billed gas and delivered reheat can differ. A participant proposed
a fix (starter-kit pull request 2): the tank temperature follows C dT/dt = Q_burner - Q_coils - Q_loss and gas is billed
as Q_burner. This script writes the same equations into a separate copy of the installed package (its own code, written
from the pull request's description; the pull request's files are not downloaded or run), so that our controller and the
official baselines can be scored under the proposed fix without touching the installed simulator.

    python -m sb.make_tankfix --out D:/SmartBuildings_data/kit_tankfix
    PYTHONPATH=D:/SmartBuildings_data/kit_tankfix python -m sb.jobs ...     # runs on the patched copy
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

SIM = "smart_control/simulator"

# (file, anchor that must occur exactly once, text inserted after it, or a replacement when the third item is None)
EDITS = [
    ("boiler.py", "    self._insulation_thickness = insulation_thickness\n",
     "    # Tank temperature from an energy balance (sb/make_tankfix.py).\n"
     "    self.energy_balance = self._has_tank and heating_rate > 0\n"),
    ("boiler.py", "    self._run_command = smart_device.RunStatus.OFF\n",
     "    self._burner_heat_rate = 0.0\n"),
    ("boiler.py", "  def supply_water_temperature_sensor(self) -> float:\n    self._set_current_temperature()\n",
     None,
     "  def supply_water_temperature_sensor(self) -> float:\n    if not self.energy_balance:\n"
     "      self._set_current_temperature()\n"),
    ("boiler.py", "  @property\n  def run_command(self) -> smart_device.RunStatus:\n", None,
     "  def apply_heat_draw(self, coil_heat_w: float, outside_temp: float, duration_s: float) -> None:\n"
     "    \"\"\"One step of C dT/dt = Q_burner - Q_coils - Q_loss (sb/make_tankfix.py).\n\n"
     "    The burner fires towards the setpoint, at most the draw plus the standing loss plus heating_rate, so\n"
     "    without draw the tank heats as fast as the setpoint follower did.\n    \"\"\"\n"
     "    if duration_s <= 0.0:\n      return\n"
     "    c = constants.WATER_HEAT_CAPACITY * constants.WATER_DENSITY * self._water_capacity\n"
     "    loss = self.compute_thermal_dissipation_rate(self._current_temperature, outside_temp)\n"
     "    needed = c * (self._supply_water_temperature_setpoint - self._current_temperature) / duration_s\n"
     "    needed += coil_heat_w + loss\n"
     "    max_rate = max(coil_heat_w, 0.0) + loss + c * self._heating_rate / 60.0\n"
     "    self._burner_heat_rate = min(max(needed, 0.0), max_rate)\n"
     "    self._current_temperature += (self._burner_heat_rate - coil_heat_w - loss) * duration_s / c\n\n"
     "  @property\n  def run_command(self) -> smart_device.RunStatus:\n"),
    ("boiler.py", "    # If return_water_temp is greater than the setpoint,\n    # the boiler should not be cooling.\n", None,
     "    if self.energy_balance:\n      return self._burner_heat_rate\n\n"
     "    # If return_water_temp is greater than the setpoint,\n    # the boiler should not be cooling.\n"),
    ("hot_water_system.py", "from smart_buildings.smart_control.simulator import pump as pump_py\n",
     "from smart_buildings.smart_control.utils import constants\n"),
    ("hot_water_system.py", "  def _calculate_flow_rate(\n", None,
     "  def apply_heat_draw(self, outside_temp: float, duration_s: float) -> None:\n"
     "    \"\"\"Takes this step's coil heat, flow x (T_supply - T_return), out of an energy-balanced tank.\"\"\"\n"
     "    if not getattr(self._heat_source, 'energy_balance', False):\n      return\n"
     "    coil_heat_w = (constants.WATER_HEAT_CAPACITY * constants.WATER_DENSITY * self.total_flow_rate\n"
     "                   * (self.supply_water_temperature_sensor - self.return_water_temperature_sensor))\n"
     "    self._heat_source.apply_heat_draw(coil_heat_w, outside_temp, duration_s)\n\n"
     "  def _calculate_flow_rate(\n"),
    ("simulator.py",
     "        self._calculate_return_water_temperature(zone_supply_temp_map)\n    )\n",
     "    hvac.hot_water_system.apply_heat_draw(ambient_temperature, self._time_step_sec)\n"),
    ("simulator_flexible_floor_plan.py",
     "            total_reheat_w, coil_entering_air_temps\n        )\n    )\n",
     "    hvac.hot_water_system.apply_heat_draw(ambient_temperature, self._time_step_sec)\n"),
]


def apply(pkg: Path) -> None:
    for edit in EDITS:
        name, anchor, after = edit[0], edit[1], edit[2]
        f = pkg / SIM / name
        text = f.read_text(encoding="utf-8")
        assert text.count(anchor) == 1, (name, anchor)
        new = anchor + after if after is not None else edit[3]
        f.write_text(text.replace(anchor, new), encoding="utf-8")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import smart_buildings
    src = Path(smart_buildings.__file__).resolve().parent
    dst = Path(a.out).resolve() / "smart_buildings"
    assert not dst.exists(), f"{dst} exists; remove it first"
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
    apply(dst)
    print("patched copy in", dst)


if __name__ == "__main__":
    main()
