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

## Comandos disponíveis

| Comando | Descrição |
| --- | --- |
| `retrocast` | Abre o player. |
| `update_retrocast` | Atualiza para a última versão do repositório oficial. |
| `update_retrocast --force` | Força a reinstalação da versão mais recente. |
| `update_retrocast --rollback` | Restaura a versão anterior, se disponível. |
| `update_retrocast --version` | Exibe o commit instalado. |
| `uninstall_retrocast` | Desinstala, preservando preferências, histórico e logs. |
| `uninstall_retrocast --purge` | Desinstala e remove também preferências, histórico e logs. |
| `uninstall_retrocast --help` | Exibe a ajuda do desinstalador. |

Feche o player antes de atualizar ou desinstalar. Os modelos compartilhados do Whisper e as dependências do sistema são preservados na desinstalação.

Se os comandos não forem encontrados, execute:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Debian (pacote .deb)

Se você recebeu um pacote Debian compatível com seu sistema:

```bash
sudo apt install ./retrocast_0.1.0_amd64.deb
retrocast
```

Para desinstalar: `sudo apt remove retrocast`. Atualize instalando o novo pacote ou pelo APT quando o repositório estiver disponível. Não utilize os comandos de atualização Git nesta instalação.
