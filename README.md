# Diesel Heater Controller for Home Assistant

A custom integration with a UI setup flow for the [ESP32-S3 Diesel Heater Controller](https://deanfourie.me/product/diesel-heater-controller/). The dashboard card is a separate repo: **[diesel-heater-lovelace](https://github.com/horizon10t/diesel-heater-lovelace)**.

## Screenshot

<!-- Replace images/screenshot.png in the repo with your screenshot. -->

![Diesel Heater Controller](https://raw.githubusercontent.com/horizon10t/diesel-heater-ha/main/images/screenshot.png)

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
| `sensor.diesel_heater_status` | Off / Preheating / Igniting / Running / Cooling / Priming / Fault |
| `sensor.diesel_heater_fault_message` | The current error in full, or `None`. The full text is also in the `message` attribute |
| `select.diesel_heater_operating_mode` | Thermostat / Power |
| `number.diesel_heater_power_level` | 1-10 |
| `number.diesel_heater_target_temperature` | 5-35 °C |
| `number.diesel_heater_fan_speed` | Fan speed for the current power level (Power mode only, not saved) |
| `number.diesel_heater_fuel_pump_rate` | Fuel pump rate in Hz for the current power level (Power mode only, not saved) |
| `switch.diesel_heater_power` | start / stop |
| `button.diesel_heater_emergency_stop` | emergency stop (immediate shutdown, then cooldown) |
| `button.diesel_heater_clear_fault` | clear a fault, same as Clear in the web interface (waits for the fault cooldown) |

**Measurements**

| Entity | Notes |
|---|---|
| `sensor.diesel_heater_core_temperature`, `..._cabin_temperature` | °C |
| `sensor.diesel_heater_voltage`, `..._current` | V, A |
| `sensor.diesel_heater_glow_plug_output`, `..._fan_output` | % |
| `sensor.diesel_heater_fuel_pump_rate` | Hz |
| `binary_sensor.diesel_heater_glow_plug`, `..._fan`, `..._fuel_pump` | on / off output states |
| `binary_sensor.diesel_heater_fault` | problem during a fault or after an emergency stop (message in attributes) |
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

## Dashboard card

The card is installed separately through HACS from [horizon10t/diesel-heater-lovelace](https://github.com/horizon10t/diesel-heater-lovelace) (category **Dashboard**). It finds all the entities above automatically from the heater you pick.

> **Upgrading from 1.2.x:** the integration no longer serves the card. If you added `/diesel_heater/diesel-heater-card.js` as a dashboard resource (or an earlier version added it for you), delete that entry under **Settings > Dashboards > Resources**, then install the card repo.

## Controller API (used by the integration)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/ha/status` | GET | Status JSON |
| `/api/ha/mode` | POST | `mode=thermostat\|power`, `level=1..10`, `target=<whole °C>` |
| `/api/ha/tune` | POST | `fan=<%>` and/or `pumpHz=<Hz>` (Power mode only, not saved) |
| `/api/ha/power` | POST | `on=true\|false` |
| `/api/ha/estop` | POST | Emergency stop |
| `/api/ha/fault/clear` | POST | Clear a fault (same as the web interface Clear button) |
| `/api/ha/key` | GET/POST | Read / regenerate the key (WebUI session with Settings permission) |

Send the key in the `X-API-Key` header. Anyone on your network with the key can start and stop the heater, so regenerate it if it leaks.

The network, schedule, version and emergency-stop entities need controller firmware that supports them; flash the latest firmware first.

**Languages:** the config flow and all entity names are translated into German, French, Spanish, Italian, Portuguese, Dutch, Polish, Russian, Swedish, Czech, Turkish, Japanese and Chinese (Simplified), following your Home Assistant language. Entities that already exist keep their entity ids; new installs in another language get ids in that language, which the Lovelace card handles automatically.

## The controller

This works with the [Diesel Heater Controller](https://deanfourie.me/product/diesel-heater-controller/) from [deanfourie.me](https://deanfourie.me). See the product page for details, hardware and firmware.
