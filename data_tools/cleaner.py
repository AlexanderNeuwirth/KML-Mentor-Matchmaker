"""

    Code written by Benjamin Klemp, May 2019

    Written to accompany the Kettle Moraine Lutheran Mentor-matching program
    created by Xander Neuwirth; this program is meant to reduce the amount of
    manual corrections to the input data.

    Benjamin Klemp can be contacted at benklempdev@gmail.com

    These files are necessary to run the program:
    | band-mentees.csv
    | mentees-raw.csv
    | mentors-raw.csv

    These are the final output of the program (in output folder):
    | mentees.csv
    | mentors.csv

    Use the console output to make final corrections.

    PLANNED FEATURES:
      Automatically add requests to the files

"""

import csvfile as csv

DEFAULT_LAST = "&...&"

"""
    A function to translate a list to a string

    Removes leading and trailing spaces from the name
"""
def to_line(listin):
    listin[0] = listin[0].strip()
    listin[2] = listin[2].strip()
    return ','.join(listin) + "\n"

"""
    A function to strip newlines off of a list of lines
"""
def strip_lines(lines):
    for i in range(len(lines)):
        lines[i] = lines[i].strip()

"""
    A function to remove a column from a csv file
    
    Allows for the removal of extra columns (such as Score)
    that hold no data
"""
def removeColumn(filein, col, fileout):
    print("Removing column %s from %s" % (col, filein))
    file = open(filein, "r")

    lines = []

    scanner = csv.reader(file)
    for line in scanner:
        line.pop(col)
        lines.append(to_line(line))
        

    out = open(fileout, "w+")
    for line in lines:
        out.write(line)

    print()
    file.close()
    out.close()

"""
    Removes the timestamp and email address from the input data,
    as they are not needed for the matchmaking
"""
def remove_timestamp(filein, fileout):
    removeColumn(filein, 0, "temp.csv")
    removeColumn("temp.csv", 0, fileout)

"""
    A function to remove duplicate names from a mentor/mentee csv file

    It will use the most recent (last) line out of duplicates
"""
def removeDuplicates(filein, fileout):
    print("Removing duplicates from " + filein)
    file = open(filein, "r");
    
    namelist = [];
    lines = [];
    
    scanner = csv.reader(file)
    for line in scanner:
        if(line[0] not in namelist): #only add non-duplicate lines
            namelist.append(line[0]);
            lines.append(to_line(line));
        else:                   #use the most recently added data
            ind = namelist.index(line[0])
            lines[ind] = to_line(line)
            print(line[0]) #print names of removed duplicates
        
    out = open(fileout, "w+");
    for line in lines:
        out.write(line);

    print()
    file.close();
    out.close();

"""
    Creates a new profile with name, gender, and one piece of data
    This was created to make empty profiles for band mentees that had not
    filled out the form
"""
def add_profile(lines, name, gender, index, data):
    if gender.upper() == "M" or gender.upper() == "MALE":
        gender = "Male"
    elif gender.upper() == "F" or gender.upper() == "FEMALE":
        gender = "Female"
    else:
        gender = ""
    line = [name, gender, "No","","","","","",""]
    line[index] = data
    lines.append(to_line(line))

def get_band_kids(filein, fileout, listfile=None):
    print("Getting band kids from " + filein)
    file = open(filein, "r")

    lines = []
    names = []

    scanner = csv.reader(file)
    if listfile == None:
        for line in scanner:
            if len(line) > 1 and "Band" in line[5]:
                lines.append(to_line(line))
                names.append(line[0])
    else:
        unfilled = []
        flist = open(listfile, "r")
        flines = flist.readlines()
        strip_lines(flines)
        for line in scanner:
            if len(line) > 1 and line[0] in flines:
                lines.append(to_line(line))
                names.append(line[0])
        
        unfill = open(fileout[:len(fileout)-4] + "-unfilled.csv", "w+")
        print("These band members have not yet filled out the form, adding empty profiles:")
        for line in flines:
            if not line in names:
                unfilled.append(line)
                unfill.write(line + '\n')
        unfill.close()
        flist.close()
        for name in unfilled:
            gender = input(name + " (m/f)? ")
            add_profile(lines, name, gender, 5, "Band")

    out = open(fileout, "w+")
    for line in lines:
        out.write(line)

    print()
    file.close()
    out.close()

"""
    Attempts to fix names to a first last format by combining
    three names into two (assumes 2nd and 3rd parts are both
    part of the last name)
"""
def fix_names(filein, fileout):
    file = open(filein, "r")
    
    lines = []
    
    scanner = csv.reader(file)
    for line in scanner:
        linlist = line[0].strip().split(' ')
        if len(line) > 1 and not len(linlist) == 2:
            flag = False
            for ln in linlist:
                if '(' in ln:
                    flag = True
            if len(linlist) == 3 and not flag:
                print("Fixed '" + line[0], end='')
                line[0] = linlist[0] + ' ' + linlist[1] + linlist[2]
                print("' as '" + line[0] + "'")
            else:
                print("Couldn't fix '" + line[0] + "', added default last name")
                line[0] = linlist[0] + ' ' + DEFAULT_LAST
        lines.append(to_line(line))
    out = open(fileout, "w+")
    for line in lines:
        out.write(line)

    file.close()
    out.close()

"""
    A function to find names that need correcting before being
    put into the matchmaking program

    If given an output file, will attempt to automatically
    correct some of the names
"""
def find_bad_names(filein, fileout=None):
    print("Finding bad names in " + filein)

    if not fileout == None:
        fix_names(filein, fileout)
    else:
        file = open(filein, "r")
        scanner = csv.reader(file)
        for line in scanner:
            linlist = line[0].strip().split(' ')
            if len(line) > 1 and not len(linlist) == 2:
                print(line[0])
        file.close()
    
    print()

"""
    Gets mentor-mentee requests from names
    NOT IMPLEMENTED
"""
def get_request(name):
    return ","


"""
    Changes the output files into the format used by
    the mentor-matching program
"""
def format_file(filein, fileout):
    file = open(filein, "r")
    scanner = csv.reader(file)
    first = True

    lines = []

    for line in scanner:
        if first:
            first = False
            continue
        if not len(line) > 1:
            break
        name = line[0].split(' ')
        line[0] = name[0] + "," + name[1]
        line[3] += get_request(line[0])
        lines.append(to_line(line))

    out = open(fileout, "w+")
    for line in lines:
        out.write(line)

    file.close()
    out.close()

"""
    Runs all of the necessary functions
    remove_timestamp should be called first in the loop

    Takes files "mentors-raw.csv" and "mentees-raw.csv"
    Outputs files "mentors.csv", "mentors-band.csv",
    "mentees.csv", and "mentees-band.csv"
"""
def process_forms():
    forms = ["mentors", "mentees"]
    files = { #The %s is replaced by the correct name by the loop
    "raw":"%s-raw.csv",
    "check":"./output/%s-check.csv",
    "format":"./output/%s-format.csv",
    "temp":"./output/%s-temp.csv",
    "final":"./output/%s.csv"
    }
    for form in forms: #Calls functions for mentors and mentees
        remove_timestamp(files["raw"] % form, files["temp"] % form)
        removeDuplicates(files["temp"] % form, files["check"] % form)
        find_bad_names(files["check"] % form, files["format"] % form)
        format_file(files["format"] % form, files["final"] % form)
    
"""
    Main method

    The code should work as-is, but if changes need to be made
    Calls to removeColumn should be placed before process_forms
"""
if __name__=="__main__": #TODO: Make this more efficient
    #Remove column 2 from mentees-untrimmed
    #removeColumn("mentees-untrimmed.csv", 2, "mentees-raw.csv")
    process_forms()
    get_band_kids("./output/mentors-format.csv", "./output/mentors-band-format.csv")
    get_band_kids("./output/mentees-format.csv", "./output/mentees-band-format.csv", "band-mentees.csv")
    format_file("./output/mentors-band-format.csv", "./output/mentors-band.csv")
    format_file("./output/mentees-band-format.csv", "./output/mentees-band.csv")
