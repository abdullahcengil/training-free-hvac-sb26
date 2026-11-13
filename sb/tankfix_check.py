"""Known-answer checks of the patched tank (sb/make_tankfix.py), run on the patched copy:

    PYTHONPATH=D:/SmartBuildings_data/kit_tankfix python -m sb.tankfix_check

1. Energy is conserved over charge/discharge cycles: gas burned = heat drawn + standing loss + heat stored.
2. Dropping the setpoint below the tank gives no unbilled heat: the burner is off and the tank pays for the draw.
3. With the setpoint held (our controller holds 350 K), the bill equals the shipped formula, flow x (T_set - T_return)
   plus the standing loss, every step: the fix cannot change our controller's score.
"""

from __future__ import annotations

import smart_buildings
from smart_buildings.smart_control.simulator import boiler
from smart_buildings.smart_control.utils import constants

STEP = 300.0
CW = constants.WATER_HEAT_CAPACITY * constants.WATER_DENSITY


def make(setpoint: float) -> boiler.Boiler:
    return boiler.Boiler(supply_water_temperature_setpoint=setpoint, heating_rate=0.5, cooling_rate=0.1)


def main() -> None:
    print("package:", smart_buildings.__file__)
    b = make(322.0)
    assert b.energy_balance, "the patched copy is not on the path"
    cap = CW * b._water_capacity
    t0, burned, drawn, lost = b.supply_water_temperature_sensor, 0.0, 0.0, 0.0
    for k in range(300):
        b.supply_water_temperature_setpoint = 348.0 if k % 60 < 12 else 310.0
        loss = b.compute_thermal_dissipation_rate(b.supply_water_temperature_sensor, 280.0)
        b.apply_heat_draw(40_000.0, 280.0, STEP)
        burned += b.compute_thermal_energy_rate(0.0, 280.0, 0.0) * STEP
        drawn += 40_000.0 * STEP
        lost += loss * STEP
    stored = cap * (b.supply_water_temperature_sensor - t0)
    err = abs(burned - drawn - lost - stored) / burned
    print(f"1. cycles: burned {burned / 3.6e6:.2f} kWh = drawn {drawn / 3.6e6:.2f} + lost {lost / 3.6e6:.3f} "
          f"+ stored {stored / 3.6e6:.3f} (relative error {err:.1e})")
    assert err < 1e-9

    b = make(348.0)
    b.supply_water_temperature_setpoint = 310.0
    t0 = b.supply_water_temperature_sensor
    b.apply_heat_draw(50_000.0, 280.0, STEP)
    gas = b.compute_thermal_energy_rate(0.0, 280.0, 0.0)
    drop = t0 - b.supply_water_temperature_sensor
    print(f"2. setpoint dropped: gas {gas:.1f} W, tank {drop:.2f} K cooler after one 50 kW step")
    assert gas == 0.0 and drop > 2.3

    worst = 0.0
    for t_ret, flow in ((330.0, 0.0004), (340.0, 0.0010), (320.0, 0.0020), (345.0, 0.0001)):
        b = make(350.0)
        for _ in range(12):
            draw = CW * flow * (b.supply_water_temperature_sensor - t_ret)
            b.apply_heat_draw(draw, 285.0, STEP)
            new = b.compute_thermal_energy_rate(t_ret, 285.0, flow)
            shipped = CW * flow * (350.0 - t_ret) + b.compute_thermal_dissipation_rate(350.0, 285.0)
            worst = max(worst, abs(new - shipped) / shipped)
        assert abs(b.supply_water_temperature_sensor - 350.0) < 1e-9
    print(f"3. setpoint held at 350 K: bill equals the shipped formula (largest relative difference {worst:.1e})")
    assert worst < 1e-9
    print("all checks passed")


if __name__ == "__main__":
    main()
