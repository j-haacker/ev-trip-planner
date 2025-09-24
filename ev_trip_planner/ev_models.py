from ev_trip_planner import battery, vehicle
from numpy import polyval


__all__ = ["tesla_y_long"]


def tesla_y_long():
    # Tesla Y long range
    batt = battery(
        capacity=75,
        charging_rate=[
            # data scrapped from https://zecar.com/resources/tesla-model-y-charging-guide
            [0, 211],
            [10, 211],
            [15, 198],
            [20, 185],
            [25, 172],
            [30, 157],
            [35, 139],
            [40, 125],
            [45, 113],
            [50, 101],
            [55, 90],
            [60, 81],
            [65, 76],
            [70, 71],
            [75, 61],
            [80, 46],
            [95, 11],  # last two added
            [100, 11],
        ],
    )
    return vehicle(
        battery_=batt,
        # below a quadratic velocity dependent approx. is given
        # corresponding to about 17 kWh/100km @ 110 km/h (22@130)
        power_per_kmh=lambda velocity, temperature: (
            8.29 - 0.0307 * velocity + 0.00107 * velocity**2
        )
        / polyval([2.01e-8, -6.27e-6, -6.93e-5, 1.10e-2, 8.43e-1], temperature),
    )
