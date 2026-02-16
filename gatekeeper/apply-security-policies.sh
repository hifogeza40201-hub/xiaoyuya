#!/bin/bash
# apply-security-policies.sh

kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.14.0/deploy/gatekeeper.yaml

kubectl wait --for=condition=Ready -l control-plane=controller-manager -n gatekeeper-system pod --timeout=120s

kubectl apply -f constraint-templates.yaml
sleep 5
kubectl apply -f constraints.yaml

echo "Security policies applied!"
