from os import write
from    typing              import Any, List, TypedDict
from    pydantic            import BaseModel, Field

import  json
from    datetime            import datetime
from    pathlib             import Path

try:
    from    config              import settings
except:
    from    ..config             import settings
import  sys
import  shutil
import  pudb

import  pymongo
from    pymongo             import MongoClient
from    pymongo.database    import Database
from    pymongo.collection  import Collection

class mongoDB():

    def getDB(self) -> Database[Any]:
        return self.DB

    def connectDB(self, DBname:str) -> dict:
        """
        Connect to the DB called <DBname> (or create the DB if it does
        not exist). Return the DB and a bool exist_already/not_exist
        in a dictionary.

        Args:
            DBname (str): the DB name

        Returns:
            dict[str, bool | Database[Any]]: DB -- the database
                                               bool -- False if DB is not yet created
        """
        d_ret:dict  = {
            'status':   True if DBname in self.Mongo.list_database_names() else False,
            'DB':       self.Mongo[DBname]
        }
        return d_ret

    def collection_add(self, name:str) -> bool:
        b_ret:bool  = False
        l_names     = [ x['name'] for x in self.ld_collection]
        if name not in l_names:
            b_ret   = True
            self.ld_collection.append({
                "name"      : name,
                "collection": mongoCollection(self, name)
            })
        return True

    def __init__(self, DBname:str, settingsMongo:settings.Mongo) -> None:
        """
        The constructor for the mongo data base "object". Each "object"
        is connected to a single mongo database, which can contain a variable
        number of collections (described in a list).

        For "simplicity sake" in this formulation, create a separate object
        for each DB in Mongo.

        :param DBname: the string name of the data base within Mongo
        :param settingsMongo: a structure containing the Mongo URI and login
        :return: None -- this is a constructor
        """
        self.Mongo:MongoClient  = MongoClient(
                                        settingsMongo.MD_URI,
                                        username    = settingsMongo.MD_username,
                                        password    = settingsMongo.MD_password
                                )
        self.ld_collection:list[dict]   = []
        self.DB:Database[Any]           = self.connectDB(DBname)['DB']

class mongoCollection():

    def search_on(self, d_query:dict) -> list:
        l_results:list[dict[str, Any]] = list(self.collection.find(d_query))
        return l_results

    def connectCollection(self, collection:str) -> dict:
        """
        Connect to the collection called <collection> (or create the
        collection if it does not exist). Return the collection and a
        bool exist_already/not_exist in a dictionary.

        :param mongocollection: the name of the collection
        :return: a dictionary with the collection and a status
        """
        d_ret:dict  = {
            'exists':       True if collection in self.DB.list_collection_names() else False,
            'collection':   self.DB[collection]
        }
        return d_ret

    def __init__(self, DBobject:mongoDB, name:str) -> None:
        self.DB:Database[Any]           = DBobject.getDB()
        self.d_collection:dict          = self.connectCollection(name)
        self.collection:Collection[Any] = self.connectCollection(name)['collection']


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

    def Mongo_connectDB(self, DBname:str) -> dict:
        """
        Connect / create the DB.

        Args:
            DBname (str): the DB name

        Returns:
            dict[str, bool | Database[Any]]: DB -- the database
                                               bool -- False if DB is not yet created
        """
        d_ret:dict  = {
            'status':   True if DBname in self.Mongo.list_database_names() else False,
            'DB':       self.Mongo[DBname]
        }
        return d_ret

    def Mongo_connectCollection(self, mongocollection:str) -> dict:
        """
        Simply connect to a named "collection" in a mongoDB and return
        the collection and its status.

        :param mongocollection: the name of the collection
        :return: a dictionary with the collection and a status
        """
        d_ret:dict  = {
            'status':       True if mongocollection in self.DB.list_collection_names() else False,
            'collection':   self.DB[mongocollection]
        }
        return d_ret

    def readwriteKeys_inCollectionGet(
            self,
            d_readwrite:dict,
            collectionExists:bool
    ) -> dict|None:
        if not collectionExists:
            self.collection.insert_one(d_readwrite['init']['keys'])
        d_collectionData    = self.collection.find_one({'readwritekeys': d_readwrite['keyName']})
        return d_collectionData

    def key_get(self, name:str) -> dict:
        """
        Get an access "key" from the main class. This explictly returns a
        dictionary since the self.key member variable can be either dict or
        None which can be flagged by the LSP.

        :param name: the key "name" to lookup
        :return: a dictionary containing the key value (or an error dictionary)
        """
        ret:dict    = {
                "error": f"key {name} not found"
        }
        if self.keys:
            if name in self.keys:
                ret = self.keys[name]
        return ret

    def __init__(self,
                 settingsKeys: settings.Keys,
                 settingsMongo: settings.Mongo) -> None:
        """
        Main database constructor.

        :param settingsKeys: a collection of default configuration settings
        :param settingsMongo: a collection of settings relevant to the mongoBD
        :return: the object
        """

        self.keyInitPath        = Path(settingsKeys.DBauthPath)
        self.Mongo              = MongoClient(settingsMongo.MD_URI,
                                              username  = settingsMongo.MD_username,
                                              password  = settingsMongo.MD_password)

        # Read the API read/write keys from self.keyInitPath
        # and ReadWriteKey collection
        # --- this is used only to instantiate the keys in the monogoDB
        d_readwrite: dict[str, bool | str | dict[Any, Any]] = \
            self.APIkeys_readFromFile(settingsKeys.ReadWriteKey)

        # Connect to the DB
        self.DB:Database[Any]               = self.Mongo_connectDB(settingsMongo.MD_DB)['DB']

        # Connect to the collection
        d_collection:dict                   = self.Mongo_connectCollection('sensors')
        self.collection:Collection[Any]     = d_collection['collection']
        self.keys = self.readwriteKeys_inCollectionGet(d_readwrite, d_collection['status'])

