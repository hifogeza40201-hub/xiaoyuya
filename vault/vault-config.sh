#!/bin/bash
VAULT_ADDR="https://vault.vault.svc.cluster.local:8200"
ROOT_TOKEN="${VAULT_ROOT_TOKEN}"

vault login ${ROOT_TOKEN}

# Enable KV v2
vault secrets enable -version=2 -path=secret kv-v2

# Enable PKI
vault secrets enable -path=pki pki
vault secrets tune -max-lease-ttl=87600h pki

# Configure Root CA
vault write -field=certificate pki/root/generate/internal \
  common_name="Service Mesh Root CA" ttl=87600h > ca.crt

# Configure CRL
vault write pki/config/urls \
  issuing_certificates="${VAULT_ADDR}/v1/pki/ca" \
  crl_distribution_points="${VAULT_ADDR}/v1/pki/crl"

# Create service mesh role
vault write pki/roles/service-mesh \
  allowed_domains="cluster.local,svc.cluster.local" \
  allow_subdomains=true max_ttl=720h

# Enable Database Engine
vault secrets enable -path=database database
vault write database/config/postgresql-prod \
  plugin_name=postgresql-database-plugin \
  allowed_roles="app-readonly,app-readwrite" \
  connection_url="postgresql://{{username}}:{{password}}@postgres:5432/appdb" \
  username="vaultadmin" password="${PG_ADMIN_PASSWORD}"

# Create dynamic roles
vault write database/roles/app-readonly \
  db_name=postgresql-prod \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}'; GRANT SELECT ON ALL TABLES TO \"{{name}}\";" \
  default_ttl=1h max_ttl=24h

# Enable Kubernetes Auth
vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc"

# Create policy
vault policy write app-read - <<EOF
path "secret/data/app/{{identity.entity.aliases.auth_kubernetes_xxxx.metadata.service_account_namespace}}/*" {
  capabilities = ["read"]
}
path "database/creds/app-readonly" {
  capabilities = ["read"]
}
EOF

echo "Vault configuration completed!"
