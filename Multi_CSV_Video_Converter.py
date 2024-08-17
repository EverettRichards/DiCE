import csv
import math
import os
import shutil
from collections import defaultdict

from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip as extract

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
doClearOutput = False # True to clear all previous outputs when you run the code

instruction_file = main_directory + "SourceCode\\Decoding_Instructions.csv"

# The frequency, in Hertz (s^-1), of the recorded data
frequency = 2000#Hz

######################################################################
############################ END SETTINGS ############################
######################################################################

## DEPRECATED SETTINGS
# The file name that you want to output. Leave as empty string "" to use inputFileName.
alternateFileName = "u1t2_Spraypaint"
# Where the output CSV files will go
csv_directory = main_directory + "CSV_Output\\"
# Where I put the MP4 output files (trimmed)
video_output_directory = main_directory + "Video_Output\\"
start_time0 = 14*60 + 21.5
end_time0 = 14*60 + 33.5
# The name of the file that I want to read as raw input. Looks within input_directory
inputFileName = "user1_task2.csv"
inputVideoName = "user1_activity2_Notion.mp4"

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

inputfile = input_directory+inputFileName

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
def getTrimmedVideo(start_time,end_time):
    # The minutes/seconds of the start time, used for the file name (i.e. turn 263 seconds into 4:23)
    start_min = math.floor(start_time/60)
    start_sec = start_time%60
    
    # The minutes/seconds of the end time, used for the file name
    end_min = math.floor(end_time/60)
    end_sec = end_time%60

    # Determine if you want an alternate file title
    chosenFileName = ""
    if alternateFileName == "":
        chosenFileName = inputFileName
    else:
        chosenFileName = alternateFileName
    
    input_video_address = video_input_directory + inputVideoName
    # Format the output file name
    output_video_name = f"{video_output_directory}[{chosenFileName}]_from_[{inputFileName}]_{start_min}m{start_sec}s--{end_min}m{end_sec}s.mp4"
    
    extract(input_video_address,start_time,end_time,output_video_name)

# Function that takes basic user input (initial/final time stamp) and generates CSV/JSON files accordingly
def saveTimeframe(start_time,end_time): # From X to Y seconds, on the video
    # Calculate which frames to start/end on. Keep in mind that the actual data begins at index 4.
    start_frame = 4 + start_time * frequency
    end_frame = 4 + end_time * frequency

    # The minutes/seconds of the start time, used for the file name (i.e. turn 263 seconds into 4:23)
    start_min = math.floor(start_time/60)
    start_sec = start_time%60
    
    # The minutes/seconds of the end time, used for the file name
    end_min = math.floor(end_time/60)
    end_sec = end_time%60

    # Define the name of the output file, which will look like "C:\Documents\Dir\output_4.23_4.38"
    # Note that the file extensions (.csv and .json) are added in the parse_csv function.
    chosenFileName = ""
    if alternateFileName == "":
        chosenFileName = inputFileName
    else:
        chosenFileName = alternateFileName
    outputname = f"[{chosenFileName}]_from_[{inputFileName}]_{start_min}m{start_sec}s--{end_min}m{end_sec}s"

    # Call the parse_csv function using the data calculated above
    parse_csv(inputfile,outputname,start_frame,end_frame)

    # Call the getTrimmedVideo function to quickly trim the video
    getTrimmedVideo(start_time,end_time)

sample = open(instruction_file,'r')
csv1 = csv.reader(sample,delimiter=",")
next(csv1,None)

# Add headers to CSV output clips
### THIS ^^^

def default_value():
    return 0

dict = defaultdict(default_value)

def getSec(time_string):
    min,sec = time_string.split(":")
    return int(min)*60+float(sec)

if (doClearOutput):
    clearFolder(consolidated_directory)

for line in csv1:
    inputFileName = line[0]
    inputVideoName = line[1]
    start_time0 = getSec(line[2])
    end_time0 = getSec(line[3])
    alternateFileName = line[4].replace(" ","-")

    uniqueCount = dict[alternateFileName]
    dict[alternateFileName] += 1
    if uniqueCount>0:
        alternateFileName += str(uniqueCount)

    newDirectory,success = makeNewDirectory(consolidated_directory,alternateFileName)
    if success:
        video_output_directory = newDirectory
        csv_directory = newDirectory
        saveTimeframe(start_time0,end_time0) # start_time (seconds), end_time (seconds)

print("##################################################")
print("################# TASK COMPLETE #################")
print("##################################################")

# Add option to output data, i.e. how many total tasks, avg length, etc
# More intelligent CSV parsing... Go through it all at once. It's basically O(n^2) rn