import pytest
from faultline_p2.agent.model import LiteLLMModel

def test_litellm_seam_would_send():
    model = LiteLLMModel("gpt-4", "openai", "1.0")
    messages = [{"role": "user", "content": "hello"}]
    
    with pytest.raises(RuntimeError) as exc_info:
        model.generate(messages)
        
    assert "LiteLLM Seam Not Invoked" in str(exc_info.value)
    
    # Check the kwargs it WOULD have sent
    kwargs = exc_info.value.args[1]
    assert kwargs["model"] == "gpt-4"
    assert kwargs["temperature"] == 0.0
    assert kwargs["max_tokens"] == 2048
    assert kwargs["messages"] == messages
