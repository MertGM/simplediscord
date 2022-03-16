# Simple logger, does nothing fancy and is much faster than the standard logging library.


NONE = 0
FATAL = 10
WARNING = 20
INFO = 30
DEBUG = 40

level = INFO

def debug(*args):
    if level >= DEBUG:
        print("DEBUG:", *args)

def info(*args):
    if level >= INFO:
        print("INFO:", *args)

def warning(*args):
    if level >= WARNING:
        print("WARNING:", *args)

def fatal(*args):
    if level >= FATAL:
        print("WARNING:", *args)
