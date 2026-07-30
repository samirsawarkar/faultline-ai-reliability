# docs: clarify installation path for pre-built and custom evals

Fixes #1586.

The existing sentence frames the installation choice around whether someone
plans to contribute. That leaves users writing private custom evals unsure which
path applies.

This documentation-only change states the operational distinction:

- install the package to run pre-built evals;
- clone the repository and use the editable install when developing custom
  evals.

No commands, dependencies, or runtime behavior change.

Validation: reviewed the rendered Markdown context and preserved the existing
links and command blocks.
