# RetroCast

Player de transmissões ao vivo com legendas automáticas.

## Instalação (Linux)

No Arch Linux:

```bash
sudo pacman -S --needed git python ffmpeg portaudio util-linux
```

Clone o repositório oficial e execute:

```bash
git clone https://github.com/giliover/retrocast.git
cd retrocast
bash install.sh
```

Se extraiu um ZIP, basta executar `bash install.sh` dentro da pasta.

## Executar e atualizar

```bash
retrocast
update_retrocast
```

Feche o player antes de atualizar. Para voltar à versão anterior: `update_retrocast --rollback`.

Se os comandos não forem encontrados: `export PATH="$HOME/.local/bin:$PATH"`.

## Desinstalar

```bash
bash ~/.local/share/retrocast/current/uninstall.sh
```
