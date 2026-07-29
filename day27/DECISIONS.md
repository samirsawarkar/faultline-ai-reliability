# Day 27 decision log

### D27-001 · Execute the document, not a duplicated recipe

**Decision.** Delimit one shell block in `REPRODUCE.md`; the cold harness extracts
and executes it verbatim.

**Why.** A separately coded test recipe can pass while the reader-facing
instructions rot.

### D27-002 · Use one clean Docker path

**Decision.** The cold path requires Git, Make, and Docker but no host Python.

**Why.** Supporting multiple setup routes multiplies assumptions and makes the
evidence environment depend on the reader's package resolver.

### D27-003 · Keep a documented source-transport override

**Decision.** The copied block gives `FAULTLINE_REPOSITORY_URL` a public default.

**Why.** The same commands can test a candidate snapshot or approved mirror
without a hidden URL edit. The revision and content path remain unchanged.

### D27-004 · Make numbers the success oracle

**Decision.** The inner clean image regenerates all five research families and
checks the full test report, then prints the six registered result strings.

**Why.** Availability of a command or an exit-zero build is weaker than
reproduction of the stated findings.

### D27-005 · Count questions and improvisations

**Decision.** Both must be explicitly zero in the final and peer transcripts.

**Why.** “No problems reported” is not a measurable documentation-quality claim.

### D27-006 · Pin the Day 27 candidate revision

**Decision.** Clone `v0.27.0-rc1`; stop if it is absent.

**Why.** Using `main` would make later readers reproduce different source.
