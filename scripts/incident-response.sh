#!/bin/bash
# incident-response.sh

INCIDENT_TYPE=$1

case $INCIDENT_TYPE in
  "compromised-pod")
    POD_NAME=$2
    NAMESPACE=$3
    echo "Isolating compromised Pod: $POD_NAME"
    kubectl label pod $POD_NAME -n $NAMESPACE incident/isolated=true --overwrite
    kubectl cordon $(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.nodeName}')
    ;;
    
  "revoke-access")
    SERVICE_ACCOUNT=$2
    NAMESPACE=$3
    echo "Revoking service account: $SERVICE_ACCOUNT"
    kubectl delete serviceaccount $SERVICE_ACCOUNT -n $NAMESPACE
    ;;
    
  "lockdown")
    echo "Entering security lockdown mode"
    kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF
    ;;
    
  *)
    echo "Usage: $0 {compromised-pod|revoke-access|lockdown}"
    exit 1
    ;;
esac
