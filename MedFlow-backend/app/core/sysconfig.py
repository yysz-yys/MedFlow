"""业务配置读取（从 system_config 表，启动时缓存到内存）"""
from sqlalchemy import select
from app.core.database import async_session
from app.models.system_config import SystemConfig

_cache: dict = {}

async def load_sysconfig():
    """启动时调用，全量加载 system_config 到内存缓存"""
    global _cache
    async with async_session() as db:
        result = await db.execute(select(SystemConfig))
        for row in result.scalars().all():
            _cache[row.config_key] = row.config_value
    print(f"  [sysconfig] loaded {len(_cache)} items")

def get(key: str, default: str = "") -> str:
    return _cache.get(key, default)

def get_int(key: str, default: int = 0) -> int:
    try: return int(_cache.get(key, ""))
    except: return default

async def refresh():
    """管理员修改配置后，刷新缓存"""
    await load_sysconfig()
