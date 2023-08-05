str_description = """
    This route module handles sensoric pertaining to associating
    routes to actual logic in the controller module. For the
    most part, this module mostly has route method defintions
    and UI swagger for documentation.

    In most methods, the actual logic is simply a call out
    to the real method in the controller module that performs
    the application logic as well as any surface contact with
    the DB module/service.
"""


from    fastapi             import  APIRouter, Query, HTTPException, BackgroundTasks, Request
from    fastapi.encoders    import  jsonable_encoder
from    typing              import  List, Dict

from    models              import  sensorModel
from    controllers         import  sensorController

from    datetime            import datetime, timezone
import  pudb

router          = APIRouter()
router.tags     = ['sensorger services']

@router.put(
    "/sensor/{sensorObj}/",
    response_model  = sensorModel.sensorInit,
    summary         = "PUT information to a (possibly new) pftel object"
)
async def sensorSetup_put(
    sensorObj          : str,
    sensorSetupData    : sensorModel.sensorCore
) -> sensorModel.sensorInit:
    """
    Description
    -----------
    PUT an entire object. If the object already exists, overwrite.
    If it does not exist, append to the space of available objects.
    """
    return sensorController.internalObject_initOrUpdate(
        sensorObj, sensorSetupData
    )

@router.post(
    '/ssensor/',
    response_model  = sensorModel.sensorResponse,
    summary         = '''
    Use this API route to POST a simple sensor payload to the
    sensorger.
    '''
)
async def ssensor_write(
    sensorPayload      : sensorModel.sensorSimple,
    request         : Request,
    sensorObject       : str   = 'default',
    sensorCollection   : str   = 'ssensor',
    sensorEvent        : str   = 'sensor'
) -> sensorModel.sensorResponse:
    """
    Description
    -----------

    Use this API entry point to simply record some sensor string.
    `ssensor` entries are by default sensorged to `default/ssensor/<count>-sensor`
    but this can be overriden with appropriate query parameters.

    ```
    {
        sensor  : str   = ""
    }
    ```

    Internally, they are mapped to a complete *telemetry* model for
    consistent processing.

    """
    # pudb.set_trace()
    d_ret:sensorModel.sensorResponse = sensorController.ssensor_save(
        sensorPayload,
        request,
        object      = sensorObject,
        collection  = sensorCollection,
        event       = sensorEvent)
    return d_ret


@router.post(
    '/sensor/',
    response_model  = sensorModel.sensorResponse,
    summary         = '''
    Use this API route to POST a telemetry conforming payload to the
    sensorger.
    '''
)
async def sensor_write(
    sensorPayload      : sensorModel.sensorStructured,
    request         : Request
) -> sensorModel.sensorResponse:
    """
    Description
    -----------

    Use this API entry-point to sensor a *telemetry* record called `{sensorEvent}`
    to a given `{sensorObject}`/`{sensorCollection}`:

    ```
    {
        sensorObject       : str   = "default"
        sensorCollection   : str   = ""
        sensorEvent        : str   = ""
        appName         : str   = ""
        execTime        : float = 0.0
        payload         : str   = ""
    }
    ```

    In order to "read" telemetry sensors, perform an appropriate GET request.

    """
    # pudb.set_trace()
    d_ret:sensorModel.sensorResponse = sensorController.save(sensorPayload, request)
    return d_ret

@router.get(
    "/sensor/",
    response_model  = List,
    summary         = """
    GET the list of configured sensor element objects
    """
)
async def sensorList_get() -> list:
    """
    Description
    -----------
    GET the list of configured sensor element objects handlers.
    These objects constitute the most general level of sensor aggregation.
    At this level, each handler can be thought of as a handler for a
    large group of sensorging collections.
    """
    return sensorController.internalObjects_getList()

@router.get(
    "/sensor/{sensorObject}/info/",
    response_model  = sensorModel.sensorInit,
    summary         = "GET the meta information for a given sensor object"
)
async def sensorInfo_getForObject(
    sensorObject: str
) -> dict:
    """
    Description
    -----------
    GET the setup info pertinent to a sensor object element called `sensorName`.
    """
    return sensorController.internalObject_getInfo(sensorObject)

@router.get(
    "/sensor/{sensorObject}/collections/",
    response_model  = List,
    summary         = """
    GET the collections that constitute this sensor object
    """
)
async def sensorCollections_getForObject(
    sensorObject: str
) -> list:
    """
    Description
    -----------
    GET the list of collections in `sensorObject`. A _collection_ gathers
    a set of events. For instance, a _collection_ called **02Feb2024** could
    collect all events from the 2nd Feb 2024.
    """
    return sensorController.internalObject_getCollections(sensorObject)

@router.get(
    "/sensor/{sensorObject}/{sensorCollection}/events/",
    response_model  = List,
    summary         = """
    GET the events that exist in the sensor object collection.
    """
)
async def sensorEvents_getForObjectCollection(
    sensorObject:str,
    sensorCollection:str
) -> list:
    """
    Description
    -----------
    GET the list of events that have sent telemtryto the `sensorCollection`
    of `sensorObject`.
    """
    return sensorController.internalObjectCollection_getEvents(
        sensorObject,
        sensorCollection
    )

@router.get(
    "/sensor/{sensorObject}/{sensorCollection}/{sensorEvent}/",
    response_model  = Dict,
    summary         = """
    GET a specific event that exists in this sensor object collection.
    """
)
async def sensorEvent_getForObjectCollection(
    sensorObject:str,
    sensorCollection:str,
    sensorEvent:str
) -> dict:
    """
    Description
    -----------
    GET the specific details of event `sensorEvent` in the collection
    `sensorCollection` of the object `sensorObject`.
    """
    return sensorController.internalObjectCollection_getEvent(
        sensorObject,
        sensorCollection,
        sensorEvent
    )


@router.delete(
    "/sensor/{sensorObject}/{sensorCollection}/",
    response_model  = sensorModel.sensorDelete,
    summary         = """
    DELETE all the events comprising this sensor object.
    """
)
async def sensor_getForObjectCollection(
    sensorObject:str,
    sensorCollection:str
) -> bool:
    """
    Description
    -----------
    DELETE all the events in the collection `sensorCollection` of the object
    `sensorObject`. Use with care!
    """
    return sensorController.internalObjectCollection_delete(
        sensorObject,
        sensorCollection
    )

@router.get(
    "/sensor/{sensorObject}/{sensorCollection}/",
    response_model  = List,
    summary         = """
    GET all the events comprising this sensor object collection as
    a list of JSON objects.
    """
)
async def sensor_getForObjectCollection(
    sensorObject:str,
    sensorCollection:str
) -> list:
    """
    Description
    -----------
    GET all the events in the collection `sensorCollection` of the object
    `sensorObject` as a JSON return.
    """
    return sensorController.internalObjectCollection_get(
        sensorObject,
        sensorCollection
    )

@router.get(
    "/sensor/{sensorObject}/{sensorCollection}/csv",
    response_model  = str,
    summary         = """
    GET all the events comprising this sensor object collection as
    a CSV formatted string
    """
)
async def sensor_getForObjectCollectionAsCSV(
    sensorObject:str,
    sensorCollection:str,
    style:str       = 'plain',
    padding:bool    = False,
    fields:str      = ''
) -> str:
    """
    Description
    -----------
    GET all the events in the collection `sensorCollection` of the object
    `sensorObject` as a CSV formatted string.

    By passing a URL query as `style=fancy` a _fancy_ CSV payload is
    returned. Passing a comma-separated string of `fields=<strlist>`
    will only return the `strlist` tokens in the CSV.
    """
    # pudb.set_trace()
    return sensorController.internalObjectCollection_getCSV(
        sensorObject,
        sensorCollection,
        format          = style,
        applyPadding    = padding,
        fields          = fields
    )

@router.get(
    "/sensor/{sensorObject}/{sensorCollection}/stats",
    response_model  = dict,
    summary         = """
    GET stats on the specified sensor object collection. The column to
    process is specified in the optional query parameter.
    """
)
async def sensor_getStatsForObjectCollection(
    sensorObject:str,
    sensorCollection:str,
    key:str         = 'execTime',
) -> dict:
    """
    Description
    -----------
    GET statistics on all the events in the collection `sensorCollection` of
    the object `sensorObject`.

    The URL query `key=<key>` specifies the actual key field in the event
    collection to process. This field key must contain numeric values.
    """
    # pudb.set_trace()
    return sensorController.internalObjectCollection_getStats(
        sensorObject,
        sensorCollection,
        column          = key
    )

@router.get(
    "/sensor/{sensorObject}/stats",
    response_model  = dict,
    summary         = """
    GET stats on the specified sensor object collection. The column to
    process is specified in the optional query parameter. A dictionary
    of keys where each key is one object collection is returned.
    """
)
async def sensor_getStatsForObject(
    sensorObject:str,
    key:str         = 'execTime',
) -> dict:
    """
    Description
    -----------
    GET a dictionary keyed on collections of all the collections events
    of object `sensorObject`. The stats of each collection are returned without
    further processing.

    The URL query `key=<key>` specifies the actual key field in the event
    collection to process. This field key must contain numeric values.
    """
    # pudb.set_trace()
    return sensorController.internalObject_getStats(
        sensorObject,
        column          = key
    )

@router.get(
    "/sensor/{sensorObject}/stats_process",
    response_model  = dict,
    summary         = """
    GET processed stats on the entire specified sensor object collection. The
    column to process is specified in the optional query parameter.
    """
)
async def sensor_processStatsForObject(
    sensorObject:str,
    key:str         = 'execTime',
) -> dict:
    """
    Description
    -----------
    GET a processed result of all the events in all the collections
    of object `sensorObject`. A single dictionary `allCollections` is returned.

    The URL query `key=<key>` specifies the actual key field in the event
    collection to process. This field key must contain numeric values.
    """
    # pudb.set_trace()
    return sensorController.internalObject_getStatsCumulative(
        sensorObject,
        column          = key
    )

