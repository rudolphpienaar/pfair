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
import  pypx

import  pathlib
import  sys
import  time
from    loguru                  import logger
LOG             = logger.debug

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

class Log:
    """
    """

def noop():
    """
    A dummy function that does nothing.
    """
    return {
        'status':   True
    }

def save(
        payload             : sensorModel.sensorStructured,
        request             : Request
) -> dict:
    """
    Parse the incoming payload, and write appropriate
    information to some storage resource.

    The "directory" analogous organization:

        <DB>/<logObject>/<logCollection>/<event1>
                                        /<event2>
                                        /<event3>
                        ...
                                        /<eventN>


    Args:
        payload (sensorModel.sensorStructured): the load payload

    Returns:
        dict: the return verification object

    """
    timestamp = lambda : '%s' % datetime.now()
    list_logObjects         = \
        lambda      : config.dbAPI.telemetryService_listObjs()
    logCollection_exists  = \
        lambda      : config.dbAPI.DB.exists(payload.logCollection, path = str_logObjDir)
    logCollection_create  = \
        lambda      : config.dbAPI.DB.mkdir(str_collectionDir)
    logEvents_get = \
        lambda      : config.dbAPI.telemetryService_eventList(
                            payload.logObject,
                            payload.logCollection
                    )
    logEvent_load       = \
        lambda      : config.dbAPI.DB.cat(str_logEventPath)
    logEvent_write      = \
        lambda x    : config.dbAPI.DB.touch(str_logEventPath, x)
    logEvent_commit     = \
        lambda      : config.dbAPI.DB.node_save('',
                            startPath       = str_collectionDir,
                            pathDiskRoot    = '%s' % (
                                config.dbAPI.str_FSprefix,
                            ),
                            failOnDirExist  = False
                    )
    logEvent_getCSV = \
        lambda x    : config.dbAPI.telemetryService_dictAsCSV(
                        config.dbAPI.telemetryService_event(
                            payload.logObject,
                            payload.logCollection,
                            x
                        ), separator = '│', applyPadding = True
        )
    logEvent_logObjectCreate = \
        lambda name, info    : internalObject_initOrUpdate(name, info)


    d_logEvent:dict      = {
        '_id'               : -1,
        '_timestamp'        : timestamp(),
        'appName'           : payload.appName,
        'execTime'          : payload.execTime,
        'requestHost'       : request.client.host,
        'requestPort'       : str(request.client.port),
        'requestUserAgent'  : request.headers['user-agent'],
        'payload'           : payload.payload
    }
    d_ret:dict          = {
        'log'               : d_logEvent,
        'status'            : False,
        'timestamp'         : d_logEvent['_timestamp'],
        'message'           :
            f"Nothing was saved -- logObject '{payload.logObject}' doesn't exist. Create with an appropriate PUT request!"
    }
    d_ret['log']['_id']     = '%03d'    % len(logEvents_get())
    str_logObjDir:str       = '%s/%s'   % (config.dbAPI.dobj_DB.DB, payload.logObject)
    str_collectionDir:str   = '%s/%s'   % (str_logObjDir, payload.logCollection)
    str_logEvent:str        = '%s-%s'   % (d_ret['log']['_id'], payload.logEvent)
    str_logEventPath:str    = '%s/%s'   % (str_collectionDir, str_logEvent)

    if not payload.logObject in list_logObjects():
        logSetup:sensorModel.sensorCore   = sensorModel.sensorCore()
        logSetup.description        = 'Automatically generated object'
        logEvent_logObjectCreate(payload.logObject, logSetup)

    d_existingLog:dict      = {}
    if not logCollection_exists():
        logCollection_create()
    d_existingLog.update(d_logEvent)
    logEvent_write(d_existingLog)
    logEvent_commit()
    d_ret['status'] = True
    d_ret['message'] = f"Saved log {str_logEventPath}"
    LOG(logEvent_getCSV(str_logEvent).replace('\n', ''))
    return d_ret

def slog_save(
    payload     : sensorModel.sensorSimple,
    request     : Request,
    **kwargs
) -> dict:
    """Save an slog payload

    Args:
        payload (sensorModel.sensorSimple): a payload to log

    Returns:
        dict: the return verification object
    """
    object:str                              = 'default'
    collection:str                          = 'default'
    event:str                               = 'log'
    for k,v in kwargs.items():
        if k == 'object'                    : object        = v
        if k == 'collection'                : collection    = v
        if k == 'event'                     : event         = v
    sensorStructured:sensorModel.sensorStructured    = sensorModel.sensorStructured()
    sensorStructured.logObject                 = object
    sensorStructured.logCollection             = collection
    sensorStructured.appName                   = 'slog'
    sensorStructured.execTime                  = -1.0
    sensorStructured.logEvent                  = event
    sensorStructured.payload                   = payload.log
    return save(sensorStructured, request)

def internalObject_initOrUpdate(
        logObj:str,
        d_data:sensorModel.sensorCore
) -> sensorModel.sensorInit:
    """Create a new (or made updates to a) log object.

    Args:
        logObj (str): Log Object to create or update

    Returns:
        sensorModel.logResponse: create/update response
    """
    d_ret:dict = config.dbAPI.telemetryService_initObj(
        logObj, d_data
    )
    LOG(d_ret['message'])
    return d_ret

def internalObjects_getList() -> list:
    """
    Return a list of internal object names
    """
    return list(config.dbAPI.telemetryService_listObjs())

def internalObject_getInfo(
            objName:str
) -> dict:
    """
    Return a dictionary representation of a single PACS object
    """
    return dict(config.dbAPI.telemetryService_info(objName))

def internalObject_getCollections(
            objName:str
) -> list:
    """
    Return a list representation of all the "collections" that
    exist for this object. A "collection" is a named grouping
    that houses all the logs from applications that together
    constitute some logical group -- for example all the apps
    is a given ChRIS feed could constitute one collection.
    """
    return config.dbAPI.telemetryService_collectionList(
        objName
    )

def internalObjectCollection_get(
            objName:str,
            collectionName:str
) -> list:
    """
    Return a list representation of all the "events" details
    for this collection.
    """
    return config.dbAPI.telemetryService_collectionGet(
        objName, collectionName
    )

def internalObjectCollection_delete(
            objName:str,
            collectionName:str
) -> dict:
    """
    Delete all the collection <collectionName> in object <objName>
    """
    d_ret:dict = {
        'status'    : config.dbAPI.telemetryService_collectionDel(
                                objName, collectionName
                    )
    }
    return d_ret

def internalObjectCollection_getCSV(
            objName:str,
            collectionName:str,
            **kwargs
) -> str:
    """
    Return a list representation of all the "events" details
    for this collection.
    """
    return config.dbAPI.telemetryService_collectionGetCSV(
        objName, collectionName, **kwargs
    )

def stats_describe(lstr_col:list) -> dict:
    """
    Describe and return some statistics on the passed list
    of strings. Note that all elements of the list, while
    strings, must be interpretable as floats.

    Args:
        lstr_col (list[str]): a list of strings corresponding to
                              a column in a table.

    Returns:
        dict: a description of the statistics of the numerical
              values in the <lstr_col>
    """
    d_ret:dict          = {}
    np_col:np.array[float]  = np.array([float(x) for x in lstr_col])
    des:np.DescribeResult   = stats.describe(np_col)
    d_ret       = {
                'sum'       : sum(np_col),
                'minmax'    : des.minmax,
                'mean'      : des.mean,
                'variance'  : des.variance,
                'nobs'      : des.nobs,
                'skewness'  : des.skewness,
                'kurtosis'  : des.kurtosis
    }
    return d_ret

def listTable_statsOnCol(ll_table, **kwargs) -> dict:
    """
    For a list (of lists) table, and a column to process in **kwargs,
    return a dictionary of stats on that column.
    """
    str_statsCol:str    = ''
    for k,v in kwargs.items():
        if k == 'column':  str_statsCol = v

    col:int             = 0
    d_ret:dict          = {
        'error' :       f'Column with header {str_statsCol} was not found in this collection'
    }
    l_header:list   = [x[0] for x in ll_table]
    try:
        col         = l_header.index(str_statsCol)
        d_ret       = stats_describe(ll_table[col][1:])
    except:
        pass
    return d_ret


def internalObjectCollection_getStats(
            objName:str,
            collectionName:str,
            **kwargs
) -> dict:
    """
    Return a dictionary representation describing the statistics over
    the events of a collection.
    """

    ll_table:list[list] = config.dbAPI.telemetryService_collectionGetMatrix(
        objName, collectionName, **kwargs
    )[collectionName]

    d_ret:dict          = {
        collectionName :    listTable_statsOnCol(ll_table, **kwargs)
    }

    return d_ret

def internalObject_getStats(
            objName:str,
            **kwargs
) -> dict:
    """
    Return a dictionary of dictionaries describing the statistics over
    all the collections in an object -- one dictionary key per collection.
    """

    d_ret   = {}
    for collection in internalObject_getCollections(objName):
        d_ret.update(internalObjectCollection_getStats(objName, collection, **kwargs))
    return d_ret

def internalObject_getStatsCumulative(
            objName:str,
            **kwargs
) -> dict:
    """
    Return a dictionary describing the statistics cumulated over
    all the collections in an object.
    """

    d_ret   = {
        'error':    "Object '%s' not found!" % objName
    }
    d_tableCollection:dict          = {}
    ll_tableCumulative:list[list]   = []
    colCount:int                    = 0
    for collection in internalObject_getCollections(objName):
        d_tableCollection   = config.dbAPI.telemetryService_collectionGetMatrix(
            objName, collection, **kwargs
        )
        if not len(ll_tableCumulative):
            ll_tableCumulative  = d_tableCollection[collection].copy()
        else:
            colCount    = 0
            ll_tableCumulative = [colCumulative + colCollected[1:] \
                    for colCumulative,colCollected in \
                        zip(ll_tableCumulative, d_tableCollection[collection])]
    if len(ll_tableCumulative):
        d_ret = {
            objName     : listTable_statsOnCol(ll_tableCumulative, **kwargs)
        }
    return d_ret

def internalObjectCollection_getEvents(
            objName:str,
            collectionName:str
) -> list:
    """
    Return a list representation of all the "events" that
    exist for this collection. An "event" is the atomic element
    in the logger universe, and is the actual telemetry data
    transmitted by an application, for instance an application
    in a given ChRIS feed.
    """
    return config.dbAPI.telemetryService_eventList(
        objName, collectionName
    )

def internalObjectCollection_getEvent(
            objName:str,
            collectionName:str,
            eventName:str
) -> dict:
    """
    Return the "raw" (JSON) telemetry data that was transmitted
    by an event.
    """
    return config.dbAPI.telemetryService_event(
        objName, collectionName, eventName
    )
