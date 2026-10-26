/* Diesel Heater card for Home Assistant (no dependencies)
 *
 * Added from the UI card picker ("Diesel Heater"); the visual editor selects the heater.
 * YAML:
 *   type: custom:diesel-heater-card
 *   device: <device id>           # optional, first heater is used if omitted
 *   name: Diesel Heater           # optional
 *   # Optional entity overrides: status, core_temp, cabin_temp, voltage, current,
 *   # mode, power_level, target, power
 */
const STATE_STYLE = {
  Off:        { color: "var(--secondary-text-color)", icon: "mdi:power-off" },
  Preheating: { color: "#f5a623", icon: "mdi:heat-wave" },
  Igniting:   { color: "#ff7a1a", icon: "mdi:fire-alert" },
  Running:    { color: "#e8590c", icon: "mdi:fire" },
  Cooling:    { color: "#2d9cdb", icon: "mdi:snowflake" },
  Priming:    { color: "#f5a623", icon: "mdi:gas-station" },
  Fault:      { color: "var(--error-color, #d32f2f)", icon: "mdi:alert-octagon" },
};

// [domain, entity id suffix] used to find each entity on the selected heater.
const ENTITY_SPEC = {
  status: ["sensor", "_status"],
  core_temp: ["sensor", "_core_temperature"],
  cabin_temp: ["sensor", "_cabin_temperature"],
  voltage: ["sensor", "_voltage"],
  current: ["sensor", "_current"],
  mode: ["select", ""],
  power_level: ["number", "_power_level"],
  target: ["number", "_target_temperature"],
  power: ["switch", ""],
};
const DEFAULT_ENTITIES = {
  status: "sensor.diesel_heater_status",
  core_temp: "sensor.diesel_heater_core_temperature",
  cabin_temp: "sensor.diesel_heater_cabin_temperature",
  voltage: "sensor.diesel_heater_voltage",
  current: "sensor.diesel_heater_current",
  mode: "select.diesel_heater_operating_mode",
  power_level: "number.diesel_heater_power_level",
  target: "number.diesel_heater_target_temperature",
  power: "switch.diesel_heater_power",
};

function firstHeaterDevice(hass) {
  const e = Object.values(hass.entities || {}).find((x) => x.platform === "diesel_heater" && x.device_id);
  return e ? e.device_id : undefined;
}

class DieselHeaterCard extends HTMLElement {
  setConfig(config) {
    this._config = { ...config };
    this._ids = this._entities();
    if (!this.shadowRoot) this._build();
  }

  getCardSize() { return 4; }

  static getConfigElement() { return document.createElement("diesel-heater-card-editor"); }

  // A new card picks the first heater automatically.
  static getStubConfig(hass) {
    const device = hass ? firstHeaterDevice(hass) : undefined;
    return device ? { device } : {};
  }

  _deviceName() {
    const d = this._hass && this._config.device && this._hass.devices
      ? this._hass.devices[this._config.device] : null;
    return d ? (d.name_by_user || d.name) : "";
  }

  // Entity ids: explicit override > entities of the selected heater > default ids.
  _entities() {
    const found = {};
    const hass = this._hass, cfg = this._config || {};
    const deviceId = cfg.device || (hass ? firstHeaterDevice(hass) : undefined);
    if (hass && deviceId && hass.entities) {
      const mine = Object.values(hass.entities).filter(
        (e) => e.device_id === deviceId && !e.entity_category);
      for (const [key, [domain, suffix]] of Object.entries(ENTITY_SPEC)) {
        const match = mine.find((e) => e.entity_id.startsWith(domain + ".") && e.entity_id.endsWith(suffix));
        if (match) found[key] = match.entity_id;
      }
    }
    const out = {};
    for (const key of Object.keys(ENTITY_SPEC)) {
      out[key] = cfg[key] || found[key] || DEFAULT_ENTITIES[key];
    }
    return out;
  }

  set hass(hass) {
    this._hass = hass;
    if (this._root) this._update();
  }

  _build() {
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <style>
        [hidden] { display:none !important; }
        ha-card { padding: 16px; overflow: hidden; }
        .head { display:flex; align-items:center; justify-content:space-between; gap:12px; }
        .title { font-size:1.1rem; font-weight:500; }
        .status { display:flex; align-items:center; gap:8px; font-weight:600; }
        .status ha-icon { --mdc-icon-size:26px; }
        .tiles { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin:16px 0; }
        .tile { background:var(--secondary-background-color); border-radius:12px; padding:12px 8px; text-align:center; }
        .tile .v { font-size:1.45rem; font-weight:600; line-height:1.2; }
        .tile .u { font-size:.8rem; font-weight:400; color:var(--secondary-text-color); margin-left:2px; }
        .tile .l { font-size:.75rem; color:var(--secondary-text-color); margin-top:2px; }
        .tile.core .v { color: var(--accent, inherit); }
        .seg { display:grid; grid-template-columns:1fr 1fr; background:var(--secondary-background-color); border-radius:12px; padding:4px; gap:4px; }
        .seg button { border:0; border-radius:9px; padding:10px; cursor:pointer; font:inherit; font-weight:500;
          background:transparent; color:var(--primary-text-color); }
        .seg button.on { background:var(--primary-color); color:var(--text-primary-color, #fff); }
        .seg button:disabled { opacity:.5; cursor:default; }
        .row { display:flex; align-items:center; gap:10px; margin-top:14px; }
        .row .lbl { min-width:74px; font-size:.85rem; color:var(--secondary-text-color); }
        .row input[type=range] { flex:1; accent-color:var(--primary-color); }
        .row .val { min-width:44px; text-align:right; font-weight:600; }
        .actions { display:flex; gap:10px; margin-top:16px; }
        .actions button { flex:1; border:0; border-radius:12px; padding:12px; cursor:pointer; font:inherit; font-weight:600; }
        .start { background:var(--primary-color); color:var(--text-primary-color,#fff); }
        .stop { background:var(--error-color,#d32f2f); color:#fff; }
        .fault { margin-top:12px; padding:8px 12px; border-radius:10px; background:var(--error-color,#d32f2f); color:#fff; font-size:.85rem; }
        .unavail { opacity:.5; }
      </style>
      <ha-card>
        <div class="head">
          <div class="title"></div>
          <div class="status"><ha-icon></ha-icon><span></span></div>
        </div>
        <div class="tiles">
          <div class="tile core"><div><span class="v" id="core">--</span><span class="u">°C</span></div><div class="l">Core temp</div></div>
          <div class="tile"><div><span class="v" id="volt">--</span><span class="u">V</span></div><div class="l">Voltage</div></div>
          <div class="tile"><div><span class="v" id="amp">--</span><span class="u">A</span></div><div class="l">Current</div></div>
        </div>
        <div class="seg">
          <button data-mode="Thermostat">Thermostat</button>
          <button data-mode="Power">Power</button>
        </div>
        <div class="row" id="thermoRow">
          <span class="lbl">Target</span>
          <input type="range" id="targetSlider" min="5" max="35" step="1">
          <span class="val" id="targetVal"></span>
        </div>
        <div class="row" id="powerRow">
          <span class="lbl">Power level</span>
          <input type="range" id="levelSlider" min="1" max="10" step="1">
          <span class="val" id="levelVal"></span>
        </div>
        <div class="actions"><button id="toggle"></button></div>
        <div class="fault" id="fault" hidden></div>
      </ha-card>`;
    this._root = this.shadowRoot;
    const $ = (s) => this._root.querySelector(s);

    this._root.querySelectorAll(".seg button").forEach((b) =>
      b.addEventListener("click", () =>
        this._hass.callService("select", "select_option", {
          entity_id: this._ids.mode, option: b.dataset.mode })));

    // Sliders update the label while dragging and call the service on release.
    const bindSlider = (id, valId, entity, suffix) => {
      const el = $(id);
      el.addEventListener("input", () => { this._dragging = id; $(valId).textContent = el.value + suffix; });
      el.addEventListener("change", () => {
        this._dragging = null;
        this._hass.callService("number", "set_value", { entity_id: entity(), value: Number(el.value) });
      });
    };
    bindSlider("#targetSlider", "#targetVal", () => this._ids.target, "°C");
    bindSlider("#levelSlider", "#levelVal", () => this._ids.power_level, "");

    $("#toggle").addEventListener("click", () => {
      const on = $("#toggle").dataset.on === "1";
      this._hass.callService("switch", on ? "turn_off" : "turn_on", { entity_id: this._ids.power });
    });
    this._update();
  }

  _num(entityId, digits) {
    const s = this._hass.states[entityId];
    if (!s || isNaN(parseFloat(s.state))) return null;
    return digits === undefined ? parseFloat(s.state) : parseFloat(s.state).toFixed(digits);
  }

  _update() {
    if (!this._hass || !this._config) return;
    const h = this._hass, $ = (s) => this._root.querySelector(s);
    const c = this._ids = this._entities();
    c.name = this._config.name || this._deviceName() || "Diesel Heater";
    const st = h.states[c.status];
    const state = st ? st.state : "unavailable";
    const style = STATE_STYLE[state] || { color: "var(--secondary-text-color)", icon: "mdi:help-circle" };

    $(".title").textContent = c.name;
    const statusEl = $(".status");
    statusEl.style.color = style.color;
    statusEl.querySelector("ha-icon").setAttribute("icon", style.icon);
    statusEl.querySelector("span").textContent = state === "unavailable" ? "Offline" : state;
    $(".tiles").classList.toggle("unavail", !st || state === "unavailable");

    const core = this._num(c.core_temp, 1);
    $("#core").textContent = core ?? "--";
    $(".tile.core").style.setProperty("--accent", state === "Running" || state === "Igniting" ? style.color : "inherit");
    $("#volt").textContent = this._num(c.voltage, 1) ?? "--";
    $("#amp").textContent = this._num(c.current, 1) ?? "--";

    const modeState = h.states[c.mode] ? h.states[c.mode].state : "";
    this._root.querySelectorAll(".seg button").forEach((b) => {
      b.classList.toggle("on", b.dataset.mode === modeState);
      b.disabled = !h.states[c.mode];
    });
    $("#thermoRow").hidden = modeState !== "Thermostat";
    $("#powerRow").hidden = modeState !== "Power";

    if (this._dragging !== "#targetSlider") {
      const t = this._num(c.target);
      if (t !== null) { $("#targetSlider").value = t; $("#targetVal").textContent = t + "°C"; }
    }
    if (this._dragging !== "#levelSlider") {
      const l = this._num(c.power_level);
      if (l !== null) { $("#levelSlider").value = l; $("#levelVal").textContent = l; }
    }

    const sw = h.states[c.power];
    const isOn = sw && sw.state === "on";
    const btn = $("#toggle");
    btn.dataset.on = isOn ? "1" : "0";
    btn.textContent = isOn ? "Stop heater" : "Start heater";
    btn.className = isOn ? "stop" : "start";
    btn.disabled = !sw || state === "Cooling" && !isOn;

    const fault = $("#fault");
    const msg = st && st.attributes ? st.attributes.fault : "";
    fault.hidden = !(state === "Fault" && msg);
    fault.textContent = msg || "";
  }
}

// Visual editor: pick the heater; entity overrides are optional.
class DieselHeaterCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._form) this._form.hass = hass;
    else this._render();
  }

  _schema() {
    const entity = (name, domain) => ({ name, selector: { entity: { domain } } });
    return [
      { name: "device", selector: { device: { integration: "diesel_heater" } } },
      { name: "name", selector: { text: {} } },
      {
        type: "expandable",
        name: "",
        title: "Entity overrides (optional)",
        schema: [
          entity("status", "sensor"), entity("core_temp", "sensor"),
          entity("cabin_temp", "sensor"), entity("voltage", "sensor"),
          entity("current", "sensor"), entity("mode", "select"),
          entity("power_level", "number"), entity("target", "number"),
          entity("power", "switch"),
        ],
      },
    ];
  }

  _render() {
    if (!this._config || !this._hass) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (s) => ({
        device: "Heater", name: "Name (optional)",
        status: "Status sensor", core_temp: "Core temperature sensor",
        cabin_temp: "Cabin temperature sensor", voltage: "Voltage sensor",
        current: "Current sensor", mode: "Operating mode select",
        power_level: "Power level number", target: "Target temperature number",
        power: "Power switch",
      }[s.name] || s.name);
      this._form.computeHelper = (s) =>
        s.name === "device" ? "Entities are found automatically from the selected heater." : "";
      this._form.addEventListener("value-changed", (ev) => {
        const value = {};
        for (const [k, v] of Object.entries(ev.detail.value)) {
          if (v !== "" && v !== undefined && v !== null) value[k] = v;
        }
        this._config = { type: this._config.type, ...value };
        this.dispatchEvent(new CustomEvent("config-changed", {
          detail: { config: this._config }, bubbles: true, composed: true,
        }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.schema = this._schema();
    this._form.data = this._config;
  }
}

if (!customElements.get("diesel-heater-card")) {
  customElements.define("diesel-heater-card", DieselHeaterCard);
  customElements.define("diesel-heater-card-editor", DieselHeaterCardEditor);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "diesel-heater-card",
    name: "Diesel Heater",
    preview: true,
    description: "Status, core temperature, volts/amps and mode control for the ESP32 diesel heater controller.",
    documentationURL: "https://github.com/horizon10t/diesel-heater-ha",
  });
}
