{
  "$id": "http://api.dataestate.net/test-schemas", 
  "title": "Test Mapping Schema", 
  "type": "object", 
  "$schema": "http://schemas.dataestate.net/v2/mapping-schema", 
  "$version": 2, 
  "definitions": {
    "person": {
      "type": "object", 
      "properties": {
        "name": {
          "type": "string", 
          "map": [
            "firstname", "lastname"
          ]
        }, 
        "age": {
          "type": "int", 
          "map": "age"
        }
      }
    }
  }, 
  "properties": {
    "name": {
      "type": "string", 
      "map": "company_name"
    }, 
    "type": {
      "type": "string", 
      "map": "industry"
    }, 
    "employees": {
      "type": "object", 
      "map": "employees", 
      "options": {
        "KEY_MAP": "role"
      }, 
      "$ref": "#/definitions/person"
    }, 
    "emails": {
      "type": "array", 
      "map": "emails", 
      "items": {
        "type": "string", 
        "map": "address"
      }
    }
  }
}