from hermes_telegram_overlay.model_config import ModelConfigError, build_model_config, validate_litellm_base_url


def test_validate_litellm_base_url_requires_v1():
    assert validate_litellm_base_url("http://127.0.0.1:4000/v1") == "http://127.0.0.1:4000/v1"

    try:
        validate_litellm_base_url("http://127.0.0.1:4000")
    except ModelConfigError:
        pass
    else:
        raise AssertionError("Expected ModelConfigError for base_url without /v1")


def test_build_model_config_sets_chat_completions():
    config = build_model_config("http://127.0.0.1:4000/v1")

    assert config["model"]["provider"] == "custom"
    assert config["model"]["api_mode"] == "chat_completions"
