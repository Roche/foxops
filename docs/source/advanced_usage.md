# Advanced Usage

## Authentication to Git Repositories

tbd.

## Deployment of foxops

The foxops API server can be deployed using the docker image from `ghcr.io/roche/foxops`.
It exposes the server at port `80`.

### Deployment in k8s

The following manifests are a minimal example for how to deploy foxops in k8s:

```yaml
kind: Deployment
apiVersion: apps/v1
metadata:
  name: foxops-api
  labels:
    app: foxops
spec:
  replicas: 2
  selector:
    matchLabels:
      app: foxops
  template:
    metadata:
      labels:
        app: foxops
        version: v0.0.1
    spec:
      containers:
      - name: foxops
        image: ghcr.io/roche/foxops
        env:
          - name: FOXOPS_GITLAB_ADDRESS
            value: https://gitlab.com/api/v4
          - name: FOXOPS_GITLAB_TOKEN
            value: <dummy>
          - name: FOXOPS_STATIC_TOKEN
            value: <dummy>
          - name: FOXOPS_DATABASE_URL
            value: <dummy>
          - name: FOXOPS_LOG_LEVEL
            value: INFO
        ports:
        - containerPort: 80


---
apiVersion: v1
kind: Service
metadata:
  name: foxops-api
spec:
  ports:
  - name: http
    targetPort: 80
    port: 80
  selector:
    app: foxops

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: foxops-api
spec:
  rules:
  - host: foxops.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: foxops-api
            port:
              number: 80
```