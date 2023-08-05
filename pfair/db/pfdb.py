from math import dist
from    typing              import Any, List, TypedDict, Collection
from h11 import Data
from    pydantic            import BaseModel, Field

import  json
from    datetime            import datetime
from    pathlib             import Path


from    pfstate             import S
from    pfmisc.C_snode      import C_stree
from    models              import sensorModel
from    config              import settings
import  sys
import  shutil
import  pudb

from    pymongo             import MongoClient
from    pymongo.database    import Database

class PFdb_mongo():
    """
    A mongo DB wrapper/interface object
    """

    def APIkeys_readFromFile(self, keyName:str) \
        -> dict[str, bool | str | dict[str, dict[Any, Any]]]:
        """
        Read a read/write key pair from a named <keyName> in
        the db init file (if it exists).

        Args:
            keyName (str): the key name to read in the db init.

        Return
            dict[str, bool | dict[Any, Any]]: The Read/Write key pair with
                                              bool 'status'
        """
        d_keys:dict     =   {
            'status'    : False,
            'message'   : 'DB init file not found.',
            'init':     {
                'keys'  : {}
            },
            'keyName'   : keyName
        }
        d_data:dict     = {}
        if not self.keyInitPath.is_file():
            return d_keys
        with open(str(self.keyInitPath), 'r') as f:
            try:
                d_data:dict = json.load(f)
                if keyName in d_data:
                    d_data[keyName]['readwritekeys']  = keyName
                    d_keys['status']        = True
                    d_keys['init']['keys']  = d_data[keyName]
                    d_keys['message']       = f'<keyName> "{keyName}" successfully loaded.'
                else:
                    d_keys['message']   = f'Init data does not have <keyName> {keyName}.'
            except:
                d_keys['message']   = f'Could not interpret key file {self.keyInitPath}.'
        return d_keys

    def Mongo_connectDB(self, DBname:str) -> dict[str, bool | Database[Any]]:
        """
        Connect / create the DB.

        Args:
            DBname (str): the DB name

        Returns:
            dict[str, bool | Database[Any]]: DB -- the database
                                             bool -- False if DB is not yet created
        """
        b_status:bool       = True
        DB: Database[Any]   = self.Mongo[DBname]
        d_ret:dict  = {
            'status':   b_status,
            'DB':       DB
        }
        l_dbnames: List[str]   = self.Mongo.list_database_names()
        if DBname not in l_dbnames:
            d_ret['status'] = False
        return d_ret

    def Mongo_connectCollection(self, mongocollection:str) -> dict[str, bool | Collection[Any]]:
        l_collections:list          = self.DB.list_collection_names()
        b_status:bool               = True
        collection: Collection[Any] = self.DB[mongocollection]
        d_ret:dict  = {
            'status':       b_status,
            'collection':   collection
        }
        if mongocollection not in l_collections:
            d_ret['status']     = False
        return d_ret

    def readwriteKeys_inCollectionGet(self, d_readwrite:dict, collectionExists:bool):
        if not collectionExists:
            self.collection.insert_one(d_readwrite['init']['keys'])
        d_collectionData    = self.collection.find_one({'readwritekeys': d_readwrite['keyName']})
        return d_collectionData

    def __init__(self, settingsKeys: settings.Keys, settingsMongo: settings.Mongo) -> None:
        pudb.set_trace()
        self.keyInitPath    = Path(settingsKeys.DBauthPath)
        self.Mongo          = MongoClient(settingsMongo.URI)

        # Read the API read/write keys from self.keyInitPath and ReadWriteKey collection
        # --- this is used only to instantiate the keys in the monogoDB
        d_readwrite: dict[str, bool | str | dict[Any, Any]] = \
            self.APIkeys_readFromFile(settingsKeys.ReadWriteKey)

        # Connect to the DB
        d_connectDB: dict[str, bool | Database[Any]]  = \
            self.Mongo_connectDB(settingsMongo.DB)
        self.DB: Database[Any] = d_connectDB['DB']

        # Connect to the collection
        d_collection: dict[str, bool | Collection[Any]] = \
            self.Mongo_connectCollection('sensors')
        self.collection: Collection[Any]     = d_collection['collection']

        self.keys = self.readwriteKeys_inCollectionGet(d_readwrite, d_collection['status'])

class DBstate(S):
    """

    All state data, i.e. trackers of information:

        * telemetry meta data

    are kept in this object

    """

    str_designNotes = """
            This module simulates some external data base service, used
            to save logging information to actual resources in the
            storage medium.

            Internally, the "db" is a pfstate object. There can be
            typically only one such object per namespace, so the db
            "wrapper" returns from this object in a manner that
            does not require the caller to understand this internal
            organization. This usage of pfstate is historical, and
            should probably be discouraged for future use.

    """
    str_apologies = """

            The idea with this module is to _simulate_ an external DB and
            design the system around that. All calls to any state information
            are thus routed through this module and should, in theory, be
            easily updated in future to an actual separate DB.

    """
    DB : str = '/DB/service'

    def __init__(self, *args, **kwargs):
        """
        An object to hold some generic/global-ish system state, in C_snode
        trees.

        Note that in C_snode trees, the paradigm for constructing a tree from
        a dictionary is interpreted to mean that any dictionary element is a
        tree branch and any dictionary value becomes a tree leaf at that branch.

        Thus, if storing a dictionary as a leaf is needed, then the model is to
        convert that dictionary to a JSON string and save that as a tree leaf.
        This protects the JSON dictionary from being expanded out to its own
        nested tree branch/leaf structure. Of course, remember then to interpret
        the JSON string back into a dictionary if needed by any access methods!
        """
        self.state_create(
        {
            'DB' :
            {
                'service':
                {
                    'default':
                    {
                        'json_created'   : json.dumps({'time' : '%s' % datetime.now()}),
                        'json_modified'  : json.dumps({'time' : '%s' % datetime.now()})
                    }
                }
            }
        },
        *args, **kwargs)

class PFdb_S():
    """
    An object that is meant to simulate interaction with some external
    (idiosyncratic) data base.

    Actual data is kept in the DBstate object, and this class
    provides a python API to manipulate data objects and
    and returns models of the objects where appropriate.

    The actual objects that contain data are never directly accessed
    by non db services.

    """

    # The DB object is stored directly in the class definition
    # and not in a per-object instance basis. There is afterall
    # only one DB per pfdcm session
    dobj_DB             = None

    # Data pertaining to the telemetry logger
    d_telemetryCore         : dict  = {
        'url':              'localhost:22223',
        'username':         'telemetry',
        'password':         'telemetry1234',
        'dbDir':            '/home/dicom',
        'telemetryDir':     'telemetry',
        'description':      'A telemetry object used to group together collections and events'
    }

    str_FSprefix    : str   = "%s/%s" % (d_telemetryCore['dbDir'], 'telemetry')

    def telemetryService_initObj(self,
            str_objName : str,
            d_data      : dict) -> dict:
        """
        Add (or update) information about a new (or existing) telemetry server
        to the service.
        """
        str_message     : str   = ""
        if str_objName not in self.telemetryService_listObjs():
            self.DB.mkdir('%s/%s'   % (DBstate.DB, str_objName))
            self.DB.touch(
                    '%s/%s/json_created'   % (DBstate.DB, str_objName),
                    json.dumps({'time' : '%s' % datetime.now()})
            )
            str_message     = "New object '%s' created" % str_objName
        else:
            str_message     = "Existing object '%s' modified" % str_objName

        self.DB.touch('%s/%s/info' % (DBstate.DB, str_objName), dict(d_data))
        self.DB.touch(
                '%s/%s/json_modified'     % (DBstate.DB, str_objName),
                json.dumps({'time' : '%s' % datetime.now()})
        )
        self.DB.node_save('',
                        startPath       = '%s/%s' % (DBstate.DB, str_objName),
                        pathDiskRoot    = self.str_FSprefix,
                        failOnDirExist  = False
        )
        return {
            'info'          : self.DB.cat(
                                '%s/%s/info'           % (DBstate.DB, str_objName)
                            ),
            'time_created'  : json.loads(self.DB.cat(
                                '%s/%s/json_created'   % (DBstate.DB, str_objName))
                            ),
            'time_modified' : json.loads(self.DB.cat(
                                '%s/%s/json_modified'  % (DBstate.DB, str_objName))
                            ),
            'message'       : str_message
        }


    def __init__(self, *args, **kwargs) -> None:
        """
        Constructor -- creates default data structures.

        Two "construction" possibilities exist:

        1. The _de novo_ mode, when this is the first time any telemetry is
        being managed. No other telemetry prior telemetry exists. In this case
        build an initial (mostly empty) DB, commit that, and continue.

        2. We are being constructed in an environment where previous telemetry
        exists. Perhaps a previous server crashed? Or a second telementry service
        is created on the same DB? Regardless, if previous artifacts are found,
        read from that DB into active memory.

        Note it is probably possible for multi-process/threading to collide, but
        the DB in external storage _should_ be ok with this.
        """
        self.str_loginName  = ''
        self.str_passwd     = ''
        # pudb.set_trace()
        for k,v in kwargs.items():
            if k == 'login' :   self.str_loginName  = v
            if k == 'passwd':   self.str_passwd     = v

        # Create the basic DB, mostly empty very first DB from the state object.
        PFdb.dobj_DB:DBstate        = DBstate(*args, **dict(kwargs, useGlobalState = True))
        # NB!!!! self.DB is separate from PFdb.dobj.DB.T!!!!
        self.DB:C_stree             = PFdb.dobj_DB.T

        self.telemetryService_initObj("default", PFdb.d_telemetryCore)
        # # Now add the default telemetry details
        # self.DB.touch(
        #     '%s/default/info' % DBstate.DB, PFdb.d_telemetryCore
        # )

        # With an instantiated DB, let's see if there isn't one already on storage
        # from some prior telemetry server.
        T_onDisk:C_stree            = C_stree.tree_load(pathDiskRoot = self.str_FSprefix)
        # If the size of this object is '48', then it is an empty tree and we save
        # our initial state out to storage and move on. Otherwise, we shift to using
        # this already-there DB.

        if len( '%s' % T_onDisk) < 10:
            self.DB.tree_save(startPath = '/', pathDiskRoot = self.str_FSprefix)
        else:
            self.DB                     = T_onDisk

    def telemetryService_listObjs(self)-> list:
        self.DB.cd(DBstate.DB)
        return list(self.DB.lstr_lsnode(DBstate.DB))

    def telemetryService_info(self, str_objName) -> dict:
        """
        Return a model conforming representation of a given
        log element object
        """
        if str_objName in self.telemetryService_listObjs():
            return {
                'info'          : self.DB.cat(
                                    '%s/%s/info'           % (DBstate.DB, str_objName)
                                ),
                'time_created'  : json.loads(self.DB.cat(
                                    '%s/%s/json_created'   % (DBstate.DB, str_objName))
                                ),
                'time_modified' : json.loads(self.DB.cat(
                                    '%s/%s/json_modified'  % (DBstate.DB, str_objName))
                                ),
                'message'       : "Service information for '%s'"        % str_objName
            }

    def telemetryService_collectionList(self, str_objName) -> list:
        """
        Return a list of "collections" for the passed log object
        """
        l_ret:list  = []
        if str_objName in self.telemetryService_listObjs():
            l_ret = list(self.DB.lstr_lsnode('%s/%s' % (DBstate.DB, str_objName)))
        l_ret.sort()
        return l_ret

    def telemetryService_eventList(self, str_objName, str_collectionName) -> list:
        """
        Return a list of "events" for the passed obj/collection
        """
        l_ret:list  = []
        if str_collectionName in self.telemetryService_collectionList(str_objName):
            l_ret = list(self.DB.lsf('%s/%s/%s' % (DBstate.DB, str_objName, str_collectionName)))
        l_ret.sort()
        return l_ret

    def telemetryService_event(self,
                str_objName,
                str_collectionName,
                str_eventName) -> dict:
        """
        Return a dictionary of the requested event for the passed
        obj/collection/event
        """
        d_ret:dict  = {}
        if str_eventName in self.telemetryService_eventList(str_objName, str_collectionName):
            d_ret = self.DB.cat('%s/%s/%s/%s' % (
                DBstate.DB, str_objName, str_collectionName, str_eventName)
            )
        return d_ret

    def telemetryService_collectionGet(self,
                str_objName,
                str_collectionName) -> list:
        """
        Return a list of "event" data for the passed obj/collection
        """
        l_ret:list  = [
            self.telemetryService_event(
                str_objName, str_collectionName, x
            ) for x in self.telemetryService_eventList(
                            str_objName, str_collectionName
                        )
        ]
        return l_ret

    def telemetryService_collectionDel(self,
                str_objName,
                str_collectionName) -> bool:
        """
        Delete the passed obj/collection from both internal memory
        and storage
        """
        self.DB.cd('/')
        b_ret:bool = self.DB.rm('%s/%s/%s' % (
            DBstate.DB, str_objName, str_collectionName
        ))
        shutil.rmtree('%s/%s/%s/%s' % \
                      (PFdb.str_FSprefix, DBstate.DB, str_objName, str_collectionName),
                      ignore_errors = True)
        return b_ret

    def telemetryService_padWidth(self,
                d_event:dict,
                **kwargs) -> list:
        """
        Return a list of either dictionary values or keys, padded
        according to corresponding enum classes in the model definition.

        By default the _values_ in the passed dictionary are padded
        and returned. To pad instead the _keys_ of the dictionary
        instead pass a

                use = 'keys'

        kwarg.

        Keep in mind this is a "row" dominant list across each row of
        a table!

        Args:
            d_event (dict): The dictionary event to pad

        Returns:
            list: A padded list of either the 'values' or 'keys'
        """
        str_use:str             = 'values'
        str_flush:str           = '─'
        for k,v in kwargs.items():
            if k == 'use':   str_use  = v
        d_paddedValues:dict     = {}
        d_paddedKeys:dict       = {}
        d_paddedFlush:dict      = {}
        for k,v in d_event.items():
            if logModel.logFormatting[k].value == 'int':
                d_paddedValues[k]   = "%0*d"    % (logModel.logPadding[k].value, int(v))
                d_paddedKeys[k]     = k.center(logModel.logPadding[k].value)
            if logModel.logFormatting[k].value == 'float':
                d_paddedValues[k]   = "%*.4f"   % (logModel.logPadding[k].value, float(v))
                d_paddedKeys[k]     = k.center(logModel.logPadding[k].value)
            if logModel.logFormatting[k].value == 'str':
                d_paddedValues[k]   = v.center(logModel.logPadding[k].value)
                d_paddedKeys[k]     = k.center(logModel.logPadding[k].value)
            d_paddedFlush[k]    = str_flush * logModel.logPadding[k].value
        if str_use == 'keys':
            return d_paddedKeys.values()
        elif str_use == 'flush':
            return d_paddedFlush.values()
        else:
            return d_paddedValues.values()

    def telemetryService_dictAsCSV(self,
                d_event:dict,
                **kwargs) -> str:
        """
        Convert either the values or keys of a dictionary into a CSV string,
        with options to pad this string to fixed width lengths.

        The following kwargs are set as defaults:

            separator       = ','
            applyPadding    = True
            use             = 'values'

        where:

            * <separator> is the CSV separator
            * if <applyPadding> then pad fields according to enum classes in
              the model
            * <use> a choice of 'values', 'keys', or 'flush'.

        Args:
            d_event (dict): an arbitrary dictionary

        Returns:
            str: a CSV formatted string representation of the dictionary values, with
                 field padding applied.
        """
        str_separator:str   = ","
        str_use:str         = 'values'
        b_applyPadding:bool = False
        str_CSV:str         = ""
        l_cols:list         = list(d_event.keys())
        for k,v in kwargs.items():
            if k == 'separator'         :   str_separator   = v
            if k == 'use'               :   str_use         = v
            if k == 'applyPadding'      :   b_applyPadding  = bool(v)
            if k == 'show' and len(v)   :   l_cols          = v.split(',')
        if len(l_cols):
            try:
                d_event = {key: d_event[key] for key in l_cols}
            except:
                pass
        lcsv_get            = \
            lambda doPadding, use   : \
                self.telemetryService_padWidth(d_event, use = use)  if doPadding \
                    else list(d_event.keys()) if use == 'keys'      \
                    else list(d_event.values())

        str_CSV += str_separator.join(str(x) for x in lcsv_get(b_applyPadding, str_use))
        # str_CSV += '\n'
        return str_CSV

    def telemetryService_collectionGetCSV(self,
                str_objName,
                str_collectionName,
                **kwargs) -> str:
        """
        Return a CSV formatted string of "event" data for the passed obj/collection
        """
        CSV_getStr      = \
            lambda d, fields, sep, field, padding : self.telemetryService_dictAsCSV(
                d, show = fields, separator = sep, use = field, applyPadding = padding
            )
        table_topBorder = \
            lambda d, fields : self.telemetryService_dictAsCSV(
                d, show = fields, separator = '┬', use = 'flush', applyPadding = True
            )
        table_middleBorder = \
            lambda d, fields : self.telemetryService_dictAsCSV(
                d, show = fields, separator = '┼', use = 'flush', applyPadding = True
            )
        table_bottomBorder = \
            lambda d, fields : self.telemetryService_dictAsCSV(
                d, show = fields, separator = '┴', use = 'flush', applyPadding = True
            )
        str_format:str  = "plain"
        str_sep:str     = ','
        str_fields:str  = ''
        b_padding:bool  = False
        for k,v in kwargs.items():
            if k == 'format'        : str_format    = v
            if k == 'applyPadding'  : b_padding     = bool(v)
            if k == 'fields'        : str_fields    = v
        if str_format == 'fancy': str_sep = '│'
        str_CSV:str     = ""
        l_events:list   = [
            self.telemetryService_event(
                str_objName, str_collectionName, x
            ) for x in self.telemetryService_eventList(
                            str_objName, str_collectionName
                        )
        ]
        if len(l_events):
            # Get the "headers"
            if str_format == 'fancy':
                str_CSV += "┌" + table_topBorder(l_events[0], str_fields)                        + "┐\n"
                str_CSV += '│' + CSV_getStr(l_events[0], str_fields, str_sep, 'keys', b_padding) + '│\n'
                str_CSV += "├" + table_middleBorder(l_events[0], str_fields)                     + "┤\n"
            else:
                str_CSV += CSV_getStr(l_events[0], str_fields, str_sep, 'keys', b_padding) + '\n'

            # Now for the table body
            for el in l_events:
                if str_format == 'fancy':
                    str_CSV += '│' + CSV_getStr(el, str_fields, str_sep, 'values', b_padding) + '│\n'
                else:
                    str_CSV += CSV_getStr(el, str_fields, str_sep, 'values', b_padding) + '\n'
            if str_format == 'fancy': str_CSV += "└" + table_bottomBorder(l_events[0], str_fields) + "┘\n"
        return str_CSV

    def telemetryService_collectionGetMatrix(self,
                str_objName,
                str_collectionName,
                **kwargs) -> dict:
        """
        Return a named "matrix", i.e. a dictionary containing a list of
        lists of "event" data for the passed obj/collection. This is
        essentially a CSV "table" but each column of the table is a list.
        Taken together, all the lists are further packaged into a list,
        resulting in the "list of lists", where each list is one "column".

        The first element of each list is the column header -- hence all list
        contents are strings. Callers should parse/process the matrix as they
        see fit.
        """
        d_ret:dict      = {
            str_collectionName  : []
        }
        l_events:list   = [
            self.telemetryService_event(
                str_objName, str_collectionName, x
            ) for x in self.telemetryService_eventList(
                            str_objName, str_collectionName
                        )
        ]
        l_header:list       = []
        l_table:list[list]  = []
        colCount:int        = 0
        if len(l_events):
            # Get the "headers"
            l_header = list(l_events[0].keys())
            for heading in l_header:
                l_table.append([])
                l_table[colCount].append(str(heading))
                colCount += 1
            for el in l_events:
                colCount = 0
                for body in el.values():
                    l_table[colCount].append(str(body))
                    colCount += 1
        d_ret[str_collectionName] = l_table
        return d_ret

