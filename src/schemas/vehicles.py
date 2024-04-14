from pydantic import BaseModel, Field


class VehicleSchema(BaseModel):
    id: str


class HVehicleSchema(BaseModel):
    id: str = Field(alias="id")
    color: str = Field(alias="color")
    has_battery_device: bool = Field(alias="has.battery.device")
    device_battery_capacity: int = Field(alias="device.battery.capacity")
    vehicle_mass: int = Field(alias="vehicleMass")
    front_surface_area: float = Field(alias="frontSurfaceArea")
    air_drag_coefficient: float = Field(alias="airDragCoefficient")
    constant_power_intake: int = Field(alias="constantPowerIntake")
    internal_moment_of_inertia: float = Field(alias="internalMomentOfInertia")
    radial_drag_coefficient: float = Field(alias="radialDragCoefficient")
    roll_drag_coefficient: float = Field(alias="rollDragCoefficient")
    propulsion_efficiency: float = Field(alias="propulsionEfficiency")
    recuperation_efficiency: float = Field(alias="recuperationEfficiency")
    stopping_threshold: float = Field(alias="stoppingThreshold")
