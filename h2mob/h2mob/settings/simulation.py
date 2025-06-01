import random

from enum import Enum
from functools import lru_cache

from h2mob.settings import general

from pydantic import BaseModel


class FuelType(Enum):
    petrol = "petrol"
    hydrogen = "hydrogen"


class Vehicle(BaseModel):
    colour: tuple[int, int, int, int]  # RGBA
    fuel_type: FuelType
    charging_duration_seconds: int = 5 * 60  # 5 mins

    tank_liters: int  # Fuel tank capacity
    mass_kg: int  # vehicleMass
    front_surface_area: float  # frontSurfaceArea
    air_drag_coefficient: float  # airDragCoefficient
    roll_drag_coefficient: float  # rollDragCoefficient

    internal_moment_of_inertia: float  # internalMomentOfInertia

    constant_power_intake: int  # constantPowerIntake
    propulsion_efficiency: float  # gearEfficiency
    recuperatoin_efficiency: float = 0.0  # Value between 0 and 1

    wheel_radius: float  # wheelRadius
    gear_ratio: float  # gearRatio
    maximum_torque: float  # maximumTorque
    maximum_power: float  # maximumPower
    maximum_recuperation_torque: float  # maximumRecuperationTorque
    maximum_recuperation_power: float  # maximumRecuperationPower
    internal_battery_resistance: float  # internalBatteryResistance
    nominal_battery_voltage: float  # nominalBatteryVoltage


class SimulationConfig(general.GeneralConfig):
    fuel_threshold_liters: int = 20
    petrol_vehicle_colour: tuple[int, int, int, int] = (255, 0, 0, 255)


def get_murai_vehicle_properties() -> Vehicle:
    return Vehicle(
        colour=(0, 255, 0, 255),
        fuel_type=FuelType.hydrogen,
        # Assume short idle charge duration for sim
        charging_duration_seconds=5 * 60,
        # Close to usable hydrogen tank capacity converted to liters
        tank_liters=random.randint(20, 60),
        mass_kg=random.randint(1900, 1950),
        front_surface_area=2.23,  # 0.8 × width × height
        air_drag_coefficient=0.29,  # Cd from source
        constant_power_intake=100,  # Default value
        internal_moment_of_inertia=0.01,  # Default as actual not available
        roll_drag_coefficient=0.012,  # From PDF
        propulsion_efficiency=0.97,  # Gear efficiency
        # Estimated good efficiency for regen braking
        recuperatoin_efficiency=0.8,
        wheel_radius=0.3706,  # From tire size
        gear_ratio=11.691,  # Reduction gear ratio
        maximum_torque=300.0,  # Nm
        maximum_power=134000.0,  # W
        maximum_recuperation_torque=300.0,  # Nm
        maximum_recuperation_power=42100.0,  # W
        internal_battery_resistance=0.3629,  # Ohm
        nominal_battery_voltage=310.8,  # V
    )


def get_petrol_vehicle_properties() -> Vehicle:
    return Vehicle(
        colour=(255, 0, 0, 255),
        fuel_type=FuelType.petrol,
        charging_duration_seconds=5 * 60,
        tank_liters=random.randint(20, 60),  # Typical petrol tank size
        # Common mass range for compact/mid-size ICE cars
        mass_kg=random.randint(1200, 1600),
        # Estimated from car dimensions
        front_surface_area=round(random.uniform(2.0, 2.5), 2),
        # Common Cd for modern sedans
        constant_power_intake=0,  # No constant draw from battery like in EVs
        air_drag_coefficient=round(random.uniform(0.28, 0.35), 3),
        # Slightly higher due to engine drivetrain complexity
        internal_moment_of_inertia=0.015,
        # Typical rolling resistance
        roll_drag_coefficient=round(random.uniform(0.01, 0.015), 4),
        # Efficiency for ICE drivetrains
        propulsion_efficiency=round(random.uniform(0.25, 0.35), 3),
        recuperatoin_efficiency=0.0,  # No regen braking
        # 16"–17" rims with tire
        wheel_radius=round(random.uniform(0.31, 0.34), 4),
        # Overall gear ratio including differential
        gear_ratio=round(random.uniform(4.0, 6.5), 3),
        maximum_torque=random.randint(150, 250),  # Nm, mid-range ICE torque
        maximum_power=random.randint(70000, 110000),  # W, ~95–150 hp
        maximum_recuperation_torque=0.0,  # No regen braking
        maximum_recuperation_power=0.0,  # No regen braking
        internal_battery_resistance=0.0,  # Not applicable to ICE simulation
        nominal_battery_voltage=12.0,  # Standard car battery voltage
    )


@lru_cache(maxsize=1)
def get_simulation_config() -> SimulationConfig:
    return SimulationConfig()
