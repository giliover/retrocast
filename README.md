# RetroCast

Player de transmissões ao vivo com legendas automáticas.

## Instalação (Linux)

Tenha Python 3, FFmpeg e PortAudio instalados. No Arch Linux:

```bash
sudo pacman -S --needed python ffmpeg portaudio
```

Extraia o projeto, abra o terminal na pasta `retrocast` e execute:

```bash
bash install.sh
```

## Executar

Abra o RetroCast no menu de aplicativos ou execute:

```bash
"${XDG_BIN_HOME:-$HOME/.local/bin}/retrocast"
```

## Desinstalar

Na pasta do projeto:

```bash
bash uninstall.sh
```
