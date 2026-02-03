# Jenkins Tutorial


By specifying the git provider flags (i.e. `git-provider-type` and/or `git-server-url`) in `trestle-bot`, the application can be run in any CI tool that can execute jobs in a container environment. Below we will explore how to use `trestle-bot` with [Jenkins](https://www.jenkins.io/).

<details markdown="block">
  <summary>Optionally set up a test environment</summary>

  **Prerequisites**

  This tutorial will include how to stand up a local Jenkins environment for testing. To get started, ensure you have the following prerequisites installed:

  - [Podman](https://podman.io/docs/installation)
  - [OpenShift Local](https://docs.redhat.com/en/documentation/red_hat_openshift_local/2.18/html/getting_started_guide/installation_gsg)
  - [Podman Desktop](https://podman.io/docs/installation)


  **High Level Steps**

  1. Run `crc setup` to ensure your system is properly configured
  2. Obtain your [pull secret](https://console.redhat.com/openshift/create/local)
  3. Initialize and start OpenShift [local](https://podman-desktop.io/docs/openshift/openshift-local)
  4. Get `oc` in your path by running `eval $(crc oc-env)`
  5. Get cluster credentials through `crc console --credentials` and run the `oc login` command
  6. Create a new project - `oc new-project jenkins-test`
  7. Deploy Jenkins with the template - `oc new-app jenkins-ephemeral`

</details>

## Build a basic [Jenkins Job Builder](https://docs.openstack.org/infra/jenkins-job-builder/) job template for trestle-bot

1. Install `jenkins-job-builder`: `pip install --user jenkins-job-builder`
2. [Configure](https://jenkins-job-builder.readthedocs.io/en/latest/execution.html) `jenkins-job-builder`
3. Create and apply `jenkins-jobs update jobs/my-job.yml`

```yaml
- job-template:
    name: 'trestlebot-{git_repo}-autosync'
    description: "DO NOT EDIT"
    concurrent: false
    properties:
        - github:
            url: https://github.com/{git_organization}/{git_repo}/
    scm:
        - git-scm:
            git_url: https://{github_user}@github.com/{git_organization}/{git_repo}.git
            branches:
                - main
    triggers:
        - github
    builders:
        - shell: |
            trestlebot-autosync --markdown-path={markdown} --oscal-model={model}

- project:
    name: my-oscal-project
    jobs:
      - 'trestlebot-{git_repo}-autosync':
          git_organization: my-org
          git_repo: my-repo
          markdown: md_profiles
          model: profile
```

## Example with Groovy

```groovy
pipeline {
    agent {
        docker {
            image 'quay.io/continuouscompliance/trestle-bot:v0.10'
            args "-v ${WORKSPACE}:/trestle-workspace -w /trestle-workspace --entrypoint=''"
            reuseNode true
        }
    }
    stages {
        stage('Autosync') {
            parameters {
                string(name: 'MARKDOWN', defaultValue: 'md_profiles', description: 'Markdown path to use')
                string(name: 'MODEL', defaultValue: 'profile', description: 'OSCAL model to author')
            }
            steps {
                sh 'trestlebot-autosync --markdown-path=${params.MARKDOWN} --oscal-model=${params.MODEL} '
            }
        }
    }
}
```


