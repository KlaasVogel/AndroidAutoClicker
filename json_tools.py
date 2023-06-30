import json
import os
import traceback

class JSONs:
    def __init__(self, *dirs):
        self.create_path(*dirs)
        self.path = os.path.join(*dirs)
    
    @staticmethod
    def create_path(*dirs):
        fullpath = ""
        for dir in dirs:
            fullpath = os.path.join(fullpath, dir)
            if not os.path.isdir(fullpath):
                os.mkdir(fullpath)

    @staticmethod
    def filename(name: str) -> str:
        return name+".json"
    
    @staticmethod
    def loadJSON(file) -> dict:
        data={}
        try:
            if os.path.isfile(file):
                with open(file) as json_file:
                    data = json.load(json_file)
            else:
                raise Exception(f"file not found: {file}")
        except Exception as e:
            print(e)
            traceback.print_exc()
        finally:
            return data
        
    @staticmethod
    def saveJSON(data, file):
        try:
            with open(file, 'w') as outfile:
                json.dump(data, outfile, indent=2)
        except Exception as e:
            traceback.print_exc()
    
    def get_file(self, name: str) -> os.path:
        filename = self.filename(name)
        return os.path.join(self.path, filename)

    def load(self, name: str) -> dict:
        file = self.get_file(name)
        return self.loadJSON(file)
    
    def save(self, data: dict, name: str):
        filename = self.get_file(name)
        self.saveJSON(data, filename)





