from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for dev_id, data in coordinator.data.items():
        mac = data.get("mac-address")
        if mac:
            entities.append(
                HostmanagerScannerEntity(
                    coordinator,
                    dev_id,
                )
            )

    async_add_entities(entities)


class HostmanagerScannerEntity(CoordinatorEntity, ScannerEntity):
    def __init__(self, coordinator, dev_id):
        super().__init__(coordinator)
        self._dev_id = dev_id

    @property
    def unique_id(self):
        device = self.coordinator.data.get(self._dev_id, {})
        return device.get("mac-address")

    @property
    def name(self):
        device = self.coordinator.data.get(self._dev_id, {})
        return device.get("hostname", self._dev_id)

    @property
    def source_type(self):
        return SourceType.ROUTER

    @property
    def is_connected(self):
        device = self.coordinator.data.get(self._dev_id, {})
        return device.get("state") == "connected"

    @property
    def ip_address(self):
        device = self.coordinator.data.get(self._dev_id, {})
        ipv4 = device.get("ipv4", {})
        for ip_info in ipv4.values():
            if ip_info.get("state") == "connected":
                return ip_info.get("address")
        return None

    @property
    def extra_state_attributes(self):
        device = self.coordinator.data.get(self._dev_id, {})
        wireless = device.get("wireless", {})
        return {
            "l2interface": device.get("l2interface"),
            "l3interface": device.get("l3interface"),
            "technology": device.get("technology"),
            "rssi": wireless.get("rssi"),
            "radio": wireless.get("radio"),
        }