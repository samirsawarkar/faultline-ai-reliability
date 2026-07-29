# Release candidate — `v0.26.0-rc1`

This candidate packages the completed reliability arc through Day 26.

## Release gate

- full host reproduction green;
- digest-pinned clean-container reproduction green;
- frozen evaluation result unchanged;
- fast experiment subset byte-identical;
- README result traceability green;
- Checkpoint 26 green;
- intended source and evidence committed;
- tag points to that exact commit.

## Reproduce

```bash
make reproduce
make container-reproduce
make release-check
```

The final attestation and tag commit are recorded in Day 26 evidence.
