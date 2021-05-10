"""Definitions for DSMR Reader sensors added to MQTT."""

from homeassistant.const import (
    ATTR_NAME,
    CURRENCY_EURO,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TIMESTAMP,
    DEVICE_CLASS_VOLTAGE,
    ELECTRICAL_CURRENT_AMPERE,
    ENERGY_KILO_WATT_HOUR,
    POWER_KILO_WATT,
    VOLT,
    VOLUME_CUBIC_METERS,
)


def dsmr_transform(value):
    """Transform DSMR version value to right format."""
    if value.isdigit():
        return float(value) / 10
    return value


def tariff_transform(value):
    """Transform tariff from number to description."""
    if value == "1":
        return "low"
    return "high"


DEFINITIONS = {
    "dsmr/reading/electricity_delivered_1": {
        ATTR_NAME: "Low tariff usage",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/reading/electricity_returned_1": {
        ATTR_NAME: "Low tariff returned",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/reading/electricity_delivered_2": {
        ATTR_NAME: "High tariff usage",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/reading/electricity_returned_2": {
        ATTR_NAME: "High tariff returned",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/reading/electricity_currently_delivered": {
        ATTR_NAME: "Current power usage",
        "enable_default": True,
        "device_class": DEVICE_CLASS_POWER,
        "unit": POWER_KILO_WATT,
    },
    "dsmr/reading/electricity_currently_returned": {
        ATTR_NAME: "Current power return",
        "enable_default": True,
        "device_class": DEVICE_CLASS_POWER,
        "unit": POWER_KILO_WATT,
    },
    "dsmr/reading/phase_currently_delivered_l1": {
        ATTR_NAME: "Current power usage L1",
        "enable_default": True,
        "device_class": DEVICE_CLASS_POWER,
        "unit": POWER_KILO_WATT,
    },
    "dsmr/reading/phase_currently_delivered_l2": {
        ATTR_NAME: "Current power usage L2",
        "enable_default": True,
        "device_class": DEVICE_CLASS_POWER,
        "unit": POWER_KILO_WATT,
    },
    "dsmr/reading/phase_currently_delivered_l3": {
        ATTR_NAME: "Current power usage L3",
        "enable_default": True,
        "device_class": DEVICE_CLASS_POWER,
        "unit": POWER_KILO_WATT,
    },
    "dsmr/reading/phase_currently_returned_l1": {
        ATTR_NAME: "Current power return L1",
        "enable_default": True,
        "device_class": DEVICE_CLASS_POWER,
        "unit": POWER_KILO_WATT,
    },
    "dsmr/reading/phase_currently_returned_l2": {
        ATTR_NAME: "Current power return L2",
        "enable_default": True,
        "device_class": DEVICE_CLASS_POWER,
        "unit": POWER_KILO_WATT,
    },
    "dsmr/reading/phase_currently_returned_l3": {
        ATTR_NAME: "Current power return L3",
        "enable_default": True,
        "device_class": DEVICE_CLASS_POWER,
        "unit": POWER_KILO_WATT,
    },
    "dsmr/reading/extra_device_delivered": {
        ATTR_NAME: "Gas meter usage",
        "enable_default": True,
        "icon": "mdi:fire",
        "unit": VOLUME_CUBIC_METERS,
    },
    "dsmr/reading/phase_voltage_l1": {
        ATTR_NAME: "Current voltage L1",
        "enable_default": True,
        "device_class": DEVICE_CLASS_VOLTAGE,
        "unit": VOLT,
    },
    "dsmr/reading/phase_voltage_l2": {
        ATTR_NAME: "Current voltage L2",
        "enable_default": True,
        "device_class": DEVICE_CLASS_VOLTAGE,
        "unit": VOLT,
    },
    "dsmr/reading/phase_voltage_l3": {
        ATTR_NAME: "Current voltage L3",
        "enable_default": True,
        "device_class": DEVICE_CLASS_VOLTAGE,
        "unit": VOLT,
    },
    "dsmr/reading/phase_power_current_l1": {
        ATTR_NAME: "Phase power current L1",
        "enable_default": True,
        "device_class": DEVICE_CLASS_CURRENT,
        "unit": ELECTRICAL_CURRENT_AMPERE,
    },
    "dsmr/reading/phase_power_current_l2": {
        ATTR_NAME: "Phase power current L2",
        "enable_default": True,
        "device_class": DEVICE_CLASS_CURRENT,
        "unit": ELECTRICAL_CURRENT_AMPERE,
    },
    "dsmr/reading/phase_power_current_l3": {
        ATTR_NAME: "Phase power current L3",
        "enable_default": True,
        "device_class": DEVICE_CLASS_CURRENT,
        "unit": ELECTRICAL_CURRENT_AMPERE,
    },
    "dsmr/reading/timestamp": {
        ATTR_NAME: "Telegram timestamp",
        "enable_default": False,
        "device_class": DEVICE_CLASS_TIMESTAMP,
    },
    "dsmr/consumption/gas/delivered": {
        ATTR_NAME: "Gas usage",
        "enable_default": True,
        "icon": "mdi:fire",
        "unit": VOLUME_CUBIC_METERS,
    },
    "dsmr/consumption/gas/currently_delivered": {
        ATTR_NAME: "Current gas usage",
        "enable_default": True,
        "icon": "mdi:fire",
        "unit": VOLUME_CUBIC_METERS,
    },
    "dsmr/consumption/gas/read_at": {
        ATTR_NAME: "Gas meter read",
        "enable_default": True,
        "device_class": DEVICE_CLASS_TIMESTAMP,
    },
    "dsmr/day-consumption/electricity1": {
        ATTR_NAME: "Low tariff usage",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/day-consumption/electricity2": {
        ATTR_NAME: "High tariff usage",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/day-consumption/electricity1_returned": {
        ATTR_NAME: "Low tariff return",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/day-consumption/electricity2_returned": {
        ATTR_NAME: "High tariff return",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/day-consumption/electricity_merged": {
        ATTR_NAME: "Power usage total",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/day-consumption/electricity_returned_merged": {
        ATTR_NAME: "Power return total",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/day-consumption/electricity1_cost": {
        ATTR_NAME: "Low tariff cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/day-consumption/electricity2_cost": {
        ATTR_NAME: "High tariff cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/day-consumption/electricity_cost_merged": {
        ATTR_NAME: "Power total cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/day-consumption/gas": {
        ATTR_NAME: "Gas usage",
        "enable_default": True,
        "icon": "mdi:counter",
        "unit": VOLUME_CUBIC_METERS,
    },
    "dsmr/day-consumption/gas_cost": {
        ATTR_NAME: "Gas cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/day-consumption/total_cost": {
        ATTR_NAME: "Total cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/day-consumption/energy_supplier_price_electricity_delivered_1": {
        ATTR_NAME: "Low tariff delivered price",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/day-consumption/energy_supplier_price_electricity_delivered_2": {
        ATTR_NAME: "High tariff delivered price",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/day-consumption/energy_supplier_price_electricity_returned_1": {
        ATTR_NAME: "Low tariff returned price",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/day-consumption/energy_supplier_price_electricity_returned_2": {
        ATTR_NAME: "High tariff returned price",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/day-consumption/energy_supplier_price_gas": {
        ATTR_NAME: "Gas price",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/meter-stats/dsmr_version": {
        ATTR_NAME: "DSMR version",
        "enable_default": True,
        "icon": "mdi:alert-circle",
        "transform": dsmr_transform,
    },
    "dsmr/meter-stats/electricity_tariff": {
        ATTR_NAME: "Electricity tariff",
        "enable_default": True,
        "icon": "mdi:flash",
        "transform": tariff_transform,
    },
    "dsmr/meter-stats/power_failure_count": {
        ATTR_NAME: "Power failure count",
        "enable_default": True,
        "icon": "mdi:flash",
    },
    "dsmr/meter-stats/long_power_failure_count": {
        ATTR_NAME: "Long power failure count",
        "enable_default": True,
        "icon": "mdi:flash",
    },
    "dsmr/meter-stats/voltage_sag_count_l1": {
        ATTR_NAME: "Voltage sag L1",
        "enable_default": True,
        "icon": "mdi:flash",
    },
    "dsmr/meter-stats/voltage_sag_count_l2": {
        ATTR_NAME: "Voltage sag L2",
        "enable_default": True,
        "icon": "mdi:flash",
    },
    "dsmr/meter-stats/voltage_sag_count_l3": {
        ATTR_NAME: "Voltage sag L3",
        "enable_default": True,
        "icon": "mdi:flash",
    },
    "dsmr/meter-stats/voltage_swell_count_l1": {
        ATTR_NAME: "Voltage swell L1",
        "enable_default": True,
        "icon": "mdi:flash",
    },
    "dsmr/meter-stats/voltage_swell_count_l2": {
        ATTR_NAME: "Voltage swell L2",
        "enable_default": True,
        "icon": "mdi:flash",
    },
    "dsmr/meter-stats/voltage_swell_count_l3": {
        ATTR_NAME: "Voltage swell L3",
        "enable_default": True,
        "icon": "mdi:flash",
    },
    "dsmr/meter-stats/rejected_telegrams": {
        ATTR_NAME: "Rejected telegrams",
        "enable_default": True,
        "icon": "mdi:flash",
    },
    "dsmr/current-month/electricity1": {
        ATTR_NAME: "Current month low tariff usage",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/current-month/electricity2": {
        ATTR_NAME: "Current month high tariff usage",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/current-month/electricity1_returned": {
        ATTR_NAME: "Current month low tariff returned",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/current-month/electricity2_returned": {
        ATTR_NAME: "Current month high tariff returned",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/current-month/electricity_merged": {
        ATTR_NAME: "Current month power usage total",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/current-month/electricity_returned_merged": {
        ATTR_NAME: "Current month power return total",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/current-month/electricity1_cost": {
        ATTR_NAME: "Current month low tariff cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/current-month/electricity2_cost": {
        ATTR_NAME: "Current month high tariff cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/current-month/electricity_cost_merged": {
        ATTR_NAME: "Current month power total cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/current-month/gas": {
        ATTR_NAME: "Current month gas usage",
        "enable_default": True,
        "icon": "mdi:counter",
        "unit": VOLUME_CUBIC_METERS,
    },
    "dsmr/current-month/gas_cost": {
        ATTR_NAME: "Current month gas cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/current-month/fixed_cost": {
        ATTR_NAME: "Current month fixed cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/current-month/total_cost": {
        ATTR_NAME: "Current month total cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/current-year/electricity1": {
        ATTR_NAME: "Current year low tariff usage",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/current-year/electricity2": {
        ATTR_NAME: "Current year high tariff usage",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/current-year/electricity1_returned": {
        ATTR_NAME: "Current year low tariff returned",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/current-year/electricity2_returned": {
        ATTR_NAME: "Current year high tariff usage",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/current-year/electricity_merged": {
        ATTR_NAME: "Current year power usage total",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/current-year/electricity_returned_merged": {
        ATTR_NAME: "Current year power returned total",
        "enable_default": True,
        "device_class": DEVICE_CLASS_ENERGY,
        "unit": ENERGY_KILO_WATT_HOUR,
    },
    "dsmr/current-year/electricity1_cost": {
        ATTR_NAME: "Current year low tariff cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/current-year/electricity2_cost": {
        ATTR_NAME: "Current year high tariff cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/current-year/electricity_cost_merged": {
        ATTR_NAME: "Current year power total cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/current-year/gas": {
        ATTR_NAME: "Current year gas usage",
        "enable_default": True,
        "icon": "mdi:counter",
        "unit": VOLUME_CUBIC_METERS,
    },
    "dsmr/current-year/gas_cost": {
        ATTR_NAME: "Current year gas cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/current-year/fixed_cost": {
        ATTR_NAME: "Current year fixed cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
    "dsmr/current-year/total_cost": {
        ATTR_NAME: "Current year total cost",
        "enable_default": True,
        "icon": "mdi:currency-eur",
        "unit": CURRENCY_EURO,
    },
}
