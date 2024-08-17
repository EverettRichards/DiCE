import csv
import math
import os
import shutil
import time
from collections import defaultdict

from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip as extract
execution_start_time = time.time()

######################################################################
############################## SETTINGS ##############################
######################################################################

# The main folder where I store my DiCE stuff
main_directory = "C:\\Users\\ehric\\OneDrive\\Documents\\DiCE\\"
# Where I put the CSV files to be read
input_directory = main_directory + "CSV_Input\\"

# Where I put the MP4 files to be read
video_input_directory = main_directory + "Video_Input\\"

# Where the outputs will eventually go
consolidated_directory = main_directory + "Consolidated_Output\\"
sourceFileName = "user3_task5"
doClearOutput = True # True to clear all previous outputs when you run the code

#instruction_directory = main_directory + "Instructions\\"
#instruction_file = instruction_directory + "user1_activity1.txt"

# The frequency, in Hertz (s^-1), of the recorded data
frequency = 2000#Hz

activity_ranges = {
	"carrying material": [
		(0*60 + 1, 0*60 + 14), (3*60 + 25, 3*60 + 33),
		(4*60 + 46, 5*60 + 7), (7*60 + 34, 7*60 + 38),
		(10*60 + 28, 10*60 + 43), (14*60 + 41, 14*60 + 56),
		(16*60 + 16, 16*60 + 27), (35*60 + 46, 36*60 + 0),
		(42*60 + 19, 42*60 + 26), (55*60 + 55, 56*60 + 59)
	],
	"nailing": [
		(0*60 + 25, 0*60 + 40), (1*60 + 19, 2*60 + 41),
		(5*60 + 12, 6*60 + 32), (8*60 + 9, 8*60 + 25),
		(10*60 + 44, 11*60 + 6), (11*60 + 11, 11*60 + 35),
		(11*60 + 52, 12*60 + 57), (15*60 + 12, 15*60 + 50),
		(15*60 + 58, 16*60 + 13), (16*60 + 34, 17*60 + 22),
		(18*60 + 14, 21*60 + 40), (22*60 + 9, 23*60 + 30),
		(23*60 + 40, 25*60 + 13), (27*60 + 13, 28*60 + 11),
		(28*60 + 51, 29*60 + 47), (30*60 + 18, 31*60 + 5),
		(32*60 + 28, 33*60 + 13), (34*60 + 30, 35*60 + 15),
		(36*60 + 4, 36*60 + 34), (37*60 + 11, 38*60 + 39),
		(39*60 + 15, 40*60 + 5), (40*60 + 40, 40*60 + 47),
		(42*60 + 39, 43*60 + 50), (43*60 + 39, 46*60 + 45),
		(55*60 + 14, 55*60 + 49)
	],
	"measure": [
		(0*60 + 51, 1*60 + 16), (2*60 + 46, 3*60 + 22),
		(7*60 + 21, 7*60 + 31), (7*60 + 43, 8*60 + 1),
		(13*60 + 7, 13*60 + 33), (17*60 + 43, 18*60 + 3),
		(25*60 + 23, 25*60 + 45), (31*60 + 11, 31*60 + 22),
		(33*60 + 44, 34*60 + 7), (36*60 + 45, 37*60 + 2)
	],
	"cutting": [
		(3*60 + 40, 3*60 + 44), (3*60 + 54, 3*60 + 57),
		(4*60 + 11, 4*60 + 23), (8*60 + 40, 9*60 + 11),
		(48*60 + 28, 49*60 + 12)
	],
	"adjusting sheets": [
		(6*60 + 33, 7*60 + 16), (26*60 + 31, 26*60 + 51),
		(28*60 + 41, 28*60 + 48), (30*60 + 7, 30*60 + 14),
		(32*60 + 10, 32*60 + 24), (34*60 + 12, 34*60 + 29),
		(38*60 + 56, 39*60 + 13), (42*60 + 30, 42*60 + 38),
		(43*60 + 17, 43*60 + 38), (54*60 + 57, 55*60 + 13)
	]
}


######################################################################
############################ END SETTINGS ############################
######################################################################

## DEPRECATED SETTINGS
# The file name that you want to output. Leave as empty string "" to use inputFileName.
alternateFileName = "u1t2_Spraypaint"
start_time0 = 14*60 + 21.5
end_time0 = 14*60 + 33.5
# The name of the file that I want to read as raw input. Looks within input_directory
inputFileName = sourceFileName+".csv"
inputVideoName = sourceFileName+".mp4"

def clearFolder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def makeNewDirectory(parent_directory,new_directory):
    path = os.path.join(parent_directory,new_directory+"\\")
    if os.path.isdir(path):
        if doClearOutput:
            clearFolder(path)
        else:
            return path,False
    else:
        os.mkdir(path)
    return path,True

# Mini function to cut out certain unneeded data pieces
def clean_bar(input):
    output = [input[0]]+input[4:] # Use only the 0th, and 4th-nth data points
    # (in other words, ignore data points 1, 2, and 3)
    return output

def clean_title_bar(input):
    return clean_bar(input)

# Function that will output specified portions of a CSV file in both CSV and JSON format.
# The parameters {start,end} are for the first/last index you want to capture,
# i.e. for t=15s to t=20s @ 2000Hz, you want start=30000 and end=40000
def parse_csv(path,filename,start,end):
    print("Attempting to open file...")
    # Use built-in "open" and csv "reader" functions to begin reading CSV data
    file = open(path)
    reader = csv.reader(file)
    index=0
    contents = [] # The list of output data points. Empty to start.
    for row in reader: # Cycle through every row in the input CSV file
        if (index>=start): # Only count the data if it's after the specified start point
            contents.append(clean_bar(row)) # Add the current data point to the list "contents"
        elif index==3:
            contents.append(clean_title_bar(row))
        if (index>=end or (len(row)==0 and index>3)): # Once you reach the "end" point, stop reading.
            break
        index += 1
    print("Finished opening file!")
    print("Attempting to save CSV file...")
    # Save the CSV file using Python/csv functions
    output = open(csv_directory+filename+".csv",'w',newline='\n')
    writer = csv.writer(output)
    writer.writerows(contents)
    output.close()
    print("Finished saving CSV file!")

# Get trimmed video given input video address, where to put it, and time stamps.
def getTrimmedVideo(fileName,start_time,end_time):
    # The minutes/seconds of the start time, used for the file name (i.e. turn 263 seconds into 4:23)
    start_min = math.floor(start_time/60)
    start_sec = start_time%60
    
    # The minutes/seconds of the end time, used for the file name
    end_min = math.floor(end_time/60)
    end_sec = end_time%60
    
    input_video_address = video_input_directory + inputVideoName
    # Format the output file name
    output_video_name = f"{video_output_directory}{fileName}.mp4"
    
    extract(input_video_address,start_time,end_time,output_video_name)

def getSec(time_string):
    min,sec = time_string.split(":")
    return int(min)*60+float(sec)

def default_value():
    return 0

dict = defaultdict(default_value)

def custom_sort(item):
    return item[1]

time_stamps = [[activity_name,stamp[0],stamp[1]] for activity_name,time_stamps in activity_ranges.items() for stamp in time_stamps ]
time_stamps = sorted(time_stamps,key=custom_sort)

unique_csv_count = 0

def saveCSV(contents,activityName):
    unique_csv_count += 1
    alternateFileName = activityName

    uniqueCount = dict[alternateFileName]
    dict[alternateFileName] += 1
    alternateFileName += str(uniqueCount)

    output = open(csv_directory+alternateFileName+".csv",'w',newline='\n')
    writer = csv.writer(output)
    writer.writerows(contents)
    output.close()
    print("Saved CSV file. (%i/%i)"%(unique_csv_count,len(time_stamps)))

print("Attempting to open file...")
# Use built-in "open" and csv "reader" functions to begin reading CSV data
inputfile = input_directory+inputFileName
file = open(inputfile)
reader = csv.reader(file)

file_cycle = -1
activity_index = 0

current_stamp = time_stamps[0]
header_row = None

################################
######## SAVE CSV FILES ########
################################

chosen_directory,success = makeNewDirectory(consolidated_directory,sourceFileName)
# Where the output CSV files will go
csv_directory = chosen_directory#main_directory + "CSV_Output\\"
# Where I put the MP4 output files (trimmed)
video_output_directory = chosen_directory#main_directory + "Video_Output\\"

if (doClearOutput):
    clearFolder(chosen_directory)

contents = [] # The list of output data points. Empty to start.
for row in reader: # Cycle through every row in the input CSV file
    file_cycle += 1
    if file_cycle < 3:
        continue
    elif file_cycle==3: # Add header row.
        header_row = clean_title_bar(row)
        contents.append(header_row)
        continue
    
    row_time = float(row[0])

    if (row_time>=current_stamp[1] and row_time<=current_stamp[2]):
        contents.append(clean_bar(row))

    elif (row_time>current_stamp[2]):
        # Go to the next one
        activity_index += 1
        saveCSV(contents,current_stamp[0])
        contents = [header_row]
        if activity_index>=len(time_stamps):
            break
        else:
            current_stamp = time_stamps[activity_index]

    if len(row)==0 and file_cycle>3: # Once you reach the "end" point, stop reading.
        print("Loop artificially broken.")
        saveCSV(contents,current_stamp[0])
        break

################################
######### SAVE VIDEOS ##########
################################

dict = defaultdict(default_value)
for set in time_stamps:
    activity_name = set[0]
    start_time = set[1]
    end_time = set[2]

    uniqueCount = dict[activity_name]
    dict[activity_name] += 1
    activity_name += str(uniqueCount)

    # Call the getTrimmedVideo function to quickly trim the video
    getTrimmedVideo(activity_name,start_time,end_time)

print("##################################################")
print("############# TASK COMPLETE (%.2fs) #############" % (time.time()-execution_start_time))
print("##################################################")

# Add option to output data, i.e. how many total tasks, avg length, etc
# More intelligent CSV parsing... Go through it all at once. It's basically O(n^2) rn