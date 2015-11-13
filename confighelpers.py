"""
Some helpers for building and parsing configuration files.
"""
import os
import json

import csv
import cStringIO as StringIO
from django.core.serializers.json import DjangoJSONEncoder

import logging
logger=logging.getLogger(__name__)

def uniqueField(record,basefld):
    "Ensure that 'field' is unique in the record by appending digits"
    field = basefld
    if field in record:
        basenum = 0
        while field in record:
            basenum += 1
            field = "%s_%d"%(basefld,basenum)
    return field

class ElementSet(dict):
    '''
    Wrap a few extra functions around a bare dictionary, including a constructor
    that will load a copy of the "config" dictionary keys (and REFERENCES to the
    corresponding values).
    '''
    def __init__(self,config):
        super(ElementSet, self).__init__() # Create a bare dictionary
        for k,v in config.iteritems():
            self[k] = v.get("value",None)

    def addResult(self, field, value):
        '''
        Add result to existing data, but rename field if it already exists
        '''
        self[uniqueField(self,field)] = value

    @property
    def extension(self):
        return 'csv'

    @property
    def content_type(self):
        return 'text/csv'

    def getDataFile(self):
        output = StringIO.StringIO()
        dw = csv.DictWriter(output, fieldnames=self.keys(), extrasaction='ignore')
        dw.writeheader()
        dw.writerow(self)
        del dw
        output.seek(0)
        return output.read()

class FeatureSet(object):
    '''
    FeatureSet checks to see if there are any "properties" (mapped fields) that are not
    functioning as constants.  If there are, then open and iterate through the associated
    file, filling in the property fields and supplying constants for the non-property fields
    (the results are returned as an ElementSet, q.v.).  If there are no mapped fields (all
    constants) then the first call to iterate yields an ElementSet with all the constants, and
    no further iteration is allowed.
    Data from a FeatureSet will always be accessed by iterating, and there will always be
    at least one row if there are any constant values defined (and only one row if only
    constant values are defined).
    If there is a filename and there are "property" fields (i.e. field mappings), then
    
    '''
    def __init__(self,elements,filename):
        self.file_data = filename
        self.iterable_fields = {}
        self.constant_fields = {}
        for key,value in elements.iteritems():
            if (value.get('property',False) or value['type'] == 'property') and \
               value.get('value', None) is not None:
                self.iterable_fields[key] = value.get('value', None)
            else:
                self.constant_fields[key] = value.get('value', None)
        if self.iterable_fields and self.file_data:
            filedata = open(self.file_data).read()
            parsed_data = json.loads(filedata)
            # We're going to repackage the data if it's a list
            if type(parsed_data) is list:
                self.data_parsed = { "features" : [ { "properties" : row } for row in parsed_data ] }
                self.isList = True
            else:
                self.data_parsed = parsed_data
                self.isList = False
        elif self.constant_fields: # but no iterable fields
            # Reproduce a minimal "geo" JSON file with one feature
            # whose properties are the costant fields
            
            self.data_parsed = { "features" : [ { "properties" : self.constant_fields } ] }
        else:
            self.data_parsed = None

    @property
    def iterable(self):
        return True

    def __iter__(self):
        if self.data_parsed:
            if type(self.data_parsed) is dict: # expect geoJSON like
                self.file_iterator = iter(self.data_parsed['features'])
            else:
                raise Exception('Do not know how to parse type '+str(type(self.data_parsed)))
        else:
            self.file_iterator = None
        return self

    def next(self):
        if not self.file_iterator:
            raise StopIteration
        self.this_row = next(self.file_iterator)           # Raise StopIteration if done
        if self.iterable_fields:
            if self.constant_fields:
                data = self.constant_fields.copy()         # Merge constant_fields keys
            else:
                data = {}                                  # If no constants, a new dictionary
            for k, v in self.iterable_fields.iteritems():  # Fill in mapped values from features
                if v is not None: # v is the user-defined field name
                    data[k] = self.this_row['properties'][v]
                else:
                    data[k] = None
        else:
            data = self.this_row['properties'].copy()  # return a copy of the constants
        return data  # A dictionary

    def addResult(self, field, value):
        row = self.this_row['properties']
        row[uniqueField(row,field)] = value # will not overwrite an existing field

    @property
    def extension(self):
        return 'json'

    @property
    def content_type(self):
        return 'application/json'

    def getDataFile(self):
        if self.isList:
            rows = [ row["properties"] for row in self.data_parsed['features'] ]
            return json.dumps(rows, cls=DjangoJSONEncoder)
        else:
            return json.dumps(self.data_parsed, cls=DjangoJSONEncoder)

class ConfigManager(object):
    def __init__(self,input_files,tool_config):
        self._files = input_files   # names of files extracted from the POST
        self._config = tool_config  # the job analysis settings

        self._setup = None
        self.failures = []

    def datafile(self,namespace):
        if namespace in self._files:
            return self._files[namespace][0]  # the location of the job's data file
        else:
            return None

    def cleanup(self):
        """
        Delete the temporary files created by the tool server for
        this job from the data that was posted.
        """
        for namespace, fileinfo in self._files.iteritems():
            os.unlink(fileinfo[0])

    def fail(self,message):
        self.failures.append(message)

    def setup(self,namespace=None):
        if not self._setup:
            try:
                self._setup=self.loadJSON('config').get('analysis settings',{})
                if (not self._setup or not isinstance(self._setup, (dict))):
                    raise Exception('No analysis settings')
            except Exception as e:
                logger.exception(str(e))
                self.fail(str(e))
                raise Exception('JSON load of posted job configuration failed')
            else:
                logger.debug("Loaded config: %s", self._setup)
        if namespace:
            return self._setup[namespace]
        else:
            return self._setup

    def loadJSON(self,namespace):
        if not namespace:
            raise Exception("Missing namespace for JSON file")
        try:
            filename = self.datafile(namespace)
            if filename:
                jsonfile = json.loads(open(filename).read())
            else:
                jsonfile = ""
        except Exception as e:
            self.fail(str(e))
            raise Exception("JSON load of file failed")
        return jsonfile

    @property
    def valid(self):
        return self.setup() and not self.failures

    def getParameters(self,namespace):
        '''
        For Files, return an ElementSet (dictionary) consisting of the values of constant
           (non-iterable) element values and the NAMES of iterable/property elements (field maps)
        For ConfigurationPages, return an ElementSet consisting of the elements (all non-iterable)
        '''
        return ElementSet(self.setup()[namespace])

    def getFeatures(self,namespace):
        '''
        This will reach into the actual file data (if any) to return a FeatureSet (iterable rows, each a dictionary).
        For Files, the FeatureSet will consist of iterable rows filling in the property-type element values,
           including any constant values assigned.  At least one row will be iterated (even if the "File" is all constants)
        For ConfigurationPages, return a FeatureSet whose one iterable element is a geoJSON like version
           of the defined constants (i.e. the source data wrapped in {"features":{"properties": { key/value-pairs }}})
        '''
        return FeatureSet(self.setup()[namespace],self.datafile(namespace))

class Job(object):
    '''
    Manage automatic cleanup of files
    '''
    def __init__(self,input_files,tool_config):
        self._job = ConfigManager(input_files,tool_config)
    def __enter__(self):
        return self._job
    def __exit__(self,exc_type,exc_value,traceback):
        self._job.cleanup()
