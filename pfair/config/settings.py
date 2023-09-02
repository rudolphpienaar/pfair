import  os
from    pydantic_settings import BaseSettings

class Keys(BaseSettings):
    DBauthPath:str      = '/db/init.json'
    ReadWriteKey:str    = "local"

class Mongo(BaseSettings):
    MD_URI:str          = "localhost:27017"
    MD_DB:str           = "default"
    MD_username:str     = "username"
    MD_password:str     = "password"

keys            = Keys()
mongosettings   = Mongo()
