# Displio Rebirth for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)

Official companion Home Assistant integration (HACS) for the **Displio V1.0** E-Ink desk display running the open-source [displio-rebirth](https://github.com/Ldo-fr/displio-rebirth) firmware.

> [!NOTE]
> This is an independent, **non-profit**, volunteer-driven open-source project created so that a great piece of hardware doesn't end up forgotten at the bottom of a drawer or in the trash. It is **not affiliated with, endorsed by, or associated with** Displio or Draugiem Group in any way.

---

## Features

- **100% Local Polling** over your LAN — zero cloud dependency.
- **Onboard Sensors**:
  - Ambient **Temperature** (`Si7021`, °C)
  - Relative **Humidity** (`Si7021`, %)
  - **Orientation** (`MMA8452Q`: portrait up/down, landscape left/right)
  - **Battery ADC** voltage (`mV`, diagnostic) & **Uptime** (`s`, diagnostic)
  - **USB Power** & **Front Button** binary sensors
  - **Beep** test button entity directly in the Home Assistant UI
- **Actions / Services** for Automations & Scripts:
  - `displio_rebirth.display_text` — render a clean 264×176 E-Ink card (title, body, footer, optional invert, full refresh, and notification beep)
  - `displio_rebirth.display_image` — convert any local image or HTTP(S) image URL to 264×176 1-bpp monochrome (with Floyd-Steinberg dithering) and push it to the screen
  - `displio_rebirth.beep` — sound the piezo buzzer with custom frequency and duration

---

## Prerequisites

1. A **Displio V1.0** flashed with the [displio-rebirth](https://github.com/Ldo-fr/displio-rebirth) firmware (`v1.0.0` or newer) and connected to your 2.4 GHz Wi-Fi network.
2. *(Recommended)* Assign a static DHCP lease on your router so your Displio keeps the same local IP address.

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
