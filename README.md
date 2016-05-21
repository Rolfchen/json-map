# json-map beta
*DISCLAIMER: This library is still being worked on and has not yet gone through serious testing.*

This library's main purpose is to convert one JSON object to another through the use of JSON-Mapping-Schema. Current version is only available in Python. Next to come will be in PHP. 

## Installation
### Python ###
Requirements:
* Python 3 
* Request (http://docs.python-requests.org/)
* jsonpointer (https://github.com/manuelstofer/json-pointer)
Simply pull **jsonMap.py** from the source code, place it in your project and reference it. Full installation guide will come later when this project is more stable. 

## Usage ##
To use it, instanciatiate a **Mapper** object using the JSON-Mapping-Schema and call the transform function on the JSON object to transform. The transform() method takes in a Dictionary or JSON string as parameter. Full documentation is still to come and will be updated when project is more stable. 

i.e.
```
import json
from jsonMap import Mapper

original=open("Original-Json.js", "r")
schema_json=open("Schema-Json.js", "r")
schema=Mapper(json.load(schema_json))
result=schema.transform(json.load(original)) # Returns a JSON Object

# to output the result
json.dumps(td)
```

## JSON-Mapping-Schema ##
The JSON Mapping Schema is based on JSON-Schema (http://json-schema.org/) with additional properties to achieve various methods of transforms. A Mapping Schema looks like this: 
```
{
  "$id": "http://api.dataestate.net/test-schemas", 
  "title": "Test Mapping Schema", 
  "type": "object", 
  "$schema": "http://schemas.dataestate.net/v2/mapping-schema", 
  "$version": 2, 
  "properties": {
    "name": {
      "type": "object", 
      "map": "personName"
    }
  }
}
```
### Properties ###
Most properties available in json-schema is available here (or will be after full development is completed). Here're some that's exclusive to JSON Mapping. 
#### Map ####
**type: string | array**
This property is a dot string paths (i.e. name.firstname) to the property to map to. For example, if the original JSON is like this: 
```
{
 "name": {
  "firstname": "Joe", 
  "lastname": "Black
 }
}
```
and the mapping schema looks like this: 
```
{
...
  "properties": {
    "name": {
      "type": "string", 
      "map": "name.firstname"
   }
  }
}
```
result will look like this: 
```
{
 "name": "Joe"
}
```
