from scipy.optimize import minimize_scalar

# some roughly estimated parameters for an imaginary electric vehicle to
# test the script:
# 21kWh/100km @130km/h
# 17kWh/100km @110km/h
# 75kWh @100%

class battery():

    def __init__(self,
                 capacity,
                 charge_rate):
        self.capa = capacity
        self.charge_rate = charge_rate
        self.state = 80
    
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
                    lambda velocity: 8.28571 - 0.0307143 * velocity + 0.00107143 * velocity**2
                 ):
        self.battery = battery(battery_capacity_kWh, battery_charging_rate_kWh_per_min)
        self.batt_reserve = battery_reserve_percent
        self.power_consumption = power_per_kmh

    def min_break_duration(self,
                           distance: float,
                           speed: float,
                           end_batt_state: float = None,
                           start_batt_state: float = 100
                           ) -> float:
        result = (
            - self.battery.kWh(start_batt_state)
            + distance/100*self.power_consumption(speed)
            + self.battery.kWh(end_batt_state)
        )/self.battery.charge_rate
        return result if result > 0 else 0
    
    def max_trip_speed(self,
                       distance: float,
                       break_number: int = 0,
                       break_duration: float = 15,
                       end_batt_state: float = None,
                       start_batt_state: float = 100
                       ) -> float:
        if end_batt_state is None:
            end_batt_state = self.batt_reserve
        available_charge = self.battery.kWh(start_batt_state) \
                           + break_number*self.battery.charge_rate*break_duration \
                           - self.battery.kWh(end_batt_state)
        return minimize_scalar(lambda x: (self.power_consumption(x)*distance/100-available_charge)**2,
                               bounds=(0, 999), method="bounded").x
        

if __name__ == "__main__":
    ev = vehicle()

    print("Possible speed for a 450 km ride give two 15 min breaks (starting with 100 %, ending with 10 %):\n",
          ev.max_trip_speed(450, break_number=2, break_duration=15, end_batt_state=10, start_batt_state=100))
