#!/usr/bin/env bash
# Descarga uv e instala dependencias
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
make install