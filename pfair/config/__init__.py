from    db                      import  pfdb
from    config                  import  settings

dbAPI   = pfdb.PFdb_mongo(settings.keys, settings.mongosettings)
