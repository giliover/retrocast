# RetroCast — Player de lives com transcrição em tempo real

[English](README.md) | **Português (Brasil)**

O RetroCast é um player desktop nativo para Linux, compatível com transmissões ao vivo da Twitch e do YouTube, com legendas geradas localmente pelo Faster-Whisper. A interface utiliza Pygame-ce e um visual retrô de terminal.

## Requisitos

Arch Linux:

```bash
sudo pacman -S ffmpeg portaudio python python-pip
```

Debian / Ubuntu:

```bash
sudo apt install ffmpeg libportaudio2 python3-venv
```

## Instalação

```bash
chmod +x install.sh
./install.sh
retrocast
```

O instalador cria um `.venv`, instala as dependências Python (incluindo Streamlink) e cria `~/.local/bin/retrocast` e `~/.local/share/applications/retrocast.desktop`. O instalador não exige `sudo`. Verifique se `~/.local/bin` está no `PATH`.

Para remover apenas os atalhos, preservando o projeto e as preferências, execute `./uninstall.sh`.

## Controles

| Tecla / controle | Ação |
| --- | --- |
| Enter | Iniciar transmissão informada |
| Tab / setas | Completar ou escolher uma sugestão de fonte |
| Espaço | Pausar ou retomar reprodução |
| F11 / F | Ativar ou desativar vídeo em tela cheia |
| Esc | Sair da tela cheia; fora dela, fechar o aplicativo |
| C | Ativar ou desativar legendas |
| S | Salvar transcrição em TXT |
| M | Alterar modelo de transcrição |
| L | Alterar idioma de reconhecimento de fala |
| T | Alternar temas da interface |
| I | Alternar idiomas da interface |
| F3 | Exibir ou ocultar métricas de desempenho |
| VOL + / VOL - | Ajustar volume em intervalos de 5% |

O campo SOURCE aceita trechos de URLs e atalhos como `twi`, `you`, `yt` e `@canal`. As sugestões vêm de atalhos locais e do histórico, sem consultar APIs da Twitch ou do YouTube.

## Idioma e aparência

**O inglês é o idioma padrão para novas instalações.** Para escolher português, clique em **UI LANG** ou pressione **I** para alternar os idiomas. Espanhol também está disponível. O idioma da interface é independente do idioma falado reconhecido pelo Whisper.

Temas: `phosphor`, `amber`, `cyan` e `mono`. As preferências são salvas em `${XDG_CONFIG_HOME:-~/.config}/retrocast/settings.json`. Preferências de idioma já salvas são preservadas após atualizações.

## Configuração de CPU do Whisper

Por padrão, a aplicação detecta as CPUs disponíveis com `nproc` e configura `cpu_threads=nproc` e `num_workers=max(1, nproc // 2)`. Para sobrescrever:

```bash
RETROCAST_WHISPER_THREADS=4 RETROCAST_WHISPER_WORKERS=2 retrocast
```

Mais workers não significam necessariamente mais desempenho quando existe apenas uma transcrição em execução.

## Diagnóstico de desempenho

Pressione **F3** para mostrar ou ocultar as métricas. Os dados são agregados a cada cinco segundos e registrados em `${XDG_STATE_HOME:-~/.local/state}/retrocast/performance.log`.

```bash
tail -f ~/.local/state/retrocast/performance.log
```

## Limitações atuais

- O Streamlink resolve uma URL de mídia, mas nem toda live oferece uma URL reutilizável. Player e transcritor fazem capturas separadas.
- As legendas são geradas em blocos e podem atrasar; as capturas não têm timestamps alinhados.
- A apresentação usa um relógio simples baseado nos PTS do vídeo. Streams irregulares podem apresentar dessincronização; um relógio mestre de áudio ajudaria.
- A decodificação PyAV e a conversão RGB consomem CPU; não há aceleração de GPU nem renderização zero-copy.
- Pausar o vídeo não pausa a transcrição. Pausas longas podem causar buffering ou perda de pacotes.
- Na primeira execução, o Whisper baixa o modelo selecionado. A transcrição é local, sem API externa de transcrição.

**Estado dos testes:** Foram realizadas verificações estáticas de sintaxe; testes completos com lives e hardware precisam ser executados em um sistema Linux.
