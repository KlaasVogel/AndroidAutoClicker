from os import path


def printtime(seconds):
    if seconds <= 60:
        return f"{int(seconds)} seconds"
    if seconds <= 60*60:
        min=int(seconds/60)
        sec=int(seconds%60)
        return f"{min} minute(s) and {sec} seconds"
    hour=int(seconds/3600)
    min=int((seconds%3600)/60)
    sec=int(seconds%60)
    text=f"{hour} hour(s)"
    sep=", " if (min and sec) else " and "
    text=text+sep
    if min:
        text=text+f"{min} minute(s)"
    if sec:
        text=text+f" and {sec} seconds"
    return text

def getName(file):
    filename=f"{path.splitext(path.split(file)[1])[0]}"
    for str in ["_C_","_C","_T","_B","L_","R_"]:
        if str in filename:
            filename=filename.replace(str,"")
    return filename
