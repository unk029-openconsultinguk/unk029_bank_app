def test_database_config_validate_true() -> None:
    from unk029.database import DatabaseConfig

    cfg = DatabaseConfig(user="user", password="pass", dsn="dsn")
    assert cfg.validate() is True


def test_database_config_validate_false() -> None:
    import os

    # Ensure environment variables are not present so defaults are missing
    os.environ.pop("ORACLE_USER", None)
    os.environ.pop("ORACLE_PASSWORD", None)
    os.environ.pop("ORACLE_DSN", None)

    from unk029.database import DatabaseConfig

    cfg = DatabaseConfig(user=None, password=None, dsn=None)
    assert cfg.validate() is False
