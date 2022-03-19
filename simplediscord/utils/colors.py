CSI_FG  = "\x1b[38;2;"
CSI_BG  = "\x1b[48;2;"
CSI_END = "\x1b[m"

class Colors:
    red   = "255;0;0m"
    green = "0;255;0m"
    blue  = "0;0;255m"
    cyan  = "0;255;255m"
    yellow  = "255;255;0m"
    magenta  = "255;0;255m"
    spring_green = "0;255;127m"
    purple = "128;0;128m"
    corn_flower_blue = "100;149;237m"
    white = "255;255;255m"
    black = "0;0;0m"


def Colored(text, fg=None, bg=None):
    output = ""
    color_given = False
    if fg:
        output += CSI_FG + fg  
        color_given = True
    if bg:
        output += CSI_BG + bg
        color_given = True
    if color_given:
        output += text + CSI_END
    else:
        return text

    return output


# This is only needed for Windows shells e.g: CMD, Powershell. 
# Most operating systems already support ANSI escape sequences, even Windows in Windows Terminal.

# Enable Virtual Terminal Sequences, released in 2016 for Windows 10. 
def EnableVT():
    from platform import system

    if system() == "Windows":
        from ctypes import windll, byref
        from ctypes.wintypes import WORD, DWORD, HANDLE

        # Values from Winbase.h.
        STDOUT = -11
        STDERR = -12

        # Value from WinCon.h.
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = DWORD(4)

        kernel = windll.kernel32
        stdout = HANDLE(kernel.GetStdHandle(STDOUT))
        if stdout == -1:
            return False

        mode = DWORD(0)
        if not kernel.GetConsoleMode(stdout, byref(mode)):
            return False

        mode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING.value
        if not kernel.SetConsoleMode(stdout, mode):
            return False
    else:
        return False

    return True
