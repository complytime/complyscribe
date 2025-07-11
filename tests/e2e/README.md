# End-to-End Testing

End-to-end tests are used to verify the CLI functionality of complyscribe from a user's perspective, running in a containerized environment.

## Prerequisites

Before running the end-to-end tests, ensure you have the following prerequisites installed:

- [Podman](https://podman.io/docs/installation) - Container management tool
- [Python 3](https://www.python.org/downloads/) - Required for test automation
- [Poetry](https://python-poetry.org/docs/#installation) - Dependency management

## Resources

- **`mappings`**: This directory contains JSON mappings used with WireMock to mock the Git server endpoints.
- **`play-kube.yml`**: This file includes Kubernetes resources for deploying the mock API server in a pod.
- **`Dockerfile`**: The Dockerfile used to build the mock server container image.

## Running the Tests

To run the end-to-end tests, follow these steps:

1. Clone the project repository:

   ```bash
   git clone https://github.com/RedHatProductSecurity/complyscribe.git
   cd complyscribe 
   ```

2. Install the project dependencies:

   ```bash
   poetry install --without dev --no-root
   ```

3. Run the tests:

   ```bash
    make test-e2e
   ```

   > **Note:** This should always be run from the root of the project directory.

## Additional Notes
- The WireMock tool is used to mock Git server endpoints for testing.
- Podman is used for container and pod management and to build the container image for the mock API server.
- If the images are not already built, the `make test-e2e` command will build them automatically and remove them at the end of the test. If not, you can build them manually with the following command from the root of the project directory:

  ```bash
  podman build -t localhost/mock-server:latest -f tests/e2e/Dockerfile tests/e2e
  podman build -t localhost/complyscribe:latest -f Dockerfile .

  # Use a prebuilt image from quay.io
  podman pull quay.io/continuouscompliance/complyscribe:latest
  export COMPLYSCRIBE_IMAGE=quay.io/continuouscompliance/complyscribe:latest
  ```

- When created tests that push to a branch, ensure the name is "test". This is because the mock API server is configured to only allow pushes to a branch named "test".