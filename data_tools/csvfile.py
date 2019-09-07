def reader(file, delimiter=',', quotechar='"', newline='\n'):
    filestr = file.read()
    
    linelist = []
    filelist = []
    current = ""
    quoted = False
    for char in filestr:
        if ord(char) == ord(quotechar):
            current += char
            quoted = not quoted
        elif ord(char) == ord(newline) and not quoted:
            linelist.append(current)
            filelist.append(linelist)
            linelist = []
            current = ""
        elif char == delimiter and not quoted:
            linelist.append(current)
            current = ""
        else:
            current += char
    
    return filelist
