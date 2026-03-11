import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD

from .const import SCAN_INTERVAL

import time

_LOGGER = logging.getLogger(__name__)


class HostmanagerCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self.hass = hass
        self.host = entry.data[CONF_HOST]
        self.port = entry.data[CONF_PORT]
        self.username = entry.data[CONF_USERNAME]
        self.password = entry.data[CONF_PASSWORD]
        self.endpoint = entry.data["endpoint"]

        self._session = async_get_clientsession(hass)
        self._ubus_session_id = None

        super().__init__(
            hass,
            _LOGGER,
            name="ubus_hostmanager",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    async def _login(self):
        url = f"http://{self.host}:{self.port}{self.endpoint}"

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": [
                "00000000000000000000000000000000",
                "session",
                "login",
                {
                    "username": self.username,
                    "password": self.password,
                },
            ],
        }

        async with self._session.post(url, json=payload) as resp:
            data = await resp.json()

        try:
            self._ubus_session_id = data["result"][1]["ubus_rpc_session"]
            _LOGGER.debug("Logged in successfully")
        except Exception:
            raise Exception("Login failed")

    async def _call_ubus(self, object_name, method):
        if not self._ubus_session_id:
            await self._login()

        url = f"http://{self.host}:{self.port}{self.endpoint}"

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": [
                self._ubus_session_id,
                object_name,
                method,
            ],
        }

        async with self._session.post(url, json=payload) as resp:
            data = await resp.json()

        if data.get("result", [1])[0] != 0:
            _LOGGER.debug("Session expired, re-logging")
            await self._login()
            return await self._call_ubus(object_name, method)

        _LOGGER.debug("Router response: %s", data)

        return data

    async def _async_update_data(self):
        _LOGGER.debug("Starting device refresh")

        start = time.time()
        try:
            data = await self._call_ubus("hostmanager.device", "get")
        except Exception as err:
            _LOGGER.error("Failed to fetch devices: %s", err)
            raise

        _LOGGER.debug("Device refresh complete")
        _LOGGER.debug("Refresh took %.2fs", time.time() - start)

        result = data.get("result", [])
        if len(result) < 2:
            _LOGGER.warning("Unexpected ubus response: %s", data)
            return {}

        return result[1]