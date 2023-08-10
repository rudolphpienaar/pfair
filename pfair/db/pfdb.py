from math import dist
from time import monotonic
from    typing              import Any, List, TypedDict, Collection
from h11 import Data
from    pydantic            import BaseModel, Field

import  json
from    datetime            import datetime
from    pathlib             import Path


#from    pfstate             import S
from    pfmisc.C_snode      import C_stree
from    models              import sensorModel
from    config              import settings
import  sys
import  shutil
import  pudb

import  pymongo
from    pymongo             import MongoClient
from    pymongo.database    import Database
from    pymongo.collection  import Collection

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
        collection:Collection       = self.DB[mongocollection]
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

