# FFConverter

A simple, portable video, audio, and image converter for Linux.

## Download

Choose one:

- **FFConverter.AppImage** (~1MB) - Any Linux, needs system Python
- **FFConverter-portable.tar.xz** (~90MB) - Full portable, includes everything
- **FFConverter-1.0-1.x86_64.rpm** (~500KB) - Fedora/RHEL, needs system Python + FFmpeg

Download from the releases page and save to your preferred location (e.g., ~/Downloads)

## Install (RPM) - Fedora/RHEL

For Fedora, CentOS, RHEL, and derivatives:

```bash
sudo dnf install FFConverter-1.0-1.x86_64.rpm
```

That's it! Run with:

```bash
ffc.py
```

## Run (AppImage)

### Step 1: Make executable

```bash
chmod +x FFConverter.AppImage
```

### Step 2: Run

```bash
./FFConverter.AppImage
```

That's it! The app will open with a friendly interface.

## Screenshots

### Dark Theme
![FFConverter Dark Theme](screenshot-ui-dark_converted.png)

### Light Theme
![FFConverter Light Theme](screenshot-ui-light_converted.png)

## Install (Portable .tar.xz)

### Step 1: Extract the archive

```bash
tar -xf FFConverter-portable.tar.xz
```

### Step 2: Navigate to the folder

```bash
cd FFConverter
```

### Step 3: Make the launcher executable

```bash
chmod +x run.sh
```

### Step 4: Run the app

```bash
./run.sh
```

That's it! The app will open with a friendly interface.

## Desktop Integration (Optional)

To add FFConverter to your application menu:

```bash
# Copy desktop file
cp usr/share/applications/ffconverter.desktop ~/.local/share/applications/

# Copy icon
mkdir -p ~/.local/share/icons/hicolor/256x256/apps/
cp usr/share/icons/hicolor/256x256/ffconverter.png ~/.local/share/icons/hicolor/256x256/apps/
```

Log out and log back in, or restart your desktop environment for the menu to update.

## Requirements

- **Platform:** Linux only (not Windows or macOS)
- **Python 3.8 or higher**
- **FFmpeg is optional** - the app checks your system first, then uses the bundled version if not found

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


### App won't start
Make sure you're in the FFConverter folder and run:
```bash
./run.sh
```

### File too large warning when extracting
The archive is ~90MB compressed (~388MB uncompressed). Ensure you have enough disk space.

## What's Included

| Component | Description |
|-----------|-------------|
| ffc.py | Main application |
| run.sh | Launcher script (hybrid: system FFmpeg → bundled) |
| usr/bin/ffmpeg | Bundled FFmpeg (fallback, 194MB) |
| usr/bin/ffprobe | Bundled FFprobe (fallback) |
| usr/share/applications/ffconverter.desktop | Desktop menu entry |
| usr/share/icons/.../ffconverter.png | App icon (256x256) |

The app automatically uses system FFmpeg if available, otherwise falls back to the bundled version.

## Uninstall

Simply delete the FFConverter folder:

```bash
rm -rf FFConverter
```

To remove desktop integration:

```bash
rm ~/.local/share/applications/ffconverter.desktop
rm ~/.local/share/icons/hicolor/256x256/apps/ffconverter.png
```

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
| **FiatCard/Paypal** | Ko-Fi | `ko-fi.com/369arc` |

> *Note: The Ethereum address supports ETH, USDT, USDC, Polygon, and BNB Chain.*

---

Enjoy converting your files!
