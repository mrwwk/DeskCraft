import logging
from desktop_env.providers.aws.proxy_pool import get_global_proxy_pool

logger = logging.getLogger("utils.taiji_proxy")

def initialize_taiji_proxy_pool(host: str, port: int, protocol: str):
    # Initialize proxy pool with given proxy (for VM to access external websites)
    proxy_pool = get_global_proxy_pool()
    proxy_pool.add_proxy(
        host=host,
        port=port,
        protocol=protocol
    )
    logger.info("Proxy pool initialized with given proxy: {host}:{port}")
    