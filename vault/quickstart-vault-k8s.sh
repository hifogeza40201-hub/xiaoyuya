#!/bin/bash
# quickstart-vault-k8s.sh

helm repo add hashicorp https://helm.releases.hashicorp.com
helm upgrade --install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true" \
  --set "csi.enabled=true" \
  --namespace vault --create-namespace

kubectl wait --for=condition=Ready pod/vault-0 -n vault --timeout=120s

kubectl exec -it vault-0 -n vault -- vault operator init -key-shares=1 -key-threshold=1 -format=json > vault-init.json
UNSEAL_KEY=$(jq -r ".unseal_keys_b64[0]" vault-init.json)
ROOT_TOKEN=$(jq -r ".root_token" vault-init.json)
kubectl exec -it vault-0 -n vault -- vault operator unseal $UNSEAL_KEY

kubectl exec -it vault-0 -n vault -- vault login $ROOT_TOKEN
kubectl exec -it vault-0 -n vault -- vault auth enable kubernetes
kubectl exec -it vault-0 -n vault -- vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc"

echo "Vault ready! Root token: $ROOT_TOKEN"
