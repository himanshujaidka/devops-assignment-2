# ACEest Fitness - DevOps CI/CD Assignment

This submission provides a Flask-based fitness-client application, pytest suite, Jenkins pipeline, Docker image definition, SonarQube configuration, and Kubernetes examples. The supplied Tkinter source files are archived unchanged under `versions/`; they are not imported into or packaged with the Flask runtime.

## Run locally

Requires Python 3.12 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
pytest
python ACEest_Fitness.py
```

Open `http://127.0.0.1:5000`. The JSON API provides `GET /health`, `GET /api/programs`, `GET /api/clients`, and `POST /api/clients`. The SQLite database is created under `instance` by default; set `ACEEST_DATABASE` to select another path.

## Build and run with Docker

```powershell
docker build -t aceest-fitness:local .
docker run --rm -p 5000:5000 aceest-fitness:local
```

Before publishing, replace `YOUR_DOCKERHUB_USER` in `Jenkinsfile` and the Kubernetes image references with the Docker Hub account used for submission. Set Jenkins credentials with ID `dockerhub-creds` (Docker Hub username and access token), configure the SonarQube installation as `SonarQube`, install the SonarScanner CLI and Kubernetes CLI on the Jenkins agent, and configure its Kubernetes context. The pipeline tests every branch; publishing and rolling deployment run on `main`.

## Kubernetes deployment

The base manifests use a rolling update and expect an NGINX Ingress controller. Replace the image placeholder, then apply:

```powershell
kubectl apply -f k8s/base
kubectl rollout status deployment/aceest
```

For Minikube, enable the ingress add-on and map `aceest.local` to the Minikube IP in the local hosts file. A successful local endpoint is then `http://aceest.local`.

### Release strategies

Examples are in `k8s/strategies`; they are selectable demonstrations, not applied together:

* **Rolling update:** `k8s/base/deployment.yaml` sets `maxUnavailable: 0` and `maxSurge: 1`. Roll back with `kubectl rollout undo deployment/aceest`.
* **Blue-green:** apply the base Ingress and `blue-green.yaml` (use its `aceest` Service instead of the base Service), wait until both Deployments are ready, test green with `kubectl port-forward service/aceest 8080:80`, then switch the Service selector with `kubectl patch service aceest -p '{"spec":{"selector":{"app":"aceest","track":"green"}}}'`. Roll back by changing `green` to `blue`.
* **Canary:** apply the canary Deployment and Service and then `canary-ingress.yaml`. NGINX Ingress sends 10% of eligible traffic to the candidate; adjust `nginx.ingress.kubernetes.io/canary-weight` as rollout evidence permits.
* **A/B test:** apply the canary Deployment and Service and `ab-test-ingress.yaml`. Requests with `X-ACEest-Variant: B` route to the candidate; other requests stay on the stable Ingress.
* **Shadow:** apply the shadow Deployment and Service, then apply `shadow-ingress-patch.yaml` in place of the base Ingress. NGINX Ingress mirrors requests to the shadow backend while returning the stable response. Do not use mirrored requests for endpoints with side effects.

Canary, A/B, and shadow examples require the community NGINX Ingress controller and the stable base Ingress. The strategies are alternatives and share resource names/host; apply only the strategy being demonstrated. Kubernetes rollback and delivery are dependent on a cluster, Ingress controller, registry image, and configured credentials.

## CI/CD architecture

GitHub is the source repository and Jenkins is triggered by repository webhooks. Jenkins creates a Python virtual environment, compiles the application, runs pytest and publishes JUnit results. On `main`, SonarScanner submits static analysis to SonarQube, Docker builds and pushes a build-number-tagged image, and `kubectl` updates the rolling Deployment and waits for readiness. Kubernetes readiness/liveness probes expose unhealthy rollouts, and `kubectl rollout undo` provides rollback.

## Assignment report

See [REPORT.md](REPORT.md) for the architecture, implementation notes, validation performed, and remaining environment-dependent submission steps.
