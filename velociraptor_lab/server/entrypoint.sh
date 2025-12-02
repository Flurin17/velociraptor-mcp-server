#!/bin/sh
set -eu

CONFIG_DIR=${CONFIG_DIR:-/config}
SERVER_CONFIG="$CONFIG_DIR/server.config.yaml"
CLIENT_CONFIG=${CLIENT_CONFIG:-/client/client.config.yaml}
API_CONFIG=${API_CONFIG:-/api/api.config.yaml}

GUI_PORT=${GUI_PORT:-8889}
FRONTEND_PORT=${FRONTEND_PORT:-8000}
API_PORT=${API_PORT:-8001}
SERVER_HOSTNAME=${SERVER_HOSTNAME:-velociraptor-server}
ADMIN_USER=${ADMIN_USER:-admin}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin}
API_USER=${API_USER:-api-admin}

update_ports() {
  # Loosely adjust relevant bind addresses/ports if present in config.
  sed -i "s/bind_address: .*/bind_address: 0.0.0.0/" "$SERVER_CONFIG" || true
  perl -0777 -pi -e "s/(API:\n(?:[^\n]*\n){0,10}?bind_port: )\d+/\${1}${API_PORT}/" "$SERVER_CONFIG" || true
  sed -i "s/bind_scheme: .*/bind_scheme: tcp/" "$SERVER_CONFIG" || true
  sed -i "s/port: 8889/port: ${GUI_PORT}/" "$SERVER_CONFIG" || true
  sed -i "s#public_url: .*#public_url: https://${SERVER_HOSTNAME}:${GUI_PORT}/app/index.html#" "$SERVER_CONFIG" || true
}

generate_server_config() {
  echo "[server] generating server.config.yaml"
  mkdir -p "$(dirname "$SERVER_CONFIG")"
  velociraptor config generate > "$SERVER_CONFIG"
  update_ports
}

ensure_admin_user() {
  if [ -n "$ADMIN_USER" ] && [ -n "$ADMIN_PASSWORD" ]; then
    velociraptor --config "$SERVER_CONFIG" user add "$ADMIN_USER" --role administrator --password "$ADMIN_PASSWORD" || true
  fi
}

ensure_client_config() {
  if [ ! -s "$CLIENT_CONFIG" ]; then
    echo "[server] generating client.config.yaml"
    velociraptor --config "$SERVER_CONFIG" config client > "$CLIENT_CONFIG"
  fi
  # Point client at the frontend hostname/port configured for compose.
  sed -i "0,/https:\/\/.*:[0-9]\+\//s#https://.*:[0-9]\+/#https://${SERVER_HOSTNAME}:${FRONTEND_PORT}/#" "$CLIENT_CONFIG" || true
}

ensure_api_client_config() {
  if [ -n "$API_USER" ] && [ ! -s "$API_CONFIG" ]; then
    echo "[server] generating api.config.yaml for $API_USER"
    velociraptor --config "$SERVER_CONFIG" config api_client --name "$API_USER" --role administrator "$API_CONFIG"
  fi
  sed -i "s#api_connection_string: .*#api_connection_string: localhost:${API_PORT}#" "$API_CONFIG" || true
}

if [ ! -s "$SERVER_CONFIG" ]; then
  generate_server_config
fi

update_ports
# Admin user creation can be performed manually if needed; newer versions
# may not accept --password here, so we skip automatic creation to avoid startup failures.
# ensure_admin_user
ensure_client_config
ensure_api_client_config

exec velociraptor --config "$SERVER_CONFIG" frontend
