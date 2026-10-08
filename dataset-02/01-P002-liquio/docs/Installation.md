## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Node.js](https://nodejs.org/) (v18 or higher)
- [Git](https://git-scm.com/)
- Basic understanding of JavaScript/TypeScript and Node.js

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/liquio-opensource.git
   cd liquio-opensource
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/liquio-opensource.git
   ```

### Initial Setup

#### Docker Compose Setup

**Basic requirements**

To deploy the Liquio platform locally, ensure you have Docker and Docker Compose installed on your system. You can find the official Docker Compose installation guide [here](https://docs.docker.com/compose/). Additionally, make sure you have the necessary permissions to execute shell scripts. The included shell scripts, such as `./scripts/init.sh`, are used to generate configuration files required for the platform's operation. Docker Compose is then utilized to set up and manage the containerized environment, simplifying the deployment process.

**Access control**

The basic local deployment includes an automatically generated Central Authority certificate and user X.509 certificates in PKCS#12 format, simplifying the initial setup process. These certificates are essential for secure communication and authentication within the platform. For production deployments, you can integrate your existing Public Key Infrastructure (PKI) to replace the auto-generated certificates, ensuring compliance with organizational security policies and standards.

**Local startup**

1. Run `./scripts/init.sh` to generate configuration files from templates.
2. Run `docker compose up -d` to setup Docker Compose environment.
3. Navigate to http://localhost:8082 to enter the admin panel.
4. Use the generated key file for admin located in config/admin.p12. The default password is 'admin'.
5. Logout and navigate to http://localhost:8081 to enter the cabinet.
6. Use the generated key file for demo user located in config/demo.p12. The default password is 'demo'.
7. Use the `./scripts/generate-user.sh` to create more user key files.

**Example process**

1. To deploy an example process, let's open the admin panel via admin key.
2. Navigate to Register list page: http://localhost:8082/registry
3. Click "Import" and select "examples/register-100-100.dat". Then confirm the import. This will import the register schema for students.
4. Do the same for "examples/register-100-101.dat" and "examples/register-100-102.dat". This will import the register schemas for institutions and groups.
5. Let's navigate to Workflow list: http://localhost:8082/workflow
6. Click import, continue without skipping the validation, and select "examples/workflow-1000.bpmn" file for import. Confirm to continue.
7. You can now open the workflow configuration page and play with it: http://localhost:8082/workflow/1000
8. Let's log out and open the cabinet: http://localhost:8081. Use the demo key this time.
9. Click "Order a service" and select "Student editing".

**Running Tests**

After the environment is set up, you can run Playwright tests:

```bash
cd test

# Run tests in headless mode
npm run test

# Run tests in headed mode (see browser automation)
npm run test:headed

# Run tests with Playwright UI
npm run test:ui
```

## Kubernetes Setup

For Kubernetes development and testing:

1. Install prerequisites:
   - [minikube](https://minikube.sigs.k8s.io/docs/start/)
   - [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)
   - [helm](https://helm.sh/docs/intro/install/)
2. Start minikube: `minikube start`.
3. Add ingress addon: `minikube addons enable ingress`.
4. Patch ingress controller to use LoadBalancer type: `kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{"spec": {"type": "LoadBalancer"}}'`.
5. Install the Helm chart: `helm install liquio ./helm-chart -f ./helm-chart/values.yaml --create-namespace --namespace liquio`.
   > Images are pulled automatically from `ghcr.io/liquio` — no local build step required.
   > **For local development:** if you have made code changes and need to rebuild images, point your shell at minikube's Docker daemon and run the build script before installing:
   > ```bash
   > eval $(minikube docker-env)
   > ./scripts/build-images.sh --registry ghcr.io/liquio --tag 0.1.0
   > # or rebuild a single service:
   > ./scripts/build-images.sh --registry ghcr.io/liquio --tag 0.1.0 --image cabinet-api
   > ```
   > Then install with `image.pullPolicy=IfNotPresent` so Kubernetes uses the locally built images instead of pulling from the registry:
   > ```bash
   > helm install liquio ./helm-chart -f ./helm-chart/values.yaml --create-namespace --namespace liquio \
   >   --set image.pullPolicy=IfNotPresent
   > ```
6. Set default namespace: `kubectl config set-context --current --namespace=liquio`
7. Wait for the deployment to be ready: `kubectl get pods -w`.
8. Setup domain name resolution:
    8.1. Start minikube tunnel (in a separate terminal, keep it running): `minikube tunnel`
    8.2. Get the LoadBalancer ClusterIP: `CLUSTER_IP=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.spec.clusterIP}')`
    8.3. Add service domain names to hosts file (mapped to ClusterIP): `echo "$CLUSTER_IP admin.liquio.local admin-api.liquio.local cabinet.liquio.local cabinet-api.liquio.local id.liquio.local id-api.liquio.local" | sudo tee -a /etc/hosts`
9. Generate user keys:
    9.1. `./scripts/generate-user.sh --k8s-secret "liquio-ca-certs" --first-name "Admin" --last-name "Liquio" --serial-number "0000000001" --password "admin" --output admin.p12`
    9.2. `./scripts/generate-user.sh --k8s-secret "liquio-ca-certs" --first-name "Demo" --last-name "Liquio" --serial-number "3123456789" --password "demo" --output demo.p12`
10. Access http://admin.liquio.local from the browser.
