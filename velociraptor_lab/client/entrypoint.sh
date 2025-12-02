#!/bin/sh
set -eu

CLIENT_CONFIG=${CLIENT_CONFIG:-/client/client.config.yaml}
SERVER_HOSTNAME=${SERVER_HOSTNAME:-velociraptor-server}
API_PORT=${API_PORT:-8001}

echo "[client] waiting for client config at $CLIENT_CONFIG"
for i in $(seq 1 30); do
  if [ -s "$CLIENT_CONFIG" ]; then
    break
  fi
  sleep 2
done

if [ ! -s "$CLIENT_CONFIG" ]; then
  echo "[client] expected client config at $CLIENT_CONFIG but it is missing after waiting"
  exit 1
fi

exec /opt/velociraptor/velociraptor --config "$CLIENT_CONFIG" client
