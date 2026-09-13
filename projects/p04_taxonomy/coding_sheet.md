# P4 Failure Taxonomy — Open Coding Sheet

Total traces analyzed: **200**

| ID | Tier | Verdict | Steps | Expected Answer | Agent Answer | Required Source | Cited Sources | First Failure (Plain Language) | Axial Mode |
|---|---|---|---|---|---|---|---|---|---|
| `s-0001` | T1 | **FAIL** | 3 | `Sable-4492` | `` | `doc-0098` | `` | Model emitted text without structured tool call or answer after 2 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0002` | T1 | **FAIL** | 3 | `Ultra-4519` | `` | `doc-0103` | `` | Model emitted text without structured tool call or answer after 2 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0003` | T1 | **PASS** | 3 | `Zinc-4524` | `The internal codename of Girona Foundry is **Zinc-4524**.` | `doc-0104` | `doc-0104` | N/A (Grounded Pass) | `NONE` |
| `s-0004` | T1 | **FAIL** | 6 | `Vellum-4545` | `` | `doc-0109` | `` | Model emitted text without structured tool call or answer after 5 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0005` | T1 | **FAIL** | 8 | `Rune-4566` | `` | `doc-0113` | `` | Model emitted text without structured tool call or answer after 7 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0006` | T1 | **FAIL** | 5 | `Rune-4591` | `` | `doc-0118` | `` | Model emitted text without structured tool call or answer after 4 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0007` | T1 | **FAIL** | 6 | `Xeno-4597` | `` | `doc-0119` | `` | Model emitted text without structured tool call or answer after 5 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0008` | T1 | **FAIL** | 7 | `Wisp-4621` | `` | `doc-0124` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0009` | T1 | **FAIL** | 7 | `Talc-4643` | `` | `doc-0128` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0010` | T1 | **FAIL** | 3 | `Talc-4668` | `` | `doc-0133` | `` | Model emitted text without structured tool call or answer after 2 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0011` | T1 | **FAIL** | 3 | `Zinc-4674` | `` | `doc-0134` | `` | Model emitted text without structured tool call or answer after 2 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0012` | T1 | **FAIL** | 4 | `Vellum-4695` | `` | `doc-0139` | `` | Model emitted text without structured tool call or answer after 3 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0013` | T1 | **FAIL** | 3 | `Ultra-4719` | `` | `doc-0143` | `` | Model emitted text without structured tool call or answer after 2 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0014` | T1 | **FAIL** | 2 | `Sable-4742` | `` | `doc-0148` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0015` | T1 | **FAIL** | 1 | `Vellum-4745` | `` | `doc-0149` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0016` | T1 | **FAIL** | 1 | `Zinc-4074` | `` | `doc-0014` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0017` | T1 | **PASS** | 3 | `Vellum-4145` | `The archival reference of Riven Foundry is **Vellum-4145**.` | `doc-0029` | `doc-0029` | N/A (Grounded Pass) | `NONE` |
| `s-0018` | T1 | **PASS** | 9 | `Kelvin-4384` | `The internal codename of Aster Systems is **Kelvin-4384**.` | `doc-0076` | `doc-0076` | N/A (Grounded Pass) | `NONE` |
| `s-0019` | T1 | **PASS** | 6 | `Lumen-4385` | `The archival reference of Kestrel Collective is **Lumen-4385**.` | `doc-0077` | `doc-0077` | N/A (Grounded Pass) | `NONE` |
| `s-0020` | T1 | **FAIL** | 5 | `Rune-4391` | `I couldn’t verify the external auditor for Aster Labs from the available documents—the searches returned no matching source.` | `doc-0078` | `No matching document found` | Model failed to locate doc-0078 and explicitly abstained from answering. | `RETRIEVAL_FAILURE_ABSTENTION` |
| `s-0021` | T1 | **FAIL** | 5 | `Basalt-4401` | `` | `doc-0080` | `` | Model emitted text without structured tool call or answer after 4 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0022` | T1 | **FAIL** | 5 | `Indigo-4407` | `` | `doc-0081` | `` | Model emitted text without structured tool call or answer after 4 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0023` | T1 | **FAIL** | 6 | `Onyx-4413` | `Quill Systems is headquartered in the Onyx district.` | `doc-0082` | `doc-0082` | Model retrieved correct document doc-0082 but truncated token (emitted Onyx instead of Onyx-4413). | `ANSWER_EXTRACTION_TRUNCATION` |
| `s-0024` | T1 | **FAIL** | 6 | `Xeno-4422` | `` | `doc-0084` | `` | Model emitted text without structured tool call or answer after 5 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0025` | T1 | **FAIL** | 7 | `Cobalt-4427` | `` | `doc-0085` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0026` | T1 | **FAIL** | 3 | `Helix-4431` | `` | `doc-0086` | `` | Model emitted text without structured tool call or answer after 2 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0027` | T1 | **FAIL** | 4 | `Onyx-4438` | `` | `doc-0087` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0028` | T1 | **FAIL** | 3 | `Cobalt-4452` | `` | `doc-0090` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0029` | T1 | **FAIL** | 2 | `Kelvin-4459` | `` | `doc-0091` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0030` | T1 | **FAIL** | 1 | `Mica-4461` | `` | `doc-0092` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0031` | T1 | **FAIL** | 1 | `Quartz-4465` | `` | `doc-0093` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0032` | T1 | **FAIL** | 1 | `Cobalt-4477` | `` | `doc-0095` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0033` | T1 | **FAIL** | 1 | `Kelvin-4484` | `` | `doc-0096` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0034` | T1 | **FAIL** | 1 | `Lumen-4485` | `` | `doc-0097` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0035` | T1 | **FAIL** | 1 | `Zinc-4499` | `` | `doc-0099` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0036` | T1 | **PASS** | 3 | `Alto-4500` | `The archival reference of Girona Systems is **Alto-4500**.` | `doc-0100` | `doc-0100` | N/A (Grounded Pass) | `NONE` |
| `s-0037` | T1 | **PASS** | 5 | `Gossamer-4505` | `The archival reference of Peregrine Collective is **Gossamer-4505**.` | `doc-0101` | `doc-0101` | N/A (Grounded Pass) | `NONE` |
| `s-0038` | T1 | **FAIL** | 9 | `Onyx-4513` | `` | `doc-0102` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0039` | T1 | **FAIL** | 6 | `Basalt-4526` | `` | `doc-0105` | `` | Model emitted text without structured tool call or answer after 5 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0040` | T1 | **PASS** | 4 | `Kelvin-4534` | `The internal codename of Solace Systems is **Kelvin-4534**.` | `doc-0106` | `doc-0106` | N/A (Grounded Pass) | `NONE` |
| `s-0041` | T1 | **FAIL** | 6 | `Mica-4536` | `` | `doc-0107` | `` | Model emitted text without structured tool call or answer after 5 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0042` | T1 | **FAIL** | 5 | `Talc-4543` | `` | `doc-0108` | `` | Model emitted text without structured tool call or answer after 4 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0043` | T1 | **FAIL** | 3 | `Cobalt-4552` | `` | `doc-0110` | `` | Model emitted text without structured tool call or answer after 2 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0044` | T1 | **FAIL** | 7 | `Helix-4556` | `` | `doc-0111` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0045` | T1 | **FAIL** | 7 | `Nyx-4562` | `` | `doc-0112` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0046` | T1 | **FAIL** | 5 | `Wisp-4571` | `` | `doc-0114` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0047` | T1 | **PASS** | 4 | `Alto-4575` | `The archival reference of Ironwood Foundry is **Alto-4575**.` | `doc-0115` | `doc-0115` | N/A (Grounded Pass) | `NONE` |
| `s-0048` | T1 | **FAIL** | 1 | `Kelvin-4584` | `` | `doc-0116` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0049` | T1 | **FAIL** | 1 | `Prism-4589` | `` | `doc-0117` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0050` | T1 | **FAIL** | 1 | `Ferro-4604` | `` | `doc-0120` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0051` | T1 | **FAIL** | 8 | `Jade-4608` | `` | `doc-0121` | `` | Upstream API server error (HTTP 500: Internal Server Error) interrupted agent execution. | `INFRASTRUCTURE_SERVER_ERROR` |
| `s-0052` | T1 | **FAIL** | 3 | `Nyx-4612` | `` | `doc-0122` | `` | Model emitted text without structured tool call or answer after 2 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0053` | T1 | **FAIL** | 3 | `Ultra-4619` | `` | `doc-0123` | `` | Model emitted text without structured tool call or answer after 2 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0054` | T1 | **PASS** | 3 | `Ferro-4629` | `The internal codename of Orrery Foundry is **Ferro-4629**.` | `doc-0125` | `doc-0125` | N/A (Grounded Pass) | `NONE` |
| `s-0055` | T1 | **PASS** | 6 | `Indigo-4632` | `The flagship product of Juniper Works is **Indigo-4632**.` | `doc-0126` | `doc-0126` | N/A (Grounded Pass) | `NONE` |
| `s-0056` | T1 | **PASS** | 4 | `Lumen-4635` | `The archival reference of Lodestar Union is **Lumen-4635**.` | `doc-0127` | `doc-0127` | N/A (Grounded Pass) | `NONE` |
| `s-0057` | T1 | **FAIL** | 8 | `Xeno-4647` | `` | `doc-0129` | `` | Model emitted text without structured tool call or answer after 7 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0058` | T1 | **PASS** | 5 | `Ferro-4654` | `The internal codename of Xebec Union is **Ferro-4654**.` | `doc-0130` | `doc-0130` | N/A (Grounded Pass) | `NONE` |
| `s-0059` | T1 | **FAIL** | 8 | `Kelvin-4659` | `` | `doc-0131` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0060` | T1 | **PASS** | 3 | `Lumen-4660` | `The archival reference of Kestrel Systems is **Lumen-4660**.` | `doc-0132` | `doc-0132` | N/A (Grounded Pass) | `NONE` |
| `s-0061` | T1 | **FAIL** | 3 | `Alto-4675` | `` | `doc-0135` | `` | Model emitted text without structured tool call or answer after 2 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0062` | T1 | **FAIL** | 5 | `Helix-4681` | `` | `doc-0136` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0063` | T1 | **PASS** | 4 | `Lumen-4685` | `The archival reference of Quill Union is **Lumen-4685**.` | `doc-0137` | `doc-0137` | N/A (Grounded Pass) | `NONE` |
| `s-0064` | T1 | **FAIL** | 1 | `Rune-4691` | `` | `doc-0138` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0065` | T1 | **FAIL** | 1 | `Alto-4700` | `` | `doc-0140` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0066` | T1 | **FAIL** | 1 | `Helix-4706` | `` | `doc-0141` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0067` | T1 | **FAIL** | 1 | `Mica-4711` | `` | `doc-0142` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0068` | T2 | **FAIL** | 12 | `Mica-4161` | `` | `doc-0032` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0069` | T2 | **FAIL** | 1 | `Rune-4166` | `` | `doc-0033` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0070` | T2 | **FAIL** | 1 | `Onyx-4188` | `` | `doc-0037` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0071` | T2 | **PASS** | 12 | `Yolk-4198` | `Yolk-4198` | `doc-0039` | `doc-0039` | N/A (Grounded Pass) | `NONE` |
| `s-0072` | T2 | **FAIL** | 12 | `Lumen-4210` | `` | `doc-0042` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0073` | T2 | **FAIL** | 12 | `Onyx-4238` | `` | `doc-0047` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0074` | T2 | **FAIL** | 12 | `Ultra-4244` | `` | `doc-0048` | `` | Model issued overconstrained multi-word search queries (9/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0075` | T2 | **FAIL** | 4 | `Onyx-4263` | `` | `doc-0052` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0076` | T2 | **FAIL** | 1 | `Xeno-4272` | `` | `doc-0054` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0077` | T2 | **FAIL** | 12 | `Lumen-4285` | `` | `doc-0057` | `` | Model issued overconstrained multi-word search queries (7/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0078` | T2 | **FAIL** | 9 | `Nyx-4312` | `` | `doc-0062` | `` | Model emitted text without structured tool call or answer after 8 search attempts. | `MALFORMED_TOOL_CALL` |
| `s-0079` | T2 | **FAIL** | 12 | `Sable-4317` | `` | `doc-0063` | `` | Model issued overconstrained multi-word search queries (10/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0080` | T2 | **FAIL** | 12 | `Onyx-4338` | `` | `doc-0067` | `` | Model issued overconstrained multi-word search queries (8/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0081` | T2 | **FAIL** | 12 | `Vellum-4345` | `` | `doc-0069` | `` | Model issued overconstrained multi-word search queries (7/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0082` | T2 | **FAIL** | 2 | `Onyx-4363` | `` | `doc-0072` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0083` | T2 | **FAIL** | 2 | `Nyx-4387` | `` | `doc-0077` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0084` | T2 | **FAIL** | 2 | `Talc-4393` | `` | `doc-0078` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0085` | T2 | **FAIL** | 1 | `Nyx-4412` | `` | `doc-0082` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0086` | T2 | **FAIL** | 1 | `Wisp-4421` | `` | `doc-0084` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0087` | T2 | **FAIL** | 12 | `Mica-4436` | `` | `doc-0087` | `` | Model issued overconstrained multi-word search queries (10/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0088` | T2 | **FAIL** | 12 | `Nyx-4462` | `` | `doc-0092` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0089` | T2 | **FAIL** | 11 | `Talc-4468` | `` | `doc-0093` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0090` | T2 | **FAIL** | 12 | `Nyx-4487` | `` | `doc-0097` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0091` | T2 | **FAIL** | 12 | `Wisp-4496` | `` | `doc-0099` | `` | Model issued overconstrained multi-word search queries (10/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0092` | T2 | **FAIL** | 4 | `Mica-4511` | `` | `doc-0102` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0093` | T2 | **FAIL** | 2 | `Mica-4536` | `` | `doc-0107` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0094` | T2 | **FAIL** | 12 | `Rune-4541` | `` | `doc-0108` | `` | Model issued overconstrained multi-word search queries (10/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0095` | T2 | **FAIL** | 12 | `Lumen-4560` | `` | `doc-0112` | `` | Model issued overconstrained multi-word search queries (8/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0096` | T2 | **FAIL** | 9 | `Wisp-4571` | `` | `doc-0114` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0097` | T2 | **FAIL** | 12 | `Prism-4589` | `` | `doc-0117` | `` | Model issued overconstrained multi-word search queries (7/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0098` | T2 | **FAIL** | 12 | `Nyx-4612` | `` | `doc-0122` | `` | Model issued overconstrained multi-word search queries (7/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0099` | T2 | **FAIL** | 3 | `Quartz-4615` | `` | `doc-0123` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0100` | T2 | **FAIL** | 2 | `Lumen-4635` | `` | `doc-0127` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0101` | T2 | **FAIL** | 2 | `Yolk-4648` | `` | `doc-0129` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0102` | T2 | **FAIL** | 1 | `Mica-4661` | `` | `doc-0132` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0103` | T2 | **FAIL** | 12 | `Mica-4686` | `` | `doc-0137` | `` | Model issued overconstrained multi-word search queries (8/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0104` | T2 | **FAIL** | 12 | `Talc-4693` | `` | `doc-0138` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0105` | T2 | **FAIL** | 12 | `Prism-4714` | `` | `doc-0142` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0106` | T2 | **FAIL** | 12 | `Vellum-4720` | `` | `doc-0144` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0107` | T2 | **PASS** | 10 | `Lumen-4735` | `Lumen-4735` | `doc-0147` | `doc-0147` | N/A (Grounded Pass) | `NONE` |
| `s-0108` | T2 | **FAIL** | 6 | `Ultra-4019` | `` | `doc-0003` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0109` | T2 | **FAIL** | 1 | `Xeno-4022` | `` | `doc-0004` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0110` | T2 | **FAIL** | 12 | `Quartz-4040` | `Lumen-4035` | `doc-0008` | `doc-0007` | Model stopped at intermediate hop doc-0007 and cited wrong organization instead of traversing to doc-0008. | `PREMATURE_STOP_WRONG_HOP` |
| `s-0111` | T2 | **FAIL** | 12 | `Wisp-4046` | `` | `doc-0009` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0112` | T2 | **FAIL** | 12 | `Talc-4068` | `` | `doc-0013` | `` | Model issued overconstrained multi-word search queries (6/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0113` | T2 | **FAIL** | 11 | `Talc-4093` | `` | `doc-0018` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0114` | T2 | **PASS** | 10 | `Wisp-4096` | `Wisp-4096` | `doc-0019` | `doc-0019` | N/A (Grounded Pass) | `NONE` |
| `s-0115` | T2 | **FAIL** | 4 | `Rune-4116` | `` | `doc-0023` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0116` | T2 | **FAIL** | 3 | `Yolk-4123` | `` | `doc-0024` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0117` | T2 | **FAIL** | 1 | `Sable-4142` | `` | `doc-0028` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0118` | T2 | **FAIL** | 12 | `Yolk-4173` | `` | `doc-0034` | `` | Model issued overconstrained multi-word search queries (8/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0119` | T2 | **FAIL** | 11 | `Sable-4192` | `` | `doc-0038` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0120` | T2 | **FAIL** | 11 | `Talc-4218` | `` | `doc-0043` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0121` | T2 | **FAIL** | 12 | `Yolk-4223` | `` | `doc-0044` | `` | Model issued overconstrained multi-word search queries (8/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0122` | T2 | **FAIL** | 12 | `Wisp-4246` | `` | `doc-0049` | `` | Model issued overconstrained multi-word search queries (10/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0123` | T2 | **FAIL** | 4 | `Sable-4267` | `` | `doc-0053` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0124` | T2 | **FAIL** | 2 | `Rune-4291` | `` | `doc-0058` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0125` | T2 | **FAIL** | 1 | `Zinc-4299` | `` | `doc-0059` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0126` | T2 | **FAIL** | 12 | `Zinc-4324` | `` | `doc-0064` | `` | Model issued overconstrained multi-word search queries (8/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0127` | T2 | **FAIL** | 12 | `Ultra-4344` | `` | `doc-0068` | `` | Model issued overconstrained multi-word search queries (9/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0128` | T2 | **FAIL** | 11 | `Quartz-4365` | `` | `doc-0073` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0129` | T2 | **FAIL** | 12 | `Vellum-4370` | `` | `doc-0074` | `` | Model issued overconstrained multi-word search queries (9/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0130` | T2 | **FAIL** | 11 | `Yolk-4398` | `` | `doc-0079` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0131` | T2 | **FAIL** | 3 | `Talc-4418` | `` | `doc-0083` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0132` | T2 | **FAIL** | 2 | `Sable-4442` | `` | `doc-0088` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0133` | T2 | **FAIL** | 2 | `Wisp-4446` | `` | `doc-0089` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0134` | T2 | **FAIL** | 12 | `Vellum-4470` | `` | `doc-0094` | `` | Model issued overconstrained multi-word search queries (10/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0135` | T3 | **FAIL** | 12 | `Alto-4000` | `` | `doc-0000` | `` | Model issued overconstrained multi-word search queries (10/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0136` | T3 | **FAIL** | 12 | `Cobalt-4027` | `` | `doc-0005` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0137` | T3 | **FAIL** | 12 | `Drift-4053` | `` | `doc-0010` | `` | Model issued overconstrained multi-word search queries (10/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0138` | T3 | **FAIL** | 12 | `Cobalt-4077` | `` | `doc-0015` | `` | Model traversed multiple valid intermediate hops but ran out of steps before completing chain. | `MULTI_HOP_TRAVERSAL_EXHAUSTION` |
| `s-0139` | T3 | **FAIL** | 2 | `Alto-4100` | `` | `doc-0020` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0140` | T3 | **FAIL** | 1 | `Drift-4128` | `` | `doc-0025` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0141` | T3 | **FAIL** | 1 | `Cobalt-4152` | `` | `doc-0030` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0142` | T3 | **FAIL** | 1 | `Basalt-4176` | `` | `doc-0035` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0143` | T3 | **FAIL** | 12 | `Drift-4203` | `` | `doc-0040` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0144` | T3 | **FAIL** | 12 | `Alto-4225` | `` | `doc-0045` | `` | Model issued overconstrained multi-word search queries (6/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0145` | T3 | **FAIL** | 12 | `Ferro-4254` | `` | `doc-0050` | `` | Model issued overconstrained multi-word search queries (6/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0146` | T3 | **FAIL** | 12 | `Drift-4278` | `` | `doc-0055` | `` | Model issued overconstrained multi-word search queries (7/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0147` | T3 | **FAIL** | 12 | `Ferro-4304` | `` | `doc-0060` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0148` | T3 | **FAIL** | 3 | `Basalt-4326` | `` | `doc-0065` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0149` | T3 | **FAIL** | 1 | `Drift-4353` | `` | `doc-0070` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0150` | T3 | **FAIL** | 1 | `Cobalt-4377` | `` | `doc-0075` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0151` | T3 | **FAIL** | 1 | `Cobalt-4402` | `` | `doc-0080` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0152` | T3 | **FAIL** | 1 | `Cobalt-4427` | `` | `doc-0085` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0153` | T3 | **FAIL** | 1 | `Ferro-4454` | `` | `doc-0090` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0154` | T3 | **FAIL** | 1 | `Alto-4475` | `` | `doc-0095` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0155` | T3 | **FAIL** | 12 | `Ferro-4504` | `` | `doc-0100` | `` | Model issued overconstrained multi-word search queries (10/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0156` | T3 | **FAIL** | 9 | `Drift-4528` | `` | `doc-0105` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0157` | T3 | **FAIL** | 12 | `Drift-4553` | `` | `doc-0110` | `` | Model issued overconstrained multi-word search queries (6/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0158` | T3 | **FAIL** | 12 | `Cobalt-4577` | `` | `doc-0115` | `` | Model issued overconstrained multi-word search queries (10/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0159` | T3 | **FAIL** | 11 | `Alto-4600` | `` | `doc-0120` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0160` | T3 | **FAIL** | 4 | `Ferro-4629` | `` | `doc-0125` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0161` | T3 | **FAIL** | 4 | `Ferro-4654` | `` | `doc-0130` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0162` | T3 | **FAIL** | 1 | `Ferro-4679` | `` | `doc-0135` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0163` | T3 | **FAIL** | 11 | `Basalt-4701` | `` | `doc-0140` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0164` | T3 | **FAIL** | 12 | `Alto-4725` | `` | `doc-0145` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0165` | T3 | **FAIL** | 10 | `Helix-4006` | `Wisp-4021` | `doc-0001` | `doc-0004` | Model traversed backwards to Xebec Labs (doc-0004) instead of target entity (doc-0001). | `MULTI_HOP_DIRECTION_ERROR` |
| `s-0166` | T3 | **FAIL** | 12 | `Helix-4031` | `` | `doc-0006` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0167` | T3 | **FAIL** | 12 | `Gossamer-4055` | `` | `doc-0011` | `` | Model traversed multiple valid intermediate hops but ran out of steps before completing chain. | `MULTI_HOP_TRAVERSAL_EXHAUSTION` |
| `s-0168` | T3 | **FAIL** | 4 | `Jade-4083` | `` | `doc-0016` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0169` | T3 | **FAIL** | 4 | `Gossamer-4105` | `` | `doc-0021` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0170` | T3 | **FAIL** | 11 | `Jade-4133` | `` | `doc-0026` | `` | Upstream API server error (HTTP 500: Internal Server Error) interrupted agent execution. | `INFRASTRUCTURE_SERVER_ERROR` |
| `s-0171` | T3 | **FAIL** | 12 | `Gossamer-4155` | `` | `doc-0031` | `` | Model issued overconstrained multi-word search queries (11/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0172` | T3 | **FAIL** | 12 | `Jade-4183` | `` | `doc-0036` | `` | Model issued overconstrained multi-word search queries (7/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0173` | T3 | **FAIL** | 12 | `Indigo-4207` | `` | `doc-0041` | `` | Model issued overconstrained multi-word search queries (10/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0174` | T3 | **FAIL** | 12 | `Kelvin-4234` | `` | `doc-0046` | `` | Upstream API server error (HTTP 500: Internal Server Error) interrupted agent execution. | `INFRASTRUCTURE_SERVER_ERROR` |
| `s-0175` | T3 | **FAIL** | 2 | `Helix-4256` | `` | `doc-0051` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0176` | T3 | **FAIL** | 3 | `Indigo-4282` | `` | `doc-0056` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0177` | T3 | **FAIL** | 1 | `Gossamer-4305` | `` | `doc-0061` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0178` | T3 | **FAIL** | 1 | `Helix-4331` | `` | `doc-0066` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0179` | T3 | **FAIL** | 1 | `Helix-4356` | `` | `doc-0071` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0180` | T3 | **FAIL** | 12 | `Helix-4381` | `` | `doc-0076` | `` | Model issued overconstrained multi-word search queries (8/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0181` | T3 | **FAIL** | 12 | `Jade-4408` | `` | `doc-0081` | `` | Model issued overconstrained multi-word search queries (8/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0182` | T3 | **FAIL** | 12 | `Kelvin-4434` | `` | `doc-0086` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0183` | T3 | **FAIL** | 12 | `Jade-4458` | `` | `doc-0091` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0184` | T3 | **FAIL** | 12 | `Helix-4481` | `` | `doc-0096` | `` | Model issued overconstrained multi-word search queries (9/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0185` | T3 | **FAIL** | 2 | `Gossamer-4505` | `` | `doc-0101` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0186` | T3 | **FAIL** | 2 | `Indigo-4532` | `` | `doc-0106` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0187` | T3 | **FAIL** | 1 | `Indigo-4557` | `` | `doc-0111` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0188` | T3 | **FAIL** | 12 | `Gossamer-4580` | `` | `doc-0116` | `` | Model issued overconstrained multi-word search queries (9/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0189` | T3 | **FAIL** | 12 | `Gossamer-4605` | `` | `doc-0121` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0190` | T3 | **FAIL** | 12 | `Indigo-4632` | `` | `doc-0126` | `` | Model issued overconstrained multi-word search queries (7/12 returned 0 candidates), looping until step cap. | `OVERCONSTRAINED_SEARCH_LOOP` |
| `s-0191` | T3 | **FAIL** | 12 | `Kelvin-4659` | `` | `doc-0131` | `` | Model traversed multiple valid intermediate hops but ran out of steps before completing chain. | `MULTI_HOP_TRAVERSAL_EXHAUSTION` |
| `s-0192` | T3 | **FAIL** | 12 | `Helix-4681` | `` | `doc-0136` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0193` | T3 | **FAIL** | 3 | `Indigo-4707` | `` | `doc-0141` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0194` | T3 | **FAIL** | 1 | `Indigo-4732` | `` | `doc-0146` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0195` | T3 | **FAIL** | 1 | `Nyx-4012` | `` | `doc-0002` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0196` | T3 | **FAIL** | 1 | `Onyx-4038` | `` | `doc-0007` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0197` | T3 | **FAIL** | 1 | `Nyx-4062` | `` | `doc-0012` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0198` | T3 | **FAIL** | 1 | `Nyx-4087` | `` | `doc-0017` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0199` | T3 | **FAIL** | 1 | `Onyx-4113` | `` | `doc-0022` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
| `s-0200` | T3 | **FAIL** | 1 | `Nyx-4137` | `` | `doc-0027` | `` | Upstream API rate limit error (HTTP 429: Too Many Requests) interrupted agent execution. | `INFRASTRUCTURE_RATE_LIMIT` |
