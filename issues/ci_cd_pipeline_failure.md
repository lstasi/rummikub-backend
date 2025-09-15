### CI/CD Pipeline Failure

**Description:** The CI/CD pipeline has encountered a failure during the build process. The job failed at the step `RUN make copy-static` due to the following error:

```
/bin/sh: 1: make: not found
```

This indicates that the `make` utility is not installed in the environment.

**Resolution:** To resolve this issue, add the following command before the make command in your Dockerfile or environment setup:

```
RUN apt-get update && apt-get install -y make
```

**Reference:** [GitHub Actions Run](https://github.com/lstasi/rummikub-backend/actions/runs/17712935518/job/50334073138)

**Relevant Log:**
```
process "/bin/sh -c make copy-static" did not complete successfully: exit code: 127
```