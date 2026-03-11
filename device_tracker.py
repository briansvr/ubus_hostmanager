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
    seen_macs = set()

    for data in coordinator.data.values():
        mac = data.get("mac-address")
        if mac and mac.lower() not in seen_macs:
            seen_macs.add(mac.lower())
            entities.append(
                HostmanagerScannerEntity(coordinator, mac)
            )

    async_add_entities(entities)


class HostmanagerScannerEntity(CoordinatorEntity, ScannerEntity):
    def __init__(self, coordinator, mac):
        super().__init__(coordinator)
        self._mac = mac.lower()

    @property
    def unique_id(self):
        return self._mac

    def _get_device(self):
        for device in self.coordinator.data.values():
            if device.get("mac-address", "").lower() == self._mac:
                return device
        return {}

    @property
    def name(self):
        device = self._get_device()
        return device.get("hostname", self._mac)

    @property
    def source_type(self):
        return SourceType.ROUTER

    @property
    def is_connected(self):
        device = self._get_device()
        return device.get("state") == "connected"

    @property
    def ip_address(self):
        device = self._get_device()
        ipv4 = device.get("ipv4")

        if not ipv4:
            return None

        if isinstance(ipv4, list):
            return None

        if isinstance(ipv4, dict):
            for ip_info in ipv4.values():
                if ip_info.get("state") == "connected":
                    return ip_info.get("address")

        return None