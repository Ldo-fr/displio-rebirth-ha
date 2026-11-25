# Displio Rebirth for Home Assistant

[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom%20Repository-orange.svg)](https://hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.6%2B-blue.svg)](https://www.home-assistant.io/)
[![Version](https://img.shields.io/github/v/release/Ldo-fr/displio-rebirth-ha?include_prereleases&color=yellow&label=version)](https://github.com/Ldo-fr/displio-rebirth-ha/releases)
[![CI](https://github.com/Ldo-fr/displio-rebirth-ha/actions/workflows/ci.yml/badge.svg)](https://github.com/Ldo-fr/displio-rebirth-ha/actions/workflows/ci.yml)
[![Firmware](https://img.shields.io/badge/firmware-displio--rebirth-teal.svg)](https://github.com/Ldo-fr/displio-rebirth)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Official companion **Home Assistant** integration (HACS) for the **Displio V1.0** Wi-Fi 2.7" E-Ink desk display (Draugiem Group, 2015) — 100% local, zero cloud required.

---

> [!IMPORTANT]
> ### Hardware Prerequisite — Custom Firmware Required
> **This integration does NOT work with the stock factory Displio firmware.**
>
> Before installing this integration, your Displio V1.0 **must already be flashed** with the open-source **[displio-rebirth](https://github.com/Ldo-fr/displio-rebirth)** custom firmware (`v1.0.0+`) and connected to your 2.4 GHz Wi-Fi network.
>
> - Flashing is done **100% over USB** (no soldering, no disassembly, no ST-Link, unbrickable).
> - Follow the step-by-step guide here: **[displio-rebirth Quick Start](https://github.com/Ldo-fr/displio-rebirth#quick-start-step-by-step)**.
> - *(Recommended)* Assign a static DHCP lease on your router so your Displio keeps the same local IP address.

> [!NOTE]
> ### Independent, Non-Profit & Volunteer-Driven Project
> This is an independent, **non-profit**, volunteer-driven open-source project created so that a great piece of hardware doesn't end up forgotten at the bottom of a drawer or in the trash. It is **not affiliated with, endorsed by, or associated with** Displio or Draugiem Group in any way.

---

## Features

| Feature | Status | Description |
| :--- | :---: | :--- |
| **Local Graphical Setup (Config Flow)** | ✅ Operational | Add your Displio by IP/port in the Home Assistant UI; automatic validation via `GET /status` and MAC-based `unique_id`. |
| **Onboard Environment & Motion Sensors** | ✅ Operational | Ambient temperature (`Si7021`), relative humidity (`Si7021`), 4-way orientation (`MMA8452Q`), battery ADC, `VDDA`, and uptime. |
| **Binary Sensors & Buzzer Button** | ✅ Operational | USB power detection, front button state, and a one-click **Beep** button entity directly on the device page. |
| **E-Ink Text & Image Rendering** | ✅ Operational | Non-blocking Pillow 264×176 1-bpp renderer with Floyd-Steinberg dithering, full/fast refresh, and optional inverted colors. |
| **Custom Piezo Alerts** | ✅ Operational | Configurable frequency (`100`–`10000` Hz) and duration (`1`–`2000` ms) via Home Assistant actions. |

---

## Installation (HACS)

1. Open **HACS** in Home Assistant.
2. Click the **⋮** menu (top right) → **Custom repositories**.
3. Add repository URL: `https://github.com/Ldo-fr/displio-rebirth-ha` with category **Integration**.
4. Search for **Displio Rebirth** in HACS and click **Download**.
5. Restart Home Assistant.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Displio Rebirth**.
3. Enter your Displio's local **IP address** (e.g. `192.168.1.42`) and **HTTP port** (default `80`).
4. *(Optional)* Click **Configure** on the integration entry to adjust the polling interval (default: `30` seconds).

---

## Entities

| Platform | Entity | Source / Details |
| :--- | :--- | :--- |
| `sensor` | **Temperature** | `Si7021` ambient temperature (°C) |
| `sensor` | **Humidity** | `Si7021` relative humidity (%) |
| `sensor` | **Orientation** | `MMA8452Q` (`portrait_up`, `portrait_down`, `landscape_right`, `landscape_left`) |
| `sensor` | **Battery ADC** | Divided battery rail voltage (mV, diagnostic) |
| `sensor` | **Analog supply (VDDA)** | Internal `Vrefint` supply (mV, diagnostic, disabled by default) |
| `sensor` | **Uptime** | Device uptime since boot (seconds, diagnostic) |
| `binary_sensor` | **USB power** | USB VBUS plug state (`PA9`, diagnostic) |
| `binary_sensor` | **Button** | Front button state (`PA2`) |
| `button` | **Beep** | Triggers a short 2400 Hz / 80 ms piezo beep |

---

## Automation Examples

### Display a sensor card on the E-Ink screen

```yaml
action: displio_rebirth.display_text
data:
  title: "Living Room"
  body: "{{ states('sensor.displio_temperature') }} °C"
  footer: "Humidity {{ states('sensor.displio_humidity') }}%"
  full_refresh: false
  beep: false
```

### Send an alert with inverted colors + notification beep

```yaml
action: displio_rebirth.display_text
data:
  title: "ALERT"
  body: "Front door left open!"
  footer: "{{ now().strftime('%H:%M') }}"
  invert: true
  full_refresh: true
  beep: true
```

### Push an image (PNG/JPEG) to the E-Ink display

```yaml
action: displio_rebirth.display_image
data:
  path: "/config/www/displio_dashboard.png"
  full_refresh: true
  dither: true
```

### Trigger a custom beep

```yaml
action: displio_rebirth.beep
data:
  freq: 2600
  ms: 100
```

---

## License

Released under the [MIT License](LICENSE).
