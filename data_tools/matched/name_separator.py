import time


#I don't understand what I did here...
def separate_old(filein, fileout):
    line_index = 0
    edited_lines = [];
    split_lines = [];
    file_in = open(filein, "r")
    for line in file_in.readlines():
        if (line_index == 0):
            line_index += 1
            continue
        index_a = line.index(",")
        index_b = line.index(",", index_a + 1)
        split_lines.append([line[:index_b], line[index_b + 1:]])
    file_in.close()
    for full_line in split_lines:
        for index in range(len(full_line)):
            print(full_line[index])
            split_line = full_line[index].split(' ', 3)
            """ #Hardcoding
            if split_line[0]=="Ryen":
                edited_lines.append(["Ryen", "Alexis Pagano", "female", "Trinity"])
                continue
            """
            split_line[0] = split_line[0][1:] + ","
            split_line[1] = split_line[1] + ","
            split_line[2] = split_line[2][1:]
            split_line[3] = split_line[3][:len(split_line[3])-(2+index)] + ","
            edited_lines.append(split_line)
    print(edited_lines)
    file_out = open(fileout, "w+")
    file_out.write("Mentor First,Mentor Last,Mentor Gender,Mentor School,Mentee First,Mentee Last,Mentee Gender,Mentee School\n")
    print(len(edited_lines)/2)
    for line_num in range(int(round(len(edited_lines)/2))):
        index_start = line_num * 2
        line = ""
        for index_person in range(2):
            for index in range(4):
                try:
                    line += edited_lines[index_start + index_person][index]
                except IndexError:
                    print(str(line_num) + ", " + str(index_person) + ", " + str(index))
                    break
        file_out.write(line + "\n")
    file_out.close()

def line_from_indexes(line, indexes):
    items = []
    j = 0
    for i in range(0, 5, 4):
        items.append(line[indexes[i+0]+j:indexes[i+1]])
        items.append(line[indexes[i+1]+1:indexes[i+2]])
        items.append(line[indexes[i+2]+2:indexes[i+3]])
        items.append(line[indexes[i+3]+2:indexes[i+4]])
        j = 2
    return items

def separate(filein, fileout):
    lines = []
    fin = open(filein, "r")
    for line in fin.readlines():
        f1 = line.index(" ")
        l1 = line.index(' ', f1+1)
        g1 = line.index(',', l1)
        s1 = line.index(')', g1)
        f2 = line.index(' ', s1)
        l2 = line.index(' ', f2+1)
        g2 = line.index(',', l2)
        s2 = line.index(')', g2)
        lines.append(','.join(line_from_indexes(line, [0, f1, l1, g1, s1, f2, l2, g2, s2])))
    fin.close()

    fout = open(fileout, "w+")
    fout.write("Mentor First,Mentor Last,Mentor Gender,Mentor School,Mentee First,Mentee Last,Mentee Gender,Mentee School\n")
    for line in lines:
        fout.write(line + '\n')
    fout.close()

def sep_unmatched(filein, fileout):
    lines = []
    fin = open(filein, "r")
    for line in fin.readlines():
        f1 = line.index(' ')
        l1 = line.index(' ', f1+1)
        c1 = line.index(')', l1)

        lines.append(','.join([line[0:f1], line[f1+1:l1], line[l1+2:c1]]))
    fin.close()
    
    fout = open(fileout, "w+")
    fout.write("First,Last,Mentor/Mentee\n")
    for line in lines:
        fout.write(line + '\n')
    fout.close()
        

#Only works if format given is "First Last (Gender, School)"
#And Ryen Alexis Pagano is in the list
#^^^This issue is now fixed at an earlier part of the program
if __name__=="__main__":
    files = [
        "matched-band",
        "matched"
        ]
    for file in files:
        separate(file + ".tsv", file + "-separated.csv")
    sep_unmatched("unmatched.tsv", "unmatched-separated.csv")
        
        
