# Security Policy

## Local Network Model

This integration communicates directly with a **Displio V1.0** running the open-source [displio-rebirth](https://github.com/Ldo-fr/displio-rebirth) firmware over plain HTTP on your local network (due to STM32F103xB + TI CC3000 hardware constraints).

- Keep your Displio on a trusted LAN or isolated IoT VLAN.
- Never expose your Displio's HTTP port to the public internet.

## Reporting a Vulnerability

Please report security issues privately via the **Security → Advisories** tab of this repository.
