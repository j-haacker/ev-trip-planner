from copy import deepcopy
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import minimize_scalar

class battery():

    def __init__(self,
                 capacity,
                 charging_rate: callable):
        self.capa = capacity
        if isinstance(charging_rate, float):
            self.charging_rate = lambda x: charging_rate
        elif callable(charging_rate):
            self.charging_rate = charging_rate
        else:
            charging_rate = np.array(charging_rate)
            self.charging_rate = interp1d(charging_rate[:,0], charging_rate[:,1])
        self.state = 80
    
    def charge(self, stop_percentage: float = None, kWh: float = None, duration: float = None) -> float:
        if stop_percentage:
            kWh = self.kWh(stop_percentage) - self.kWh()
        if kWh is not None:
            seconds_counter = 0
            while kWh > 0:
                tmp = self.charging_rate(self.state)/60/60  # per second
                self.state += tmp /self.capa *100
                kWh -= tmp
                if self.state > 100:
                    self.state = 100
                    kWh = 0
                seconds_counter += 1
            return seconds_counter/60
        initial_kWh = self.kWh()
        for i in range(duration*60):
            self.state += self.charging_rate(self.state)/60/60 /self.capa *100  # per second
        return self.kWh() - initial_kWh

    def kWh(self, percentage: float = None):
        if percentage is None:
            percentage = self.state
        return percentage/100*self.capa


class vehicle():

    def __init__(self,
                 battery_capacity_kWh: float = 75,
                 battery_charging_rate_kWh_per_min: float = 75*.8/20,
                 battery_reserve_percent: float = 10,
                 power_per_kmh: callable = \
                    lambda velocity: 8.28571 - 0.0307143 * velocity + 0.00107143 * velocity**2,
                 battery_: "battery" = None,
                 ):
        if battery_ is None:
            self.battery = battery(battery_capacity_kWh, battery_charging_rate_kWh_per_min*60)
        else:
            self.battery = battery_
        self.batt_reserve = battery_reserve_percent
        self.power_consumption = power_per_kmh

    def min_break_duration(self,
                           distance: float,
                           speed: float,
                           end_batt_state: float = None,
                           start_batt_state: float = 100
                           ) -> float:
        if end_batt_state is None:
            end_batt_state = self.batt_reserve
        self.battery.state = start_batt_state
        result = []
        while distance > 0:
            if (
                self.power_consumption(speed)*distance/100
                < self.battery.kWh()-self.battery.kWh(end_batt_state)
            ):
                distance = 0
            else:
                if (
                    self.power_consumption(speed)*distance/100
                    < self.battery.kWh()-self.battery.kWh(self.batt_reserve)
                ):
                    self.battery.state = (self.battery.kWh() - distance / speed * self.power_consumption(speed))\
                                         / self.battery.capa * 100
                    distance = 0
                    result.append(self.battery.charge(stop_percentage=end_batt_state))
                else:
                    distance -= (self.battery.kWh(start_batt_state) - self.battery.kWh(self.batt_reserve))\
                                / self.power_consumption(speed) * speed
                    self.battery.state = self.batt_reserve
                    if (
                        self.power_consumption(speed)*distance/100
                        > self.battery.kWh(80)-self.battery.kWh(end_batt_state)
                    ):
                        result.append(self.battery.charge(stop_percentage=80))
                    else:
                        result.append(self.battery.charge(stop_percentage=(self.power_consumption(speed)*distance/100+self.battery.kWh(end_batt_state))/self.battery.capa*100))
        return result
    
    def max_trip_speed(self,
                       distance: float,
                       break_number: int = 0,
                       break_duration: float = 15,
                       end_batt_state: float = None,
                       start_batt_state: float = 100
                       ) -> float:
        if end_batt_state is None:
            end_batt_state = self.batt_reserve
        available_charge = self.battery.kWh(start_batt_state) - self.battery.kWh(end_batt_state)
        if break_number >= 1:
            batt_clone = deepcopy(self.battery)
            def charge_test(batt, start, duration):
                batt.state = start
                batt.charge(duration=duration)
                return batt.state
            start = max(self.batt_reserve,
                        minimize_scalar(lambda x: charge_test(self.battery, x, break_duration)-end_batt_state,
                            bounds=(self.batt_reserve, end_batt_state), method="bounded", options=dict(xatol=0.1)).x)
            batt_clone.state = start
            available_charge += batt_clone.charge(duration=break_duration)
        if break_number >=2:
            batt_clone.state = self.batt_reserve
            available_charge += (break_number-1)*batt_clone.charge(duration=break_duration)
        return minimize_scalar(lambda x: (self.power_consumption(x)*distance/100-available_charge)**2,
                               bounds=(0, 999), method="bounded").x


if __name__ == "__main__":
    ev = vehicle()

    print("Possible speed for a 450 km ride give two 15 min breaks (starting with 100 %, ending with 10 %):\n",
          ev.max_trip_speed(450, break_number=2, break_duration=15, end_batt_state=10, start_batt_state=100))
