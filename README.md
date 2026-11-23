# ACEest Fitness - DevOps CI/CD Assignment

This submission provides a Flask-based fitness-client application, pytest suite, Jenkins pipeline, Docker image definition, SonarQube configuration, and Kubernetes examples. The supplied Tkinter source files are archived unchanged under `versions/`; they are not imported into or packaged with the Flask runtime.

## Run locally

Requires Python 3.12 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest
python ACEest_Fitness.py
```

Open `http://127.0.0.1:5000`. The JSON API provides `GET /health`, `GET /api/programs`, `GET /api/clients`, and `POST /api/clients`. The SQLite database is created under `instance` by default; set `ACEEST_DATABASE` to select another path.

## Build and run with Docker

```powershell
docker build -t aceest-fitness:local .
docker run --rm -p 5000:5000 aceest-fitness:local
```

The image build needs HTTPS access to PyPI with a trusted certificate. If a Windows machine trusts an approved inspection proxy but the build container reports `CERTIFICATE_VERIFY_FAILED`, export its public CA certificates to a temporary file and pass that file as a BuildKit secret:

```powershell
.\scripts\Export-WindowsCaBundle.ps1 -OutputPath "$env:TEMP\aceest-ca-bundle.pem"
docker build --secret "id=pip_ca,src=$env:TEMP\aceest-ca-bundle.pem" -t aceest-fitness:local .
docker build --secret "id=pip_ca,src=$env:TEMP\aceest-ca-bundle.pem" -f Dockerfile.test -t aceest-fitness:test .
docker run --rm aceest-fitness:test python -m pytest -q
Remove-Item -LiteralPath "$env:TEMP\aceest-ca-bundle.pem"
```

The script exports public certificates, not private keys, from Windows Root and Intermediate Certification Authorities stores. The build uses the bundle only for the dependency installation step; it is not copied into the image. Use only a certificate store approved by your organization, do not commit the bundle, and do not disable certificate verification. On a network that does not require the additional CA, use the normal `docker build` command above.

## Set up the Jenkins pipeline

1. Push this local Git repository and its tags to your own GitHub repository after checking that you are allowed to publish the historical source files. Share the public repository URL, or invite the reviewer if private access is permitted.
2. Set up a Linux Jenkins agent with Python 3, Docker, `kubectl`, and `sonar-scanner`. Use a multibranch Pipeline job pointing at the repository; the `branch 'main'` conditions require multibranch branch metadata. Jenkins polls for changes every five minutes; a GitHub webhook can also trigger builds.
3. Configure the SonarQube Jenkins plugin and an installation named `SonarQube`. Add the SonarQube webhook `https://<jenkins-url>/sonarqube-webhook/`, including the trailing slash, so `waitForQualityGate` can receive the result. Set a quality gate in SonarQube.
4. Create Jenkins username/password credentials with ID `dockerhub-creds` using the `himanshujaidka1` Docker Hub username and an access token. The pipeline publishes to `himanshujaidka1/devops-assignment-2`. If the Linux agent also needs a custom CA bundle, place an approved PEM bundle on that agent and set the agent environment variable `PIP_CA_CERT` to its absolute path. Jenkins passes it as a build secret to both images and uses it for host-side pip; the agent needs Docker BuildKit.
5. Configure the Jenkins agent to access the intended assignment cluster. Apply the base manifests before running the deployment stage; the base deployment uses the published `1.2.0` image. Do not use a workplace cluster without authorization.
6. Run a build on `main`. Jenkins runs tests both locally and inside the test container, scans the code, waits for the quality gate, builds and pushes an image tagged with the build number, then deploys it. A failed rollout triggers an automatic rollback and fails the build. Keep the successful build URL, test results, image tag, and SonarQube results for your submission.

The pipeline uses Linux shell steps; a Windows-only Jenkins agent needs equivalent adaptations. For Jenkins to receive GitHub or SonarQube webhooks, its webhook endpoints must be reachable by those services.

## Kubernetes deployment

The base manifests use a rolling update and expect an NGINX Ingress controller. Set the intended Kubernetes context explicitly, then apply:

```powershell
kubectl apply -f k8s/base
kubectl rollout status deployment/aceest
```

For Minikube, enable the ingress add-on and map `aceest.local` to the Minikube IP in the local hosts file. `http://aceest.local` is only a local demonstration address, not a publicly accessible submission endpoint. Use a cluster and DNS/Ingress address reachable by the reviewer if the assignment requires a remote endpoint.

The SQLite database is stored in each container's writable layer. It is lost when that container is replaced, and pods do not share their records; rolling, blue-green, canary, A/B and shadow routes can therefore show different or missing clients. Use sample data only. Reliable shared state and a truly zero-downtime stateful rollout require an external shared database and suitable authentication, neither of which is included.

### Release strategies

Examples are in `k8s/strategies`; they are selectable demonstrations, not applied together. The example `1.0.0` and `1.1.0` tags are published Flask snapshots with identical runtime source, so they demonstrate routing rather than a visible application change. Use distinct validated builds if demonstrating an actual version change.

* **Rolling update:** `k8s/base/deployment.yaml` sets `maxUnavailable: 0` and `maxSurge: 1`. Roll back with `kubectl rollout undo deployment/aceest`.
* **Blue-green:** apply the base Ingress and `blue-green.yaml` (use its `aceest` Service instead of the base Service), then wait until both Deployments are ready. Test green directly with `kubectl port-forward deployment/aceest-green 8080:5000` and visit `http://localhost:8080/health`. Switch traffic using `kubectl set selector service/aceest app=aceest,track=green`; roll back with `kubectl set selector service/aceest app=aceest,track=blue`.
* **Canary:** apply the canary Deployment and Service and then `canary-ingress.yaml`. NGINX Ingress sends 10% of eligible traffic to the candidate; adjust `nginx.ingress.kubernetes.io/canary-weight` as rollout evidence permits. Remove the canary Ingress to send traffic back to stable.
* **A/B test:** apply the canary Deployment and Service and `ab-test-ingress.yaml`. Requests with `X-ACEest-Variant: B` route to the candidate; other requests stay on the stable Ingress. Remove the A/B Ingress to send all traffic back to stable.
* **Shadow:** apply the shadow Deployment and Service, then apply `shadow-ingress-patch.yaml` in place of the base Ingress. NGINX Ingress mirrors requests to the shadow backend while returning the stable response. The example assumes the `default` namespace. Only demonstrate this with safe read-only requests such as `/health`: mirroring POSTs executes them on the shadow backend too. Reapply the base Ingress to remove the mirror annotations.

Canary, A/B, and shadow examples require the community NGINX Ingress controller and the stable base Ingress. The strategies are alternatives and share resource names/host; apply only the strategy being demonstrated. Kubernetes rollback and delivery are dependent on a cluster, Ingress controller, registry image, and configured credentials.

## CI/CD architecture

GitHub is the source repository and Jenkins polls it for changes. Jenkins creates a Python virtual environment, compiles the application, runs pytest on the agent and in a container, and publishes JUnit results. On `main`, SonarScanner submits static analysis to SonarQube and waits for the quality gate, Docker builds and pushes a build-number-tagged image, and `kubectl` updates the rolling Deployment. A failed rollout triggers `kubectl rollout undo` and fails the build.

## Submission evidence

The checked-in configuration is not evidence that external services ran. After completing the setup, collect:

* The accessible GitHub repository URL and commits/tags.
* A recent successful **full-pipeline** Jenkins build URL and test results. A separate local test-only job succeeded at `http://localhost:18081/job/aceest-local-tests/1/`; it does not demonstrate the complete Jenkinsfile.
* Your [Docker Hub repository](https://hub.docker.com/r/himanshujaidka1/devops-assignment-2) and the image tags actually built and pushed. Tags `1.0.0`, `1.1.0`, and `1.2.0` have identical Flask runtime source; the historical Tkinter files are archived source snapshots, **not** prebuilt Flask images.
* A SonarQube dashboard URL or exported/printed report showing the project, analysis date, issues and quality-gate status. See `SONARQUBE-REPORT.md` for the actual local analysis and its limitations.
* A reviewer-reachable cluster endpoint and evidence of each deployment strategy and rollback. Record which image tags were used.

Do not fabricate links, screenshots, analysis results, image versions or live endpoints.

## Assignment report

See [REPORT.md](REPORT.md) for the architecture, implementation notes, validation performed, and remaining environment-dependent submission steps.
