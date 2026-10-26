# Diesel Heater Controller for Home Assistant

A custom integration with a UI setup flow, plus a bundled Lovelace card, for the ESP32-S3 diesel heater controller.

## Install with HACS (recommended)

1. In Home Assistant open **HACS**, then the three-dot menu (top right) > **Custom repositories**.
2. Add `https://github.com/horizon10t/diesel-heater-ha` with category **Integration** and click **Add**.
3. Search for **Diesel Heater Controller** in HACS, open it and click **Download**.
4. **Restart Home Assistant.**
5. Go to **Settings > Devices & services > Add integration > "Diesel Heater Controller"**.
6. Enter the heater's **host / IP**, and a **WebUI username and password** (the user needs the *Settings* permission). If the account has MFA, you will be asked for the code.

The password is used once to fetch the controller's API key and is **not stored**. Home Assistant keeps only the host and key, so later logins, password changes or MFA do not break it. If you regenerate the key in the WebUI (Settings > System > Home Assistant), re-add the integration.

Updates appear in HACS when a new GitHub release is published.

### Manual install

Copy `custom_components/diesel_heater` into `/config/custom_components/`, restart Home Assistant, then continue from step 5 above.

## Entities (one "Diesel Heater" device)

**Control**

| Entity | Notes |
|---|---|
| `sensor.diesel_heater_status` | Off / Preheating / Igniting / Running / Cooling / Priming / Fault (fault text in attributes) |
| `select.diesel_heater_operating_mode` | Thermostat / Power |
| `number.diesel_heater_power_level` | 1-10 |
| `number.diesel_heater_target_temperature` | 5-35 °C |
| `switch.diesel_heater_power` | start / stop |

**Measurements**

| Entity | Notes |
|---|---|
| `sensor.diesel_heater_core_temperature`, `..._cabin_temperature` | °C |
| `sensor.diesel_heater_voltage`, `..._current` | V, A |
| `sensor.diesel_heater_glow_plug_output`, `..._fan_output` | % |
| `sensor.diesel_heater_fuel_pump_rate` | Hz |
| `binary_sensor.diesel_heater_glow_plug`, `..._fan`, `..._fuel_pump` | on / off output states |
| `binary_sensor.diesel_heater_fault` | problem when in Fault (message in attributes) |
| `binary_sensor.diesel_heater_schedule_active` | on while inside an enabled schedule window |

**Runtime**

| Entity | Notes |
|---|---|
| `sensor.diesel_heater_last_run_duration` | most recent run; recent runs listed in the `recent_runs_seconds` attribute |
| `sensor.diesel_heater_average_runtime` | average of completed runs |
| `sensor.diesel_heater_total_runtime` | total heater runtime (usable in the Energy-style statistics) |

**Diagnostic**

| Entity | Notes |
|---|---|
| `sensor.diesel_heater_ip_address` | station IP |
| `sensor.diesel_heater_active_wi_fi_network` | connected SSID |
| `sensor.diesel_heater_station_status` | Connected / Disconnected / ... |
| `sensor.diesel_heater_access_point_status` | Enabled / Disabled |
| `binary_sensor.diesel_heater_wi_fi_connected` | |
| `sensor.diesel_heater_installed_version` | firmware version (also shown on the device page) |

## Lovelace card

The integration serves and loads the card automatically; no resource needed. Add it to a dashboard (clear your browser cache once if it doesn't show):

```yaml
type: custom:diesel-heater-card
name: Diesel Heater
```

Entity ids can be overridden with `status`, `core_temp`, `cabin_temp`, `voltage`, `current`, `mode`, `power_level`, `target` and `power` if yours differ.

## Controller API (used by the integration)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/ha/status` | GET | Status JSON |
| `/api/ha/mode` | POST | `mode=thermostat\|power`, `level=1..10`, `target=<whole °C>` |
| `/api/ha/power` | POST | `on=true\|false` |
| `/api/ha/key` | GET/POST | Read / regenerate the key (WebUI session with Settings permission) |

Send the key in the `X-API-Key` header. Anyone on your network with the key can start and stop the heater, so regenerate it if it leaks.

The new network, schedule and version entities need controller firmware that reports them; flash the latest firmware first.
