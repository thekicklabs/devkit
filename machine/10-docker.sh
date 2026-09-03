#!/usr/bin/env bash
# description: Docker Engine + compose plugin from the official apt repo; adds you to the docker group
. "$(dirname "$(readlink -f "$0")")/_lib.sh"

check() { command -v docker >/dev/null && docker compose version >/dev/null 2>&1; }
main() {
  . /etc/os-release
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL "https://download.docker.com/linux/${ID}/gpg" | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  apt_install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER"
  echo "added $USER to the docker group — log out and back in for it to apply"
}
dispatch "$@"
