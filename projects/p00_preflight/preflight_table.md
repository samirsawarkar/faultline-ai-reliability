| Rung | Model | Endpoint | Status | Version | Latency (ms) | Temp-0 Deterministic | In/Out Price ($/1M) | Est/Meas USD |
|---|---|---|---|---|---|---|---|---|
| R1 | gemini-2.5-flash-lite | `gemini/gemini-2.5-flash-lite` | FAILED | FAILED: APIConnectionError: litellm.APIConnectionError: Missing Gemini API key. Set the  | 19.3 | N/A (failed) | $0.10 / $0.40 | N/A |
| R2 | deepseek-v4-flash | `deepseek/deepseek-chat` | FAILED | FAILED: AuthenticationError: litellm.AuthenticationError: AuthenticationError: DeepseekE | 236.3 | N/A (failed) | $0.14 / $0.28 | N/A |
| R3 | deepseek-v4-pro | `deepseek/deepseek-reasoner` | FAILED | FAILED: AuthenticationError: litellm.AuthenticationError: AuthenticationError: DeepseekE | 161.3 | N/A (failed) | $0.43 / $0.87 | N/A |
| R4 | minimax-m3 | `minimax/minimax-m3` | FAILED | FAILED: APIConnectionError: litellm.APIConnectionError: MinimaxException - {"type":"erro | 490.7 | N/A (failed) | $0.60 / $2.40 | N/A |
| R5 | glm-5.2 | `zhipu/glm-5.2` | FAILED | FAILED: BadRequestError: litellm.BadRequestError: LLM Provider NOT provided. Pass in the | 8.8 | N/A (failed) | $1.40 / $4.40 | N/A |
| R6 | claude-3-5-sonnet-20241022 | `anthropic/claude-3-5-sonnet-20241022` | FAILED | FAILED: AuthenticationError: litellm.AuthenticationError: Missing Anthropic API Key - A  | 20.0 | N/A (failed) | $3.00 / $15.00 | N/A |
