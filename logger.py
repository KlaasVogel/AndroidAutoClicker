import logging
from logging import handlers

class MyLogger(object):
    def __init__(self, name, LOG_LEVEL=logging.ERROR):

        self.log_level = LOG_LEVEL
        # create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LOG_LEVEL)

        # create console handler and set level to debug
        fh = handlers.TimedRotatingFileHandler(
            'info.log', when="W2", backupCount=3)
        fh.setLevel(LOG_LEVEL)
        if name=="SYSTEM_OUTPUT":
            fh.doRollover()

        # create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s- %(message)s')

        # add formatter to ch
        fh.setFormatter(formatter)

        # add ch to logger
        self.logger.addHandler(fh)

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

    def debug(self, str):
        self.logger.debug(str)

    def info(self, str):
        self.logger.info(str)

    def warning(self, str):
        self.logger.warning(str)

    def error(self, str):
        self.logger.error(str)
