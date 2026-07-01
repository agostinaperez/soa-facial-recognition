#!/bin/bash
# keycloak-setup.sh — Inicialización automática de Keycloak.
# Crea realm, client, roles, usuarios y un admin (solo si no están creados).

KC_SERVER=http://keycloak:8080

# Espera a que Keycloak esté accesible via TCP (hasta 90s).
wait_for_keycloak() {
  local host port i
  host=$(echo "$KC_SERVER" | sed 's|http://||;s|:.*||')
  port=$(echo "$KC_SERVER" | sed 's|.*:||')
  for i in $(seq 1 30); do
    if exec 3<>"/dev/tcp/$host/$port" 2>/dev/null; then
      exec 3<&- 3>&-
      return 0
    fi
    sleep 3
  done
  return 1
}

# Alias para no repetir la ruta de kcadm.sh.
kcadm() {
  /opt/keycloak/bin/kcadm.sh "$@"
}

# Ejecuta un comando e ignora errores (useful para sondeos).
try() {
  "$@" 2>/dev/null || true
}

echo "Waiting for Keycloak..."
wait_for_keycloak && echo "Keycloak is ready!"

# Autenticación temporal contra el realm master.
kcadm config credentials \
  --server "$KC_SERVER" --realm master \
  --user temp-admin --password temp-admin

# --- Si ya existe el admin permanente, salir ---
ADMIN_EXISTS=$(try kcadm get users -r master -q username="${KEYCLOAK_ADMIN_USER:-admin}" --fields id)
if echo "$ADMIN_EXISTS" | grep -q '"id"'; then
  REALM_EXISTS=$(try kcadm get realms/soa --fields realm 2>/dev/null)
  if echo "$REALM_EXISTS" | grep -q '"soa"'; then
    echo "Keycloak ya está configurado. Saliendo."
    # De todos modos actualizar .env por si cambió el secret
    CLIENT_ID=$(try kcadm get clients -r soa -q clientId=soa --fields id | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
    if [ -n "$CLIENT_ID" ]; then
      CLIENT_SECRET=$(try kcadm get "clients/$CLIENT_ID/client-secret" -r soa | grep '"value"' | sed 's/.*"value"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
      ENV_FILE="/host-env/.env"
      if [ -f "$ENV_FILE" ] && [ -n "$CLIENT_SECRET" ]; then
        TMP=$(mktemp)
        sed "s|KEYCLOAK_CLIENT_SECRET=.*|KEYCLOAK_CLIENT_SECRET=$CLIENT_SECRET|" "$ENV_FILE" > "$TMP"
        cat "$TMP" > "$ENV_FILE"
        rm -f "$TMP"
        echo "Client secret actualizado en .env"
      fi
    fi
    # Eliminar temp-admin si sigue existiendo
    TEMP_ID=$(try kcadm get users -r master -q username=temp-admin --fields id | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
    if [ -n "$TEMP_ID" ]; then
      kcadm delete "users/$TEMP_ID" -r master
    fi
    echo "Done!"
    exit 0
  fi
fi

# --- Master realm: permanent admin ---
# Keycloak 26+ trata KC_BOOTSTRAP_ADMIN como temporal.
# Creamos un admin permanente con rol "admin" y borramos temp-admin al final.
ADMIN_EXISTS=$(try kcadm get users -r master -q username="${KEYCLOAK_ADMIN_USER:-admin}" --fields id)
if ! echo "$ADMIN_EXISTS" | grep -q '"id"'; then
  kcadm create users -r master \
    -s username="${KEYCLOAK_ADMIN_USER:-admin}" \
    -s email="admin@localhost" \
    -s firstName=Admin -s lastName=Admin \
    -s emailVerified=true -s enabled=true
  kcadm set-password -r master \
    --username "${KEYCLOAK_ADMIN_USER:-admin}" \
    --new-password "${KEYCLOAK_ADMIN_PASSWORD:-admin}"
  kcadm add-roles -r master \
    --uusername "${KEYCLOAK_ADMIN_USER:-admin}" \
    --rolename admin
  echo "Permanent admin created."
else
  echo "Permanent admin already exists."
fi

# --- Realm soa ---
REALM_EXISTS=$(try kcadm get realms/soa --fields realm)
if ! echo "$REALM_EXISTS" | grep -q '"soa"'; then
  kcadm create realms -s realm=soa -s enabled=true
  echo "Realm soa created."
else
  echo "Realm soa already exists."
fi

# --- Roles (admin, operator, viewer) ---
for role in admin operator viewer; do
  ROLE_EXISTS=$(try kcadm get roles -r soa -q name="$role" --fields name)
  if ! echo "$ROLE_EXISTS" | grep -q '"name"'; then
    kcadm create roles -r soa -s name="$role" -s "description=Rol $role"
    echo "Role $role created."
  else
    echo "Role $role already exists."
  fi
done

# --- Client soa (confidencial, con Direct Access Grant) ---
CLIENT_EXISTS=$(try kcadm get clients -r soa -q clientId=soa --fields id)
if ! echo "$CLIENT_EXISTS" | grep -q '"id"'; then
  CLIENT_ID=$(kcadm create clients -r soa \
    -s clientId=soa -s clientAuthenticatorType=client-secret \
    -s enabled=true \
    -s 'redirectUris=["http://localhost:8000/*"]' \
    -s 'webOrigins=["http://localhost:8000"]' \
    -s standardFlowEnabled=true \
    -s directAccessGrantsEnabled=true \
    -s publicClient=false -s protocol=openid-connect -i)
  echo "Client soa created."
else
  CLIENT_ID=$(echo "$CLIENT_EXISTS" | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
  echo "Client soa already exists."
fi

# --- Audience mapper for client soa ---
# Por defecto Keycloak setea aud="account". Necesitamos aud="soa" para validar.
MAPPER_EXISTS=$(try kcadm get "clients/$CLIENT_ID/protocol-mappers/models" -r soa | grep '"audience-soa"')
if ! echo "$MAPPER_EXISTS" | grep -q "audience-soa"; then
  kcadm create "clients/$CLIENT_ID/protocol-mappers/models" -r soa \
    -s name=audience-soa \
    -s protocol=openid-connect \
    -s protocolMapper=oidc-audience-mapper \
    -s 'config."included.client.audience"=soa' \
    -s 'config."access.token.claim"=true' \
    -s 'config."id.token.claim"=true' \
    -s 'config."included.custom.audience"=soa' 2>&1
  echo "Audience mapper added."
else
  echo "Audience mapper already exists."
fi

# --- Users in soa realm ---
# Cada user tiene su rol homónimo. La pass sigue el patrón {username}123.
for user in admin operator viewer; do
  USER_EXISTS=$(try kcadm get users -r soa -q username="$user" --fields id)
  if ! echo "$USER_EXISTS" | grep -q '"id"'; then
    kcadm create users -r soa \
      -s username="$user" -s email="${user}@localhost" \
      -s firstName="$user" -s lastName="$user" \
      -s emailVerified=true -s enabled=true
    kcadm set-password -r soa --username "$user" --new-password "${user}123"
    kcadm add-roles -r soa --uusername "$user" --rolename "$user"
    echo "User $user created."
  else
    echo "User $user already exists."
  fi
done

# --- Get or regenerate client secret ---
CLIENT_SECRET=$(try kcadm get "clients/$CLIENT_ID/client-secret" -r soa | grep '"value"' | sed 's/.*"value"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
echo ""
echo "============================================"
echo "  SETUP COMPLETE"
echo "============================================"
echo "  Admin console: http://localhost:8081"
echo "  Admin user:    ${KEYCLOAK_ADMIN_USER:-admin}"
echo "  Admin pass:    ${KEYCLOAK_ADMIN_PASSWORD:-admin}"
echo ""
echo "  Client ID:     soa"
echo "  Client Secret: $CLIENT_SECRET"
echo "============================================"

# Update .env with client secret (if writable)
ENV_FILE="/host-env/.env"
if [ -f "$ENV_FILE" ] && [ -n "$CLIENT_SECRET" ]; then
  if grep -q "KEYCLOAK_CLIENT_SECRET=" "$ENV_FILE"; then
    TMP=$(mktemp)
    sed "s|KEYCLOAK_CLIENT_SECRET=.*|KEYCLOAK_CLIENT_SECRET=$CLIENT_SECRET|" "$ENV_FILE" > "$TMP"
    cat "$TMP" > "$ENV_FILE"
    rm -f "$TMP"
    echo "Updated KEYCLOAK_CLIENT_SECRET in $ENV_FILE"
  fi
fi

# Delete temp-admin — ya no es necesario.
TEMP_ID=$(try kcadm get users -r master -q username=temp-admin --fields id | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
if [ -n "$TEMP_ID" ]; then
  kcadm delete "users/$TEMP_ID" -r master
  echo "temp-admin deleted."
fi

echo "Done!"
