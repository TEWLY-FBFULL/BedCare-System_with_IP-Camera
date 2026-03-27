from app.models.system_config import SystemConfig

class ConfigCache:
    _cache = {}
    @classmethod
    def get(cls, key, default=None):
        return cls._cache.get(key, default)

    @classmethod
    def refresh(cls, db):
        configs = db.query(SystemConfig).all()
        cls._cache = {c.config_key: c.config_value for c in configs}