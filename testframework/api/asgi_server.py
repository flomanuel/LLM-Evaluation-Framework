#  Copyright (c) 2026 Florian Emanuel Sauer
#
#  This source code is licensed under the MIT license found in the
#  LICENSE file in the root directory of this source tree.

import os

import uvicorn


def run() -> None:
    """Start the API with the uvicorn ASGI server."""
    host = os.environ.get("API_HOST", "127.0.0.1")
    port = int(os.environ.get("API_PORT", "8000"))
    uvicorn.run(
        "testframework.api:app",
        host=host,
        port=port,
        loop="asyncio",
        http="h11",
        interface="asgi3",
    )
