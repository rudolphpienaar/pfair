str_description = """
    This route module provides routes that allow for interacting
    with the PurpleAir sensors.

    For the most part, this module mostly has route method defintions and UI
    swagger for documentation.

    In most methods, the actual logic is simply a call out to the real method
    in the controller module that performs the application logic as well as any
    surface contact with the DB module/service. """


from    fastapi             import  APIRouter, Query, HTTPException, BackgroundTasks, Request
from    fastapi.encoders    import  jsonable_encoder
from    typing              import  List, Dict

from    models              import  sensorModel
from    controllers         import  sensorController

from    datetime            import datetime, timezone
import  pudb

router          = APIRouter()
router.tags     = ['sensor services']


@router.get(
    "/sensor/data/{id}",
    response_model  = List,
    summary         = """
    GET the sensor data for sensor {id}
    """
)
async def sensorData_get(id:int) -> dict:
    """
    Description
    -----------
    GET the data for sensor with id `id`.
    """
    pudb.set_trace()
    return await sensorController.data_get(id)

