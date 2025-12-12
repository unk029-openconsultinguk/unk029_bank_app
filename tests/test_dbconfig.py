def test_database_config_validate_true():
    from unk029.database import DatabaseConfig

    cfg = DatabaseConfig(user="user", password="pass", dsn="dsn")
    assert cfg.validate() is True


def test_database_config_validate_false():
    from unk029.database import DatabaseConfig

    cfg = DatabaseConfig(user=None, password=None, dsn=None)
    assert cfg.validate() is False
