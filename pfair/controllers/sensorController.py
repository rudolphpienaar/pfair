str_description = """
    This module contains logic pertinent to the PACS setup "subsystem"
    of the `pfdcm` service.
"""

from    concurrent.futures  import  ProcessPoolExecutor, ThreadPoolExecutor, Future

from    fastapi             import  APIRouter, Query, Request
from    fastapi.encoders    import  jsonable_encoder
from    fastapi.concurrency import  run_in_threadpool
from    pydantic            import  BaseModel, Field
from    typing              import  Optional, List, Dict, Callable, Any

import  numpy               as      np
from    scipy               import  stats

from    .jobController      import  jobber
import  asyncio
import  subprocess
from    models              import  sensorModel
import  logging
import  os
from    datetime            import  datetime

import  pudb
from    pudb.remote         import set_trace
import  config
import  json

from    persair.persair     import  Persair, parser_interpret

import  pathlib
import  sys
import  time
from    loguru              import logger
LOG                         = logger.debug

logger_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> │ "
    "<level>{level: <5}</level> │ "
    "<yellow>{name: >28}</yellow>::"
    "<cyan>{function: <30}</cyan> @"
    "<cyan>{line: <4}</cyan> ║ "
    "<level>{message}</level>"
)
logger.remove()
logger.opt(colors = True)
logger.add(sys.stderr, format=logger_format)
LOG     = logger.info


threadpool: ThreadPoolExecutor      = ThreadPoolExecutor()
processpool: ProcessPoolExecutor    = ProcessPoolExecutor()

async def data_get(id:int) -> dict:
    pudb.set_trace()
    sensors:Persair         = Persair({
                "sensorDataGet":    id
            })
    await sensors.service()
    return sensors.responseData
