# RetroCast

Player de transmissões ao vivo com legendas automáticas.

[English](README.md)

## Debian 13 (amd64) — APT

### 1. Configure o repositório

```bash
sudo apt update
sudo apt install -y curl
curl -fsSL https://raw.githubusercontent.com/giliover/retrocast/main/setup-apt.sh -o setup-apt.sh
bash setup-apt.sh
```

Quando solicitado, informe o fingerprint oficial da chave GPG, obtido com o mantenedor por um canal confiável.

### 2. Instale

```bash
sudo apt update
sudo apt install retrocast
```

### Atualizar / desinstalar

```bash
sudo apt update
sudo apt install --only-upgrade retrocast
```

```bash
sudo apt remove retrocast
```

## Outras distribuições Linux — install.sh

Instale primeiro as dependências do sistema. No Arch Linux:

```bash
sudo pacman -S --needed git python ffmpeg portaudio util-linux
```

Nas demais distribuições, utilize o gerenciador de pacotes para instalar os equivalentes (incluindo suporte a venv/pip do Python).

Clone e instale com seu usuário normal (sem sudo):

```bash
git clone https://github.com/giliover/retrocast.git
cd retrocast
bash install.sh
```

Se baixou um ZIP, extraia e execute `bash install.sh` dentro da pasta do projeto.

### Atualizar / desinstalar

```bash
update_retrocast
```

```bash
uninstall_retrocast
```

Se os comandos não forem encontrados, adicione o diretório padrão de instalação ao PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Executar

```bash
retrocast
```

Pressione `K` para visualizar os atalhos.

Feche o player antes de atualizar ou desinstalar. Utilize apenas um método de instalação por vez: desinstale a instalação existente antes de trocar de método. A remoção normal preserva as preferências e o histórico.
