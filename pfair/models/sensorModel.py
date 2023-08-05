str_description = """

    The data models/schemas for the PACS QR collection.

"""

from    pydantic            import BaseModel, Field
from    typing              import Optional, List, Dict
from    datetime            import datetime
from    enum                import Enum
from    pathlib             import Path
import  pudb


class sensorCore(BaseModel):
    """Model for the core sensor info saved to DB"""
    url                                 : str = "http://localhost:2223"
    username                            : str = "any"
    password                            : str = "any"
    dbDir                               : str = "/home/dicom"
    telemetryDir                        : str = "telemetry"
    description                         : str = "Add a description!"

class sensorFile(BaseModel):
    """Model for the sensor file"""
    path                                : Path
    filename                            : str

class sensorSimple(BaseModel):
    """The simplest sensor model POST"""
    sensor                                 : str   = ""

class sensorStructured(BaseModel):
    """A simple structured sensor model"""
    sensorObject                           : str   = "default"
    sensorCollection                       : str   = ""
    sensorEvent                            : str   = ""
    appName                             : str   = ""
    execTime                            : float = 0.0
    requestHost                         : str   = ""
    requestPort                         : str   = ""
    requestUserAgent                    : str   = ""
    payload                             : str   = ""

class sensorPadding(Enum):
    _id                                 : int   = 5
    _timestamp                          : int   = 26
    appName                             : int   = 20
    execTime                            : int   = 10
    requestHost                         : int   = 40
    requestPort                         : int   = 12
    requestUserAgent                    : int   = 65
    payload                             : int   = 60

class sensorFormatting(Enum):
    _id                                 : str   = "int"
    _timestamp                          : str   = "str"
    appName                             : str   = "str"
    execTime                            : str   = "float"
    requestHost                         : str   = "str"
    requestPort                         : str   = "str"
    requestUserAgent                    : str   = "str"
    payload                             : str   = "str"

class sensorDelete(BaseModel):
    status                              : bool  = False

class sensorBoolReturn(BaseModel):
    status                              : bool  = False

class sensorResponse(BaseModel):
    """A model returned a sensor is POSTed"""
    sensor                                 : dict
    status                              : bool
    timestamp                           : str
    message                             : str

class time(BaseModel):
    """A simple model that has a time string field"""
    time            : str

class sensorInit(BaseModel):
    """
    A full model that is returned from a query call
    """
    info            : sensorCore
    time_created    : time
    time_modified   : time
    message         : str

# Some "helper" classes
class ValueStr(BaseModel):
    value           : str = ""