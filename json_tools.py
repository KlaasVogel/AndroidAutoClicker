import json
from os import path
import traceback

def loadJSON(file):
    data=[]
    try:
        if path.isfile(file):
            with open(file) as json_file:
                data = json.load(json_file)
        else:
            raise Exception(f"file not found: {file}")
    except Exception as e:
        print(e)
        traceback.print_exc()
    finally:
        return data

def saveJSON(data, file):
    try:
        with open(file, 'w') as outfile:
            json.dump(data, outfile, indent=2)
    except Exception as e:
        traceback.print_exc()
