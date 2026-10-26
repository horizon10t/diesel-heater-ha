# Home Assistant integration

A custom integration with a UI setup flow, plus a bundled Lovelace card.

## Install

1. Copy the `custom_components/diesel_heater` folder into `/config/custom_components/` on Home Assistant.
2. Restart Home Assistant.
3. **Settings > Devices & services > Add integration > "Diesel Heater Controller"**.
4. Enter the heater's **host / IP**, and a **WebUI username and password** (the user needs the *Settings* permission). If the account has MFA, you will be asked for the code.

The password is used once to fetch the controller's API key and is **not stored**. Home Assistant keeps only the host and key, so later logins, password changes or MFA do not break it. If you regenerate the key in the WebUI (Settings > System > Home Assistant), re-add the integration.

## Entities (one "Diesel Heater" device)

| Entity | Type |
|---|---|
| `sensor.diesel_heater_status` | Off / Preheating / Igniting / Running / Cooling / Priming / Fault (fault text in attributes) |
| `sensor.diesel_heater_core_temperature` | °C |
| `sensor.diesel_heater_cabin_temperature` | °C |
| `sensor.diesel_heater_voltage` | V |
| `sensor.diesel_heater_current` | A |
| `select.diesel_heater_operating_mode` | Thermostat / Power |
| `number.diesel_heater_power_level` | 1-10 |
| `number.diesel_heater_target_temperature` | 5-35 °C |
| `switch.diesel_heater_power` | start / stop |

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

## Install with HACS

1. HACS > three-dot menu > **Custom repositories** > add `https://github.com/YOUR_GITHUB_USER/ha-diesel-heater` as type **Integration**.
2. Search for "Diesel Heater Controller", download it, and restart Home Assistant.
3. Add the integration as described above.

Updates: publish a GitHub release (tag like `v1.0.1`, matching `version` in `manifest.json`) and HACS will offer it.
