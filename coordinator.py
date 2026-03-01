import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class HostmanagerCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, host: str, port: int):
        self.host = host
        self.port = port
        self._session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name="ubus_hostmanager",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        url = f"http://{self.host}:{self.port}/ubus.sh"

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": [
                "00000000000000000000000000000000",
                "hostmanager.device",
                "get",
            ],
        }

        async with self._session.post(url, json=payload) as resp:
            data = await resp.json()

        result = data.get("result", [])
        if len(result) < 2:
            return {}

        return result[1]