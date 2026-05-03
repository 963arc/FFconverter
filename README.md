# FFConverter

![FFConverter Logo](resources/images/LOGO_256.png)

A simple, portable video, audio, and image converter for Linux.

## - How to download ?

Download your desired version from [Releases](https://github.com/963arc/FFconverter/releases/tag/v1.0).

## Install (DEB) - Debian / Ubuntu

Install dependencies:

```bash
sudo apt install ffmpeg python3
```

Extract and install package:

```bash
sudo dpkg -i FFConverter_1.0-1_amd64.deb
```

Run: Type `FFConverter` in terminal, or launch from application menu.

---

## Install (RPM) - Fedora / RHEL

Install dependencies:

```bash
sudo dnf install ffmpeg python3
```

Extract and install package:

```bash
sudo dnf install FFConverter-1.0-1.x86_64.rpm
```

Run: Type `FFConverter` in terminal, or launch from application menu.

---

## Install (Arch Linux) - Manual

Install dependencies:

```bash
sudo pacman -S ffmpeg python
```

Extract and copy files:

```bash
tar -xf FFConverter-1.0-1-x86_64.tar.gz
cd FFConverter-1.0-1-x86_64
sudo cp -r usr /
```

Run: Type `FFConverter` in terminal, or launch from application menu.

---

## Install (AppImage)

```bash
chmod +x FFConverter.AppImage
./FFConverter.AppImage
```

---

## Install (Portable .tar.xz)

```bash
tar -xf FFConverter-portable.tar.xz
cd FFConverter
chmod +x run.sh
./run.sh
```

---

## Screenshots

### Dark Theme
![FFConverter Dark Theme](screenshot-ui-dark_converted.png)

### Light Theme
![FFConverter Light Theme](screenshot-ui-light_converted.png)

---

## Desktop Integration (Optional)

To add FFConverter to your application menu (for portable version):

```bash
# Copy desktop file
cp usr/share/applications/ffconverter.desktop ~/.local/share/applications/

# Copy icon
mkdir -p ~/.local/share/icons/hicolor/256x256/apps/
cp usr/share/icons/hicolor/256x256/ffconverter.png ~/.local/share/icons/hicolor/256x256/apps/
```

Log out and log back in, or restart your desktop environment for the menu to update.

---

## Requirements

- **Platform:** Linux only (not Windows or macOS)
- **Python 3.8 or higher**
- **FFmpeg is optional** - the app checks your system first, then uses the bundled version if not found

---

## Troubleshooting

### "Permission denied" when running
```bash
chmod +x run.sh
```

### "Python not found" error
Install Python 3:

- **Ubuntu/Debian**: `sudo apt install python3`
- **Fedora**: `sudo dnf install python3`
- **Arch Linux**: `sudo pacman -S python`

### App won't start (Portable version)
Make sure you're in the FFConverter folder and run:
```bash
./run.sh
```

### File too large warning when extracting
The archive is ~90MB compressed (~388MB uncompressed). Ensure you have enough disk space.

---

## What's Included (Portable .tar.xz)

| Component | Description |
|-----------|-------------|
| ffc.py | Main application |
| run.sh | Launcher script (hybrid: system FFmpeg → bundled) |
| usr/bin/ffmpeg | Bundled FFmpeg (fallback, 194MB) |
| usr/bin/ffprobe | Bundled FFprobe (fallback) |
| usr/share/applications/ffconverter.desktop | Desktop menu entry |
| usr/share/icons/.../ffconverter.png | App icon (256x256) |

The app automatically uses system FFmpeg if available, otherwise falls back to the bundled version.

---

## Uninstall

**Portable version:**
```bash
rm -rf FFConverter
```

**DEB/RPM:**
```bash
# Debian/Ubuntu
sudo apt remove ffconverter

# Fedora/RHEL
sudo dnf remove FFConverter
```

**Arch:**
```bash
sudo rm -rf /opt/FFConverter
sudo rm /usr/bin/FFConverter
```

To remove desktop integration:

```bash
rm ~/.local/share/applications/ffconverter.desktop
rm ~/.local/share/icons/hicolor/256x256/apps/ffconverter.png
```

---

## Support

For issues or questions, open an issue on the project GitHub page.

## Support the Project

If this project saved you time, consider sending a tip! 

| Asset | Network | Wallet Address |
| :--- | :--- | :--- |
| **Bitcoin** | BTC | `bc1q6ayz2jjzzvxauhj24vjjaj6ljsp86lna7ny9p6` |
| **Ethereum** | ETH / ERC-20 | `0x7958b8eC663f6062F1F5943aD87b2e8C8f945233` |
| **Solana** | SOL | `7XpptWv6db53GYiHXioUnr9phHV5tB7zo5z9wvLynFGC` |
| **Monero** | XMR | `8BL7SNroN7XGqxS8CmgBQyPB7UPSZ2uKtRSHmSk815GNh56oKFpmdWh2Ko2Pe4XsjM3oChNpkh5bxVzgSvvgaPBNGR7TJ4d` |
| **Litecoin** | LTC | `LdKdCyq7SEhELJa7kvH9Unu8dTnn3Dm9i8` |

> *Note: The Ethereum address supports ETH, USDT, USDC, Polygon, and BNB Chain.*

---

Enjoy converting your files!