"""Auto-off timers and indicator LED brightness."""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import LED_MAX, OUTLETS, TIMER_MAX_UNITS, TIMER_SECONDS_PER_UNIT
from .coordinator import BGSocketConfigEntry, BGSocketCoordinator
from .entity import BGSocketEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BGSocketConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[NumberEntity] = [
        BGSocketAutoOff(coordinator, outlet) for outlet in OUTLETS
    ]
    entities.append(BGSocketLedBrightness(coordinator))
    async_add_entities(entities)


class BGSocketAutoOff(BGSocketEntity, NumberEntity):
    """Turn the outlet off by itself after this many minutes. 0 disables it."""

    _attr_device_class = NumberDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_native_min_value = 0
    _attr_native_max_value = TIMER_MAX_UNITS
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: BGSocketCoordinator, outlet: int) -> None:
        super().__init__(coordinator, f"maxworktime{outlet}", f"Socket {outlet} auto-off")

    @property
    def native_value(self) -> float | None:
        value = self._value
        return None if value is None else round(value / TIMER_SECONDS_PER_UNIT)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_state(
            **{self._key: int(value) * TIMER_SECONDS_PER_UNIT}
        )


class BGSocketLedBrightness(BGSocketEntity, NumberEntity):
    """Brightness of the indicator LED."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_min_value = 0
    _attr_native_max_value = LED_MAX
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: BGSocketCoordinator) -> None:
        super().__init__(coordinator, "idcbrightness", "LED brightness")

    @property
    def native_value(self) -> float | None:
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_state(idcbrightness=int(value))
