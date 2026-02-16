#!/bin/bash
set -e

NAMESPACE="vault"
VAULT_POD="vault-0"

echo "Waiting for Vault pod..."
kubectl wait --for=condition=Ready pod/${VAULT_POD} -n ${NAMESPACE} --timeout=300s

echo "Initializing Vault..."
kubectl exec -it ${VAULT_POD} -n ${NAMESPACE} -- vault operator init \
  -key-shares=5 -key-threshold=3 -format=json > vault-init.json

echo "Unseal keys saved to vault-init.json (SECURE THIS FILE!)"

# Unseal Vault
for i in 0 1 2; do
  UNSEAL_KEY=$(jq -r ".unseal_keys_b64[$i]" vault-init.json)
  kubectl exec -it ${VAULT_POD} -n ${NAMESPACE} -- vault operator unseal ${UNSEAL_KEY}
done

ROOT_TOKEN=$(jq -r ".root_token" vault-init.json)
kubectl exec -it ${VAULT_POD} -n ${NAMESPACE} -- vault login ${ROOT_TOKEN}

echo "Vault initialized and unsealed! Root token: $ROOT_TOKEN"
