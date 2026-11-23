# ACEest Fitness: CI/CD Project Report

**Name:** Himanshu

**Student ID:** 2025tm93219

**Assignment:** Introduction to DevOps, Assignment 2

## Project overview

ACEest Fitness needed a repeatable way to test and deliver changes to its fitness management application. This project provides a small Flask application and the configuration for a Jenkins-based delivery pipeline. The application allows a user to view fitness programs and add clients with an optional age and program. Client records are stored in SQLite, and the application exposes a health endpoint for deployment checks.

The original files supplied for the assignment are Tkinter desktop applications. They are preserved in the `versions` directory rather than overwritten. The Flask application is a separate, smaller web implementation; it does not claim to reproduce every feature of the desktop versions.

## CI/CD architecture

The intended flow is:

**GitHub → Jenkins → pytest → SonarQube → Docker Hub → Kubernetes**

Jenkins checks the repository for changes every five minutes. It installs the Python dependencies, checks that the code compiles and runs the pytest suite. It also builds a separate test image and executes the same suite inside a container. Jenkins publishes the test results so a failed test can be investigated before a release goes any further.

For the `main` branch, the pipeline sends the source to SonarQube and waits for the configured quality gate. If that passes, Jenkins builds the runtime image, tags it with the build number and pushes it to Docker Hub. The last stage updates the Kubernetes Deployment and waits for it to become ready. If the rollout fails, the pipeline attempts to restore the previous Deployment revision and marks the build as failed. Credentials are expected to be stored in Jenkins, not in the repository.

The Kubernetes manifests include a rolling update with readiness and liveness probes. Separate examples show blue-green switching, a weighted canary, header-based A/B routing and shadow traffic using the community NGINX Ingress controller. The README explains how to select and roll back the examples. The strategies were exercised locally, as described below, but these examples are not a production deployment.

## Challenges and decisions

The main design decision was how to use the supplied desktop code while meeting the requirement for Flask. Instead of changing the old versions, the project keeps them as historical snapshots and implements a focused web application. This makes the code used by the pipeline clear, while retaining the original assignment material.

Tests need to be repeatable and should not change a user's existing data. The Flask application accepts a database path through its configuration; the pytest fixture creates a temporary database for each test. The tests cover the home page and health endpoint, the program list, client creation and retrieval, and invalid or duplicate input. The Docker test image uses the same test suite as the host.

The infrastructure is another practical challenge. A working demonstration depends on accounts, credentials and services outside the project: GitHub, Jenkins, SonarQube, Docker Hub and Kubernetes. These were connected for a local demonstration. SonarQube needs a webhook back to Jenkins so the quality-gate stage can finish, and the initial Kubernetes Deployment must exist before Jenkins can update its image. The local Jenkins agent's Kubernetes credential expires and needs renewal for future runs.

The local Docker build was initially blocked when pip could not verify the package-index certificate from inside the build container. The Windows host could download packages using its trusted certificate store, so the build was retried with a temporary bundle of public Windows CA certificates passed through a Docker BuildKit secret. Both images then built successfully without disabling certificate validation or copying the bundle into an image. Docker Desktop Kubernetes was subsequently enabled, and a local namespace was used instead of the existing workplace cluster.

SQLite is convenient for a small local example but creates a limitation in Kubernetes. Each container has its own writable layer: data can disappear on replacement, and different pods can return different records during a rollout. The examples should therefore use sample data only. A shared database, authentication and persistent storage would be needed before treating this as a reliable multi-user service or claiming a zero-downtime stateful deployment.

## Outcomes and submission evidence

The project now contains the Flask application, historical source files, automated tests, Jenkinsfile, Dockerfiles, SonarQube configuration and Kubernetes examples. Locally, all **9 pytest tests passed**, and Python compilation completed successfully. Both Docker images built using the trusted CA bundle; the test suite also passed inside the test image, and the runtime container responded to HTTP health and program requests.

The repository is public at https://github.com/himanshujaidka/devops-assignment-2. The Flask image is published at https://hub.docker.com/r/himanshujaidka1/devops-assignment-2 with tags `1.0.0`, `1.1.0`, and `1.2.0`. These tags share identical Flask runtime files and do not represent images of the historical Tkinter applications.

An actual local SonarQube scan passed its quality gate with zero reported bugs, zero vulnerabilities, one code smell and one security hotspot requiring review. No coverage report was imported, so the dashboard reports 0.0% coverage; this is not a measurement of test coverage. See `SONARQUBE-REPORT.md` for the scope and limitations.

The application was deployed in the `aceest-2025tm93219` namespace of local Docker Desktop Kubernetes. Health checks passed after a rolling update and rollback, and after switching the Service between blue and green and back to blue. Using a locally installed NGINX Ingress controller, 100 read-only canary requests produced 91 stable and 9 candidate upstream selections; an A/B request with the `B` header reached the candidate while a request without it reached stable. A read-only shadow request appeared in the shadow backend log while the client received the stable response. The examples use identical application code, and these checks do not prove uninterrupted service throughout the transitions. The local port-forward and SonarQube dashboard are not reviewer-accessible public endpoints.

The full Jenkinsfile succeeded in the local multibranch job [build 2](http://localhost:18081/job/aceest-multibranch/job/main/2/) for commit `3ff764b3d87a11968f02a037f14a2f7a39aae129`. Jenkins recorded 18 passing test executions (the same nine tests on the agent and in Docker), received an OK SonarQube quality gate, pushed image tag `2`, and completed the rolling deployment. The local Jenkins page is not reachable by an external reviewer.

The following evidence must be added after the remaining external services are configured and exercised:

| Requirement | Evidence to provide |
|---|---|
| Jenkins | Reviewer-accessible evidence of the successful full-pipeline run and test results |
| SonarQube | Reviewer-accessible dashboard or exported report, including quality-gate status |
| Docker Hub | Images of other application versions, if required by the instructor |
| Kubernetes | Reviewer-reachable endpoint and independently accessible evidence for each strategy |

The full pipeline ran locally, but no reviewer-accessible cluster endpoint is available. The historical Tkinter files are source snapshots, not container images for every application version.
