"""Support for Coinbase sensors."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import ATTR_ATTRIBUTION

from .const import (
    API_ACCOUNT_AMOUNT,
    API_ACCOUNT_BALANCE,
    API_ACCOUNT_CURRENCY,
    API_ACCOUNT_ID,
    API_ACCOUNT_NAME,
    API_ACCOUNT_NATIVE_BALANCE,
    API_RATES,
    CONF_CURRENCIES,
    CONF_EXCHANGE_RATES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

ATTR_NATIVE_BALANCE = "Balance in native currency"

CURRENCY_ICONS = {
    "BTC": "mdi:currency-btc",
    "ETH": "mdi:currency-eth",
    "EUR": "mdi:currency-eur",
    "LTC": "mdi:litecoin",
    "USD": "mdi:currency-usd",
}

DEFAULT_COIN_ICON = "mdi:currency-usd-circle"

ATTRIBUTION = "Data provided by coinbase.com"


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Coinbase sensor platform."""
    instance = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    provided_currencies = [
        account[API_ACCOUNT_CURRENCY] for account in instance.accounts
    ]

    desired_currencies = []

    if CONF_CURRENCIES in config_entry.options:
        desired_currencies = config_entry.options[CONF_CURRENCIES]

    exchange_native_currency = instance.exchange_rates[API_ACCOUNT_CURRENCY]

    for currency in desired_currencies:
        if currency not in provided_currencies:
            _LOGGER.warning(
                "The currency %s is no longer provided by your account, please check "
                "your settings in Coinbase's developer tools",
                currency,
            )
            continue
        entities.append(AccountSensor(instance, currency))

    if CONF_EXCHANGE_RATES in config_entry.options:
        for rate in config_entry.options[CONF_EXCHANGE_RATES]:
            entities.append(
                ExchangeRateSensor(
                    instance,
                    rate,
                    exchange_native_currency,
                )
            )

    async_add_entities(entities)


class AccountSensor(SensorEntity):
    """Representation of a Coinbase.com sensor."""

    def __init__(self, coinbase_data, currency):
        """Initialize the sensor."""
        self._coinbase_data = coinbase_data
        self._currency = currency
        for account in coinbase_data.accounts:
            if account[API_ACCOUNT_CURRENCY] == currency:
                self._attr_name = f"Coinbase {account[API_ACCOUNT_NAME]}"
                self._attr_unique_id = (
                    f"coinbase-{account[API_ACCOUNT_ID]}-wallet-"
                    f"{account[API_ACCOUNT_CURRENCY]}"
                )
                self._attr_state = account[API_ACCOUNT_BALANCE][API_ACCOUNT_AMOUNT]
                self._attr_unit_of_measurement = account[API_ACCOUNT_CURRENCY]
                self._native_balance = account[API_ACCOUNT_NATIVE_BALANCE][
                    API_ACCOUNT_AMOUNT
                ]
                self._native_currency = account[API_ACCOUNT_NATIVE_BALANCE][
                    API_ACCOUNT_CURRENCY
                ]
                break
        self._attr_icon = CURRENCY_ICONS.get(
            self.unit_of_measurement, DEFAULT_COIN_ICON
        )

    def update(self):
        """Get the latest state of the sensor."""
        self._coinbase_data.update()
        for account in self._coinbase_data.accounts:
            if account[API_ACCOUNT_CURRENCY] == self._currency:
                self._attr_state = account[API_ACCOUNT_BALANCE][API_ACCOUNT_AMOUNT]
                self._native_balance = account[API_ACCOUNT_NATIVE_BALANCE][
                    API_ACCOUNT_AMOUNT
                ]
                self._native_currency = account[API_ACCOUNT_NATIVE_BALANCE][
                    API_ACCOUNT_CURRENCY
                ]
                break
        self._attr_extra_state_attributes = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_NATIVE_BALANCE: f"{self._native_balance} {self._native_currency}",
        }


class ExchangeRateSensor(SensorEntity):
    """Representation of a Coinbase.com sensor."""

    def __init__(self, coinbase_data, exchange_currency, native_currency):
        """Initialize the sensor."""
        self._coinbase_data = coinbase_data
        self.currency = exchange_currency
        self._attr_name = f"{exchange_currency} Exchange Rate"
        self._attr_unique_id = (
            f"coinbase-{coinbase_data.user_id}-xe-{exchange_currency}"
        )
        self._attr_state = round(
            1 / float(coinbase_data.exchange_rates[API_RATES][exchange_currency]), 2
        )
        self._attr_unit_of_measurement = native_currency
        self._attr_icon = CURRENCY_ICONS.get(exchange_currency, DEFAULT_COIN_ICON)

    def update(self):
        """Get the latest state of the sensor."""
        self._coinbase_data.update()
        self._attr_state = round(
            1 / float(self._coinbase_data.exchange_rates.rates[self.currency]), 2
        )
        self._attr_extra_state_attributes = {ATTR_ATTRIBUTION: ATTRIBUTION}
