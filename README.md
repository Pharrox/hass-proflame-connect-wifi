# Integration Blueprint

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

_Integration to integrate with [integration_blueprint][integration_blueprint]._

**This integration will set up the following platforms.**

Platform | Description
-- | --
`binary_sensor` | Show something `True` or `False`.
`sensor` | Show info from blueprint API.
`switch` | Switch something `True` or `False`.

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `proflame_connect_wifi`.
1. Download _all_ the files from the `custom_components/proflame_connect_wifi/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Proflame"

## Configuration is done in the UI

You will need the IP address of your Proflame Connect device.  In addition, you will need it's Unique ID (e.g. the `FCC ID` on the remote).

## Lovelace Card

Once configured, you can add a card to Lovelace that looks like this:

<img width="356" alt="image" src="https://github.com/mirmirou/hass-proflame-connect-wifi/assets/109924196/f236ce65-a333-4825-9627-0ac38de6ceca">

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[proflame_connect_wifi]: https://github.com/Pharrox/hass-proflame-connect-wifi
[buymecoffee]: https://www.buymeacoffee.com/pharrox
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/Pharrox/hass-proflame-connect-wifi.svg?style=for-the-badge
[commits]: https://github.com/Pharrox/hass-proflame-connect-wifi/commits/master
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/Pharrox/hass-proflame-connect-wifi.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Kevin%20Lucas%20%40Pharrox-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/Pharrox/hass-proflame-connect-wifi.svg?style=for-the-badge
[releases]: https://github.com/Pharrox/hass-proflame-connect-wifi/releases
