# Simple logger, does nothing fancy and is much faster than the standard logging library for simple needs.

from simplediscord.utils.colors import Colored

DEBUG = 40
INFO = 30
WARNING = 20
FATAL = 10
NONE = 0

level = INFO

logging_color = {
    "debug_fg"   : None,
    "debug_bg"   : None,
    "info_fg"    : None,
    "info_bg"    : None,
    "warning_fg" : None,
    "warning_bg" : None,
    "fatal_fg"   : None,
    "fatal_bg"   : None
}


"""Format print complex data structures such as JSON.

@Param obj: any valid data structure.
@Param (optional) prefix: prefix the output.
@Param (optional) keydepth: The index or key value(s) the object currently is in an array or a dictionary, the top level depth is ascribed Root by default, seperated each by dot notation.
@Param (optional) depth: maximum recursion depth <= 1000. 
@Param (optional color_fg: foreground color, a color defined in the Color class (file: utils/colors.py) or a r;g;b;m format value where m is the terminating character.
@Param (optional color_fg: background color, format same as foreground.

"""

def format_print(obj, prefix="", keydepth="Root", depth=100, color_fg=None, color_bg=None):
    if depth > 1000:
        print("Recursion limit is a 1000.")
        return False
    elif depth <= 0:
        print(Colored(f"Recursion error: maximum recursion depth {depth} reached!", color_fg, color_bg))
        return False

    if type(obj) == list:
        for i in range(len(obj)):
            if type(obj[i]) == list or type(obj[i]) == dict:
                format_print(obj[i], prefix, keydepth + "[" + str(i) + "]", depth-1, color_fg, color_bg)
            else:
                print(Colored(f"{prefix}{keydepth}: {obj[i]}", color_fg, color_bg))
    elif type(obj) == dict:
        for k,v in obj.items():
            if type(v) == dict or type(v) == list:
                format_print(obj[k], prefix, keydepth + "." + k, depth-1, color_fg, color_bg)
            else:
                print(Colored(f"{prefix}{keydepth}: {k}: {v}", color_fg, color_bg))
    else:
        print(Colored(f"{prefix}{keydepth}: {obj}", color_fg, color_bg))

    return True
    
def debug(arg, formatprint=False):
    if level >= DEBUG:
        debug_fg, debug_bg = logging_color["debug_fg"], logging_color["debug_bg"]
        if formatprint:
            format_print(arg, "DEBUG: ", color_fg=debug_fg, color_bg=debug_bg)
        elif debug_fg or debug_bg:
            print(Colored("DEBUG: " + str(arg), debug_fg, debug_bg))
        else:
            print("DEBUG: " + str(arg))

def info(arg, formatprint=False):
    if level >= INFO:
        info_fg, info_bg = logging_color["info_fg"], logging_color["info_bg"]
        if formatprint:
            format_print(arg, "INFO: ", color_fg=info_fg, color_bg=info_bg)
        elif info_fg or info_bg:
            print(Colored("INFO: " + str(arg), info_fg, info_bg))
        else:
            print("INFO: " + str(arg))

def warning(arg, formatprint=False):
    if level >= WARNING:
        warning_fg, warning_bg = logging_color["warning_fg"], logging_color["warning_bg"]
        if formatprint:
            format_print(arg, "WARNING: ", color_fg=warning_fg, color_bg=warning_bg)
        elif warning_fg or warning_bg:
            print(Colored("WARNING: " + str(arg), warning_fg, warning_bg))
        else:
            print("WARNING: " + str(arg))

def fatal(arg, formatprint=False):
    if level >= FATAL:
        fatal_fg, fatal_bg = logging_color["fatal_fg"], logging_color["fatal_bg"]
        if formatprint:
            format_print(arg, "FATAL: ", color_fg=fatal_fg, color_bg=fatal_bg)
        elif fatal_fg or fatal_bg:
            print(Colored("FATAL: " + str(arg), fatal_fg, fatal_bg))
        else:
            print("FATAL: " + str(arg))
