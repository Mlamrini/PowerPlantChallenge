from abc import abstractmethod
from enum import Enum


class FuelType(str, Enum):
    GAS = 'gas(euro/MWh)'
    CO2 = 'co2(euro/ton)'
    KEROSENE = 'kerosine(euro/MWh)'
    WIND = 'wind(%)'


class PlantType(str, Enum):
    GAS_FIRED = 'gasfired'
    TURBO_JET = 'turbojet'
    WIND_TURBINE = 'windturbine'


class PowerPlant:
    """
    Represent a power plant.
    """

    def __init__(self, name, plant_type, efficiency, minimal_power, maximal_power):
        self.name = name
        self.plant_type = plant_type
        self.efficiency = efficiency
        self.minimal_power = minimal_power
        self.maximal_power = maximal_power

    @abstractmethod
    def get_capacity(self, fuels):
        """
        This method will be used to compute the real production capacity of a plant.
        """

    @abstractmethod
    def compute_cost(self, fuels):
        """
        This method will be used to compute the production cost of a plant for 1 MWh.
        """

    @staticmethod
    def from_json(plant: dict):
        """
        This method will be used to construct the Power Plant from the request payload.
        """

        name = plant['name']
        plant_type = plant['type']
        efficiency = plant['efficiency']
        minimal_power = plant['pmin']
        maximal_power = plant['pmax']

        switcher = {
            PlantType.GAS_FIRED: GasFiredPowerPlant(name, plant_type, efficiency, minimal_power, maximal_power),
            PlantType.TURBO_JET: TurboJetPowerPlant(name, plant_type, efficiency, minimal_power, maximal_power),
            PlantType.WIND_TURBINE: WindTurbinePowerPlant(name, plant_type, efficiency, minimal_power, maximal_power)
        }

        return switcher.get(PlantType(plant_type))


class GasFiredPowerPlant(PowerPlant):
    def get_capacity(self, fuels):
        return self.maximal_power

    def compute_cost(self, fuels):
        # print(self.name + " -> " + str(fuels[FuelType.GAS.value] * 1 / self.efficiency + 0.3 * fuels[FuelType.CO2.value]))
        return fuels[FuelType.GAS.value] * 1 / self.efficiency + 0.3 * fuels[FuelType.CO2.value]


class TurboJetPowerPlant(PowerPlant):
    def get_capacity(self, fuels):
        return self.maximal_power

    def compute_cost(self, fuels):
        # print(self.name + " -> " + str(fuels[FuelType.KEROSENE.value] * 1 / self.efficiency))
        return fuels[FuelType.KEROSENE.value] * 1 / self.efficiency


class WindTurbinePowerPlant(PowerPlant):
    def get_capacity(self, fuels):
        return self.maximal_power * fuels[FuelType.WIND.value] / 100 * 1 / self.efficiency

    def compute_cost(self, fuels):
        return 0.
