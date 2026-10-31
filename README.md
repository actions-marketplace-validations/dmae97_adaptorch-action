# AdaptOrch Run and Evidence

Run an AdaptOrch task from a GitHub Actions workflow and inspect execution and
verification separately. This repository contains a remote-only Action and a
public API client. The AdaptOrch engine and its algorithms run on the hosted
service and are not included. Runs can produce AI-generated content; review the
output and supporting evidence before relying on it.

The Action has been tested against a local mock API, including on GitHub-hosted
runners. Compatibility with your hosted deployment and credentials must be
verified with a real run. An admitted run consumes service quota; model provider
charges can also apply.

## Quick start

Create an AdaptOrch API key at [adaptorch.com/app/api-keys](https://adaptorch.com/app/api-keys).
Add `ADAPTORCH_API_KEY` and `MODEL_PROVIDER_API_KEY` to your repository's Actions
secrets. Use a model that your provider account can access.

```yaml
name: AdaptOrch
on: workflow_dispatch

permissions:
  contents: read

jobs:
  adaptorch:
    runs-on: ubuntu-latest
    steps:
      - id: adaptorch
        uses: dmae97/adaptorch-action@v0.1.0
        with:
          api-key: ${{ secrets.ADAPTORCH_API_KEY }}
          provider: openai
          provider-model: gpt-4.1-mini
          provider-api-key: ${{ secrets.MODEL_PROVIDER_API_KEY }}
          prompt: Give a concise checklist for reviewing a Python release.
          verification: report
```

For stronger supply-chain control, pin the Action to the full commit SHA of a
reviewed release. Python 3.11 or later and Bash are required on the runner.

## Inputs

Choose exactly one of `prompt`, `run-spec-file`, or `resume-run-id`.

| Input | Meaning |
| --- | --- |
| `api-key` | Required AdaptOrch API key; pass an Actions secret. |
| `provider`, `provider-model`, `provider-api-key` | Supply all three for BYOK; omit all three only when the service supports managed credentials. |
| `prompt` | Text task description, at most 64 KiB. |
| `context-file` | Workspace-relative UTF-8 file sent with `prompt`, at most 1 MiB. |
| `run-spec-file` | Workspace-relative JSON run specification with 1–50 subtasks, at most 1 MiB. |
| `resume-run-id` | Observe an existing run without submitting another; do not supply prompt, specification, context, idempotency key or provider credentials. |
| `idempotency-key` | Optional hyphenated UUID; a new UUID is generated when omitted. |
| `api-url` | AdaptOrch API origin; defaults to `https://adaptorch.com`. HTTPS is required except for loopback HTTP. |
| `wait-timeout-seconds` | Polling deadline, 1–3600 seconds; default 180. |
| `poll-interval-seconds` | Time between reads, 1–60 seconds; default 2. |
| `verification` | `off`, `report` (default), or `required`. |
| `report-file` | Optional new workspace-relative path for the terminal run's JSON report. |

## Outputs and recovery

The step exposes `run-id`, `status`, `result-status`, `evaluation-status`,
`verification-status`, `idempotency-key`, and, when a report is saved,
`report-sha256`. Execution `SUCCEEDED` does **not** mean that verification
passed or that the answer is correct. With `verification: required`, a status
other than the explicit server verdict `PASSED` fails the step. With `report`,
missing or failed verification is reported but does not independently fail it.

The Action prints the submission UUID before submitting and never automatically
retries a POST. A lost response or timeout does not prove a run was not created.
Reuse the same `idempotency-key` with the unchanged task to recover a submission;
if a run ID is known, use `resume-run-id` to observe it without a new submission.
A new workflow attempt generates a new UUID unless you supply the existing one.
Polling timeout does not cancel server work.

`report-file` is opt-in. The report can contain task inputs and generated output;
the Action does not upload or print it automatically. This option requires a
hosted deployment that supports the saved report endpoint.

## Data and security

Only the supplied prompt, context or run specification is sent. The Action does
not automatically check out a repository or send diffs. Inputs may be sent to
the AdaptOrch service and the selected model provider. Never include secrets in
prompts or context files, and review any report before sharing it. Use only a
trusted `api-url`: it receives the AdaptOrch credential and, on submission, the
provider credential. Provider credentials are not sent during status or evidence
reads. Avoid running secret-bearing workflows against untrusted pull request code.

## Support and privacy

Report Action bugs and unexpected output through the
[issue tracker](https://github.com/dmae97/adaptorch-action/issues), without
including credentials or sensitive task data. For service and security support,
see [AdaptOrch support](https://adaptorch.com/support). See the service's
[privacy notice](https://adaptorch.com/privacy) for its current data practices
and review status.

## Distribution boundary

This repository is an allowlisted snapshot containing the Action, tests and
public client SDK. It contains no private engine dependency. The SDK snapshot
comes from the public `dmae97/Adaptorch-MCP` repository at commit
`8df6492270d3e8a691a2d6f2a6cc5ed0dc3dd1cd`. The boundary check in CI rejects
additional files, engine imports and known credential patterns.

## License

The Action and bundled client have a limited license for accessing the hosted
AdaptOrch service from GitHub Actions. See [LICENSE](LICENSE). The hosted engine
and its algorithms are not licensed or distributed by this repository.
