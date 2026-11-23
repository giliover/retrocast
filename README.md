# RetroCast — Live Stream Player with Real-Time Transcription

**English** | [Português (Brasil)](README.pt-BR.md)

RetroCast is a native Linux desktop player for Twitch and YouTube live streams, featuring on-screen captions powered by local Faster-Whisper transcription. It uses Pygame-ce for its retro terminal-style interface.

## Requirements

Arch Linux:

```bash
sudo pacman -S ffmpeg portaudio python python-pip
```

Debian / Ubuntu:

```bash
sudo apt install ffmpeg libportaudio2 python3-venv
```

## Installation

```bash
chmod +x install.sh
./install.sh
retrocast
```

The installer creates a `.venv`, installs the Python dependencies (including Streamlink), and creates `~/.local/bin/retrocast` and `~/.local/share/applications/retrocast.desktop`. No `sudo` is needed for the installer. Ensure `~/.local/bin` is in your `PATH`.

To remove the launchers without deleting the project or preferences, run `./uninstall.sh`.

## Controls

| Key / control | Action |
| --- | --- |
| Enter | Start watching the entered stream |
| Tab / arrow keys | Complete or select a source suggestion |
| Space | Pause or resume playback |
| F11 / F | Toggle fullscreen video |
| Esc | Exit fullscreen; otherwise close the app |
| C | Toggle captions |
| S | Save transcript as TXT |
| M | Change transcription model |
| L | Change speech-recognition language |
| T | Cycle UI themes |
| I | Cycle UI languages |
| F3 | Toggle performance diagnostics |
| VOL + / VOL - | Change volume in 5% steps |

The SOURCE field supports URL fragments and shortcuts such as `twi`, `you`, `yt`, and `@channel`. Suggestions come from local domain shortcuts and history, not Twitch or YouTube APIs.

## Language and appearance

**English is the default UI language for new installations.** Choose **Portuguese** with the **UI LANG** button or press **I** to cycle languages. Spanish is also available. The UI language is independent of the spoken language used by Whisper.

Themes: `phosphor`, `amber`, `cyan`, and `mono`. Preferences are saved to `${XDG_CONFIG_HOME:-~/.config}/retrocast/settings.json`. Existing saved language preferences are preserved after upgrading.

## Whisper CPU settings

By default, the app detects available CPUs using `nproc` and configures `cpu_threads=nproc` and `num_workers=max(1, nproc // 2)`. Override them if needed:

```bash
RETROCAST_WHISPER_THREADS=4 RETROCAST_WHISPER_WORKERS=2 retrocast
```

More workers do not necessarily improve throughput when only one transcription runs at a time.

## Performance diagnostics

Press **F3** to show or hide the diagnostics overlay. Metrics are aggregated every five seconds and written to `${XDG_STATE_HOME:-~/.local/state}/retrocast/performance.log`.

```bash
tail -f ~/.local/state/retrocast/performance.log
```

## Current limitations

- Streamlink resolves a media URL, but not every live stream provides a reusable URL. Playback and transcription use separate captures.
- Captions are generated in chunks and can lag behind playback; the two captures do not have aligned timestamps.
- Video presentation uses a basic PTS clock. Irregular streams may experience audio/video drift; an audio-master clock would improve synchronization.
- PyAV decoding and RGB conversion use CPU; GPU acceleration and zero-copy rendering are not implemented.
- Pausing playback does not pause transcription. Long pauses may cause buffering or dropped packets.
- The first Whisper run downloads the selected model. Transcription runs locally, without a transcription API.

**Testing status:** Static syntax checks have been performed; full live-stream and hardware playback testing must be performed on a Linux system.
