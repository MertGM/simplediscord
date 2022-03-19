# Simple logger, does nothing fancy and is much faster than the standard logging library.


NONE = 0
FATAL = 10
WARNING = 20
INFO = 30
DEBUG = 40

level = INFO

logging_colors = {
    "debug_fg"   : None,
    "debug_bg"   : None,
    "info_fg"    : None,
    "info_bg"    : None,
    "warning_fg" : None,
    "warning_bg" : None,
    "fatal_fg"   : None,
    "fatal_bg"   : None
}

from simplediscord.utils.colors import Colored

def debug(string):
    if level >= DEBUG:
        debug_fg, debug_bg = logging_colors["debug_fg"], logging_colors["debug_bg"]
        if debug_fg or debug_bg:
            print(Colored("DEBUG: " + string, debug_fg, debug_bg))
        else:
            print("DEBUG: " + string)

def info(string):
    if level >= INFO:
        info_fg, info_bg = logging_colors["info_fg"], logging_colors["info_bg"]
        if info_fg or info_bg:
            print(Colored("INFO: " + string, info_fg, info_bg))
        else:
            print("INFO:" + string)

def warning(string):
    if level >= WARNING:
        warning_fg, warning_bg = logging_colors["warning_fg"], logging_colors["warning_bg"]
        if warning_fg or warning_bg:
            print(Colored("WARNING: " + string, warning_fg, warning_bg))
        else:
            print("WARNING: " + string)

def fatal(string):
    if level >= FATAL:
        fatal_fg, fatal_bg = logging_colors["fatal_fg"], logging_colors["fatal_bg"]
        if fatal_fg or fatal_bg:
            print(Colored("FATAL: " + string, fatal_fg, fatal_bg))
        else:
            print("FATAL: " + string)
