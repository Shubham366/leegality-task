import logging
import os

import click
import uvicorn
from uvicorn.config import LOGGING_CONFIG

logging.basicConfig(level=logging.INFO)

from core.config import config

LOG_CONFIG = {
    **LOGGING_CONFIG,
    "root": {"handlers": ["default"], "level": "INFO"},
}


@click.command()
def main():
    uvicorn.run(
        "api.server:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=True if config.ENV != "prod" else False,
        log_config=LOG_CONFIG,
    )


if __name__ == "__main__":
    main()
