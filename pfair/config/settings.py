import  os
from    pydantic    import BaseSettings

class Keys(BaseSettings):
    DBauthPath:str      = '/db/init.json'
    ReadWriteKey:str    = "local"

class Mongo(BaseSettings):
    URI:str             = os.environ['pfair_MONGODB']
    DB:str              = "default"

keys            = Keys()
mongosettings   = Mongo()
