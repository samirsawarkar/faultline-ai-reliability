# OSS-01 · OpenAI Evals installation clarification

- Upstream: `openai/evals`
- Issue: [#1586](https://github.com/openai/evals/issues/1586)
- Current README blob: `b6d57c76ee5b1361834b415ffbb63bb9c5f3ff68`
- Scope: one sentence; documentation only
- Status: prepared, not opened

The issue identifies a real ambiguity: “not contributing” is not the same as
“not writing a custom eval.” The patch names the actual choice—install the
package to run pre-built evals; clone and use an editable install to develop
custom evals.

Before opening:

1. Re-fetch the upstream README and confirm the blob SHA.
2. Apply `change.patch`.
3. Confirm Markdown renders and links are unchanged.
4. Use the prepared PR description.

No external contribution is claimed until a public pull-request URL is stored in
`day30/oss_contributions.json`.
