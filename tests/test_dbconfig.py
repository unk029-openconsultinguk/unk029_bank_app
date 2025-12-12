def test_database_config_validate_true():
    from unk029.database import DatabaseConfig

    cfg = DatabaseConfig(user="user", password="pass", dsn="dsn")
    assert cfg.validate() is True


def test_database_config_validate_false():
    from unk029.database import DatabaseConfig

    # Pass empty strings to avoid picking up environment variables during CI
    cfg = DatabaseConfig(user="", password="", dsn="")
    assert cfg.validate() is False
