# Independent cold-reader request

## Request

An independent agent was given no prior project context and instructed to:

1. read only root `REPRODUCE.md`;
2. use its documented `FAULTLINE_REPOSITORY_URL` override for the isolated
   `v0.27.0-rc1` candidate source;
3. start in a new empty directory;
4. execute the `COLD-START` block verbatim;
5. report exit state, six headline comparisons, questions, improvisations, and
   any undocumented knowledge.

The peer was explicitly prohibited from inspecting other source files, editing
the repository, changing versions, inventing commands, or repairing failures.

## Outcome

The request was made. The peer used only `REPRODUCE.md`, asked zero reader
questions, made zero improvisations, modified no repository files, and confirmed
the documented Git, Make, Docker-client, Docker-server, and Linux-container
prerequisites.

Execution was stopped before clone/build because the hosting platform denied the
peer agent separate approval for repository-controlled host Docker access. No
headline result was evaluated by that peer. This is recorded as an external
execution constraint, not promoted to a successful peer reproduction.

The required cold reproduction itself was completed independently by the
document-execution harness and is preserved in `COLD-START-TRANSCRIPT.txt`.
