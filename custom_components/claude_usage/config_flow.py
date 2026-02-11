"""Config flow for Claude Usage integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ClaudeApiAuthError, ClaudeApiClient, ClaudeApiError
from .const import CONF_SESSION_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)

SESSION_KEY_SCHEMA = vol.Schema(
    {vol.Required(CONF_SESSION_KEY): str}
)


class ClaudeUsageConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Claude Usage."""

    VERSION = 1

    async def _async_validate_session_key(
        self, session_key: str
    ) -> tuple[str | None, dict[str, str]]:
        """Validate the session key. Returns (org_id, errors)."""
        session = async_get_clientsession(self.hass)
        client = ClaudeApiClient(session, session_key)

        try:
            org_id = await client.async_validate_session_key()
        except ClaudeApiAuthError:
            return None, {"base": "invalid_auth"}
        except ClaudeApiError:
            return None, {"base": "cannot_connect"}
        except Exception:
            _LOGGER.exception("Unexpected error during validation")
            return None, {"base": "unknown"}

        return org_id, {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            org_id, errors = await self._async_validate_session_key(
                user_input[CONF_SESSION_KEY]
            )
            if not errors:
                await self.async_set_unique_id(org_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Claude Usage",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=SESSION_KEY_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth trigger."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            org_id, errors = await self._async_validate_session_key(
                user_input[CONF_SESSION_KEY]
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates=user_input,
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=SESSION_KEY_SCHEMA,
            errors=errors,
        )
