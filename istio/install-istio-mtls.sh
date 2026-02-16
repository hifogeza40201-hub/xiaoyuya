#!/bin/bash
# install-istio-mtls.sh

istioctl install -f - <<EOF
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  profile: default
  meshConfig:
    enableAutoMtls: true
    accessLogFile: /dev/stdout
  values:
    global:
      proxy:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
EOF

kubectl apply -f - <<EOF
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT
EOF
