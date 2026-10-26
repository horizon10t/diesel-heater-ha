/* Diesel Heater card for Home Assistant (no dependencies)
 *
 * Resource:  /local/diesel-heater-card.js  (type: JavaScript module)
 * Card YAML:
 *   type: custom:diesel-heater-card
 *   name: Diesel Heater            # optional
 *   # Optional overrides (defaults shown):
 *   status: sensor.diesel_heater_status
 *   core_temp: sensor.diesel_heater_core_temperature
 *   cabin_temp: sensor.diesel_heater_cabin_temperature
 *   voltage: sensor.diesel_heater_voltage
 *   current: sensor.diesel_heater_current
 *   mode: select.diesel_heater_operating_mode
 *   power_level: number.diesel_heater_power_level
 *   target: number.diesel_heater_target_temperature
 *   power: switch.diesel_heater_power
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

class DieselHeaterCard extends HTMLElement {
  setConfig(config) {
    this._config = {
      name: "Diesel Heater",
      status: "sensor.diesel_heater_status",
      core_temp: "sensor.diesel_heater_core_temperature",
      cabin_temp: "sensor.diesel_heater_cabin_temperature",
      voltage: "sensor.diesel_heater_voltage",
      current: "sensor.diesel_heater_current",
      mode: "select.diesel_heater_operating_mode",
      power_level: "number.diesel_heater_power_level",
      target: "number.diesel_heater_target_temperature",
      power: "switch.diesel_heater_power",
      ...config,
    };
    if (!this.shadowRoot) this._build();
  }

  getCardSize() { return 4; }

  static getStubConfig() { return {}; }

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
          entity_id: this._config.mode, option: b.dataset.mode })));

    // Sliders update the label while dragging and call the service on release.
    const bindSlider = (id, valId, entity, suffix) => {
      const el = $(id);
      el.addEventListener("input", () => { this._dragging = id; $(valId).textContent = el.value + suffix; });
      el.addEventListener("change", () => {
        this._dragging = null;
        this._hass.callService("number", "set_value", { entity_id: entity(), value: Number(el.value) });
      });
    };
    bindSlider("#targetSlider", "#targetVal", () => this._config.target, "°C");
    bindSlider("#levelSlider", "#levelVal", () => this._config.power_level, "");

    $("#toggle").addEventListener("click", () => {
      const on = $("#toggle").dataset.on === "1";
      this._hass.callService("switch", on ? "turn_off" : "turn_on", { entity_id: this._config.power });
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
    const c = this._config, h = this._hass, $ = (s) => this._root.querySelector(s);
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

customElements.define("diesel-heater-card", DieselHeaterCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "diesel-heater-card",
  name: "Diesel Heater",
  description: "Status, core temperature, volts/amps and mode control for the ESP32 diesel heater controller.",
});
