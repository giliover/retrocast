# RetroCast

Live stream player with automatic subtitles.

[Português (Brasil)](README.pt-BR.md)

## Debian 13 (amd64) — APT

### 1. Set up the repository

```bash
sudo apt update
sudo apt install -y curl
curl -fsSL https://raw.githubusercontent.com/giliover/retrocast/master/setup-apt.sh -o setup-apt.sh
bash setup-apt.sh
```

When prompted, enter the official GPG fingerprint obtained from the maintainer through a trusted channel.

### 2. Install

```bash
sudo apt update
sudo apt install retrocast
```

### Update / uninstall

```bash
sudo apt update
sudo apt install --only-upgrade retrocast
```

```bash
sudo apt remove retrocast
```

## Other Linux distributions — install.sh

Install the system dependencies first. On Arch Linux:

```bash
sudo pacman -S --needed git python ffmpeg portaudio util-linux
```

On other distributions, use your package manager to install the equivalent packages (including Python venv/pip support).

Clone and install as a regular user (without sudo):

```bash
git clone https://github.com/giliover/retrocast.git
cd retrocast
bash install.sh
```

If you downloaded a ZIP, extract it and run `bash install.sh` inside the project directory instead.

### Update / uninstall

```bash
update_retrocast
```

```bash
uninstall_retrocast
```

If the commands are not found, add the default installation directory to your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Run

```bash
retrocast
```

Press `K` to see keyboard shortcuts.

Close the player before updating or uninstalling. Use only one installation method at a time: uninstall the existing installation before switching. Normal removal preserves preferences and history.
