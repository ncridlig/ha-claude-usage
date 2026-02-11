# Claude Usage for Home Assistant

Track your [Claude.ai](https://claude.ai) usage limits directly in Home Assistant. Monitor session and weekly utilization percentages, and know exactly when your limits reset.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three-dot menu in the top right corner and select **Custom repositories**
3. Paste this repository URL and select **Integration** as the category
4. Click **Add**
5. Search for **Claude Usage** in HACS and click **Download**
6. Restart Home Assistant

### Manual

1. Download the `custom_components/claude_usage/` folder from this repository
2. Copy it into your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Setup

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **Claude Usage**
3. Paste your Claude.ai session key

### Finding your session key (Chrome)

1. Go to [claude.ai](https://claude.ai) and make sure you're logged in
2. Press **F12** (Windows/Linux) or **Cmd+Option+I** (Mac) to open Developer Tools
3. Click the **Application** tab in the top toolbar
4. In the left sidebar, expand **Cookies** and click **https://claude.ai**
5. The cookie list is sorted alphabetically — scroll down to find **`sessionKey`** (it will be near the bottom, in the "s" section)
6. Click on the `sessionKey` row and copy the value shown at the bottom of the panel

> **Important:** Do not confuse `sessionKey` with other cookies like `activitySessionId` or `__ssid`. You need the one named exactly `sessionKey`.

## Sensors

Once configured, four sensors appear under a single **Claude Usage** device:

| Sensor | Type | Description |
|--------|------|-------------|
| Session Usage | `%` | Current 5-hour utilization |
| Weekly Usage | `%` | Current 7-day utilization |
| Session Reset | Timestamp | When the 5-hour window resets |
| Weekly Reset | Timestamp | When the 7-day window resets |

All sensors poll every 5 minutes.

## Session key expiration

The Claude.ai session key expires periodically. When this happens:

- Sensors will show as **Unavailable**
- Home Assistant will display a **Re-authentication required** notification
- Click the notification, paste a fresh session key, and sensors will resume

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Sensors show "Unavailable" | Session key likely expired. Check for a re-authentication notification, or reconfigure the integration with a new key. |
| "Cannot connect" during setup | Verify your Home Assistant instance can reach `claude.ai`. |
| Integration not found after install | Make sure you restarted Home Assistant after installing via HACS. |
