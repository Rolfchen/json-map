#### Json Map ###
# beta
# @author Rolf Chen
# This module will "transform" one JSON object to another through the use of JSON Mapper Schema
# @license
#
# MIT License
#
# Copyright (c) 2016 Rolf Chen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
##### Json Map ###

# Native
import json
from datetime import datetime
# External Libraries
from jsonpointer import resolve_pointer
import requests

class Mapper:
	OBJTYPES={
		"string": str, 
		"object": dict,
		"array": list,
		"int": int, 
		"float": float, 
		"date": datetime
	}
	#CONSTANTS
	# condition operators
	OPERATORS={
		"$ne": lambda x,y: x != y,
		"$gte": lambda x,y: x >= y, 
		"$lte": lambda x,y: x <= y, 
		"$gt": lambda x,y: x > y, 
		"$lt": lambda x,y: x < y
	}
	def __init__(self, schema={}, root_doc=None):
		if schema == None:
			return None
		else:
			self.json=schema # It's a JSON Object (dictionary in Python.)
			if isinstance(schema,str):
				self.json=json.loads(schema)
			# Define root_doc, if root_doc is None, then it's assumed that this is the base element. 
			self.root_doc = self.json if root_doc == None else root_doc
			if "allOf" in self.json:
				for rules in self.json["allOf"]:
					self.json.update(rules)
				del self.json["allOf"]
			# Setup refs first. 
			if "$ref" in self.json:
				self.json.update(self.get_ref(self.json["$ref"]))
				del self.json["$ref"]
			# Base Properties
			self.type=self.json.get("type", "object")
			self.class_type=self.OBJTYPES[self.type]
			self.value=self.json.get("value", None) ### OVERWRITES ALL!
			self.description=self.json.get("description", None)
			self.map=self.json.get("map", "")

			# Mapper Objects
			# If property exists, make each item in the property a mapper object 
			self.properties=None
			if "properties" in self.json:
				self.properties={}
				for pkey, pitem in self.json["properties"].items():
					self.properties[pkey]=Mapper(pitem, self.root_doc) # Child properties will use this current root doc as its root doc. 
			
			# If Items exists, make the item a mapper object. 
			self.items=None
			if "items" in self.json:
				self.items=Mapper(self.json["items"], self.root_doc)
			# TODO

			# Conditions
			self.conditions=self.json.get("conditions", {})
			# Options
			self.options=self.json.get("options", {})

	# Returns JSON document (not mappable) of the reference. 
	def get_ref(self,jpointer):
		path_segment=jpointer.split("#")
		ref_doc=self.root_doc # assuming it's referencing root document
		if len(path_segment) > 1:
			doc_path=path_segment.pop(0)
			if "http" in doc_path: # path is an URL
				ref_doc=requests.get(doc_path)
			elif doc_path != "": # path is not empty and not URL, treat as file path
				f=open(root_path, "r")
				ref_doc=f.read()
		reference=resolve_pointer(ref_doc, path_segment[0])
		return reference

	def isWorthy(self,subject):
		outcome=True
		if "OR" in self.conditions:
			outcome=False
			for or_condition in self.conditions.pop("OR"):
				if self.conditionTest(or_condition, subject):
					outcome=True
					break
		outcome=self.conditionTest(self.conditions, subject)
		return outcome

	def conditionTest(self, condition_list, subject):
		outcome=True
		## Check conditions first. 
		for condition_key,condition in condition_list.items():
			# If condition key is one of the operators, do a direct compare to the property
			if condition_key in self.OPERATORS:
				if not self.OPERATORS[condition_key](subject, condition):
					outcome=False
			#condition is complex (dictionary)
			elif isinstance(condition, dict): 
				# Loop through each item in the condition (i.e. {"$gt":2, "$lt":4})
				for ops,cond in condition.items():
					if not self.OPERATORS[ops](subject[condition_key], cond):
						outcome = False
			else:
				if not subject[condition_key] == condition:
					outcome= False
		return outcome

	def key_map(self, subject):
		new_subject={}
		for subject_member in subject: # Subject must be a list of dictionary obj
			m_key=get_element_from_path(self.options["KEY_MAP"], subject_member)
			if m_key is not None:
				## Transform and add
				new_subject_member={}
				for skey,sitem in self.properties.items():
					new_item=sitem.transform(subject_member)
					if not is_empty(new_item):
						new_subject_member[skey]=new_item
				if not is_empty(new_subject_member):
					new_subject[m_key]=new_subject_member
		return new_subject

	def transform(self, subject, sub_parent=None):
		transformed=subject # Set to none mapped version
		## VALUE
		if self.value != None:
			transformed=self.value
		## MAP
		if sub_parent==None:
			sub_parent=subject # if none, make it self.
		if self.map != "":
			if isinstance(self.map, list): # ARRAY! item aggregation
				aggregated_transform=[]
				priorities=self.options.get("PRIORITY", [])
				prioritised=[]
				for map_bits in self.map:
					new_bit=get_element_from_path(map_bits, subject, sub_parent)
					if not is_empty(new_bit):
						if map_bits in priorities:
							prioritised.append(new_bit)
							aggregated_transform.append(new_bit)
				if len(prioritised) > 0:
					aggregated_transform=prioritised
				# TODO!! MAKE TYPES MORE GENERIC
				if self.type=="string":
					transformed=" ".join(aggregated_transform)
				elif self.type=="array":
					if self.json.get("item_type", None) == "float":
						for a_item in aggregated_transform:
							try:
								float(a_item)
							except ValueError as ve:
								pass
					transformed=aggregated_transform
			else:
				transformed=get_element_from_path(self.map, subject, sub_parent)

		## CONDITIONS AND OPTIONS
		if isinstance(transformed, list):
			# CONDITIONS (ARRAY ONLY)
			transformed=list(filter(self.isWorthy, transformed))
			# OPTIONS
			if len(self.options) > 0:
				if "KEY_MAP" in self.options:
					transformed=self.key_map(transformed)
				if "GET_ONE" in self.options:
					transformed=transformed[0]
			## ITEMS
			if not is_empty(self.items) and not is_empty(transformed):
				new_transform=[]
				for trans_item in transformed:
					new_trans_item=self.items.transform(trans_item, sub_parent)
					if not is_empty(new_trans_item):
						new_transform.append(new_trans_item)
				transformed=new_transform if len(new_transform) > 0 else None

		## PROPERTIES only for objects. NOTE: KeyMapped objects are different. 
		elif not is_empty(self.properties):
			new_transform={}
			for tkey, titem in self.properties.items():
				new_item=titem.transform(transformed, sub_parent)
				if not is_empty(new_item):
					new_transform[tkey]=new_item
			transformed=new_transform if not is_empty(new_transform) else None
		
		## FINALLY, convert type if it wasn't converted. 
		if not isinstance(subject, self.class_type):
			self.convert(subject)
		return transformed

	def convert(self, subject):
		dtf= "%Y-%m-%dT%H%M%S"
		df="%Y-%m-%d"
		_simple_types=["string", "int", "float"]
		#_complext_types=["object", "array"]
		converted=subject
		if self.type in _simple_types:
			# Reduce as the first item for dic
			while isinstance(converted, dict):
				ld=list(converted.values())
				converted=ld[0]
			# Reduce as the first item for lists
			while isinstance(converted, list):
				converted=converted[0]
			#converted=self.class_type(converted)
		#elif self.type == "date" and isinstance(converted, str):
			#remove timezone.

			# try:
			# 	converted=datetime.strptime(converted, df)
			# except TypeError as te:
			# 	pass
			# except AttributeError as ae:
			# 	pass
			# except ValueError as ve:
			# 	try:
			# 		date_parts=converted.split("+")
			# 		converted=datetime.strptime(date_parts[0], dtf)
			# 	except ValueError as vve:
			# 		pass
		return converted
		### TODO: IGNORE DICTIONARY TO ARRAY For NOW

class TransformSchema(Mapper):
	def __init__(self, schema={}, root_doc=None):
		super().__init__(schema, root_doc)
		# Additional objects that only Transform Schema should have. 
		self.id=schema.get("$id", None)
		self.title=schema.get("title", None)
		self.schema_type=schema.get("$schema", "http://schemas.dataestate.net/v2/mapping-schema")
		self.version=schema.get("schema_version",2)
		self.definitions=schema.get("definitions", {})
	
def is_empty(obj):
	if obj is None:
		return True
	if not obj:
		return True
	if obj == " ":
		return True
	if obj == {}:
		return True
	return False

def get_element_from_path(dot_path="", doc=None, parent=None):
	paths=dot_path.split(".")
	if len(paths) <= 0:
		return doc
	elif doc is not None:
		element=doc
		for path in paths:
			if element is None:
				break
			if path == "$root":
				element=parent if parent is not None else doc #resets to parent, if no parent, then doc itself
			try: 
				# Simple: path exists in dictionary else None
				element=element.get(path, None)
			except AttributeError: # Not a dict
				try:
					element=element[int(path)] # see if it's an array. 
				except ValueError: # path is not an integer
					new_list=[]
					for item in element:
						if item.get(path, None) != None:
							new_list.append(item[path])
					element=new_list
		return element
	else:
		return None