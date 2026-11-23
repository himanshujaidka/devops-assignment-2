pipeline {
    agent { label 'aceest' }

    options {
        disableConcurrentBuilds()
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    environment {
        IMAGE_NAME = 'himanshujaidka1/devops-assignment-2'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Install and test') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    if [ -n "${PIP_CA_CERT:-}" ]; then
                        test -r "$PIP_CA_CERT"
                        export PIP_CERT="$PIP_CA_CERT"
                    fi
                    pip install --upgrade pip
                    pip install -r requirements-dev.txt
                    python -m compileall -q ACEest_Fitness.py tests
                    python -m pytest --junitxml=pytest-report.xml
                '''
            }
            post {
                always {
                    junit 'pytest-report.xml'
                }
            }
        }

        stage('Containerized tests') {
            steps {
                sh '''
                    mkdir -p test-results
                    set --
                    if [ -n "${PIP_CA_CERT:-}" ]; then
                        test -r "$PIP_CA_CERT"
                        set -- --secret "id=pip_ca,src=$PIP_CA_CERT"
                    fi
                    docker build "$@" -f Dockerfile.test -t aceest-fitness:test .
                    container_id=$(docker create aceest-fitness:test)
                    trap 'docker rm -f "$container_id" >/dev/null' EXIT
                    status=0
                    docker start -a "$container_id" || status=$?
                    if ! docker cp "$container_id:/test-results/junit.xml" test-results/junit.xml; then
                        echo "Could not retrieve container test results."
                        exit 1
                    fi
                    exit "$status"
                '''
            }
            post {
                always {
                    junit 'test-results/*.xml'
                }
            }
        }

        stage('SonarQube analysis') {
            when {
                branch 'main'
            }
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh 'sonar-scanner'
                }
            }
        }

        stage('SonarQube quality gate') {
            when {
                branch 'main'
            }
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build and publish image') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKERHUB_USER',
                    passwordVariable: 'DOCKERHUB_TOKEN'
                )]) {
                    sh '''
                        echo "$DOCKERHUB_TOKEN" | docker login \
                          --username "$DOCKERHUB_USER" --password-stdin
                        set --
                        if [ -n "${PIP_CA_CERT:-}" ]; then
                            test -r "$PIP_CA_CERT"
                            set -- --secret "id=pip_ca,src=$PIP_CA_CERT"
                        fi
                        docker build "$@" -t "$IMAGE_NAME:$IMAGE_TAG" .
                        docker push "$IMAGE_NAME:$IMAGE_TAG"
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy rolling update') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    kubectl set image deployment/aceest \
                      aceest="$IMAGE_NAME:$IMAGE_TAG"
                    if ! kubectl rollout status deployment/aceest --timeout=120s; then
                        echo "Deployment failed; rolling back to the previous revision."
                        kubectl rollout undo deployment/aceest
                        kubectl rollout status deployment/aceest --timeout=120s
                        exit 1
                    fi
                '''
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
