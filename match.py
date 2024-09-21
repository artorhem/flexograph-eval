import re
import sys
# Define the regex pattern
regex = r"^(Read|Build|Trial)\sTime:\s+(\d+\.\d+)"


# Open the file in read mode
#the input will be piped in from the command line
input = sys.stdin.read()
# with open('/home/puneet/scratch/gapbs/pr.txt', 'r') as file:
#     # Read the content of the file
#     content = file.read()

# Search for all occurrences of the regex pattern
matches = re.finditer(regex, input, re.MULTILINE)

# Print the matches
read_times = [] 
build_times = []
trial_times = []
for match in matches:
    #we want to print the sum of times if the first element of the tuple is 'Read' or 'Build'
    if match.group(1) == 'Read':
        read_times.append(float(match.group(2)))
    elif match.group(1) == 'Build':
        build_times.append(float(match.group(2)))
    else:
        trial_times.append(float(match.group(2)))

print("Average Read Time: ", sum(read_times)/len(read_times))
print("Average Build Time: ", sum(build_times)/len(build_times))
print("Average Trial Time: ", sum(trial_times)/len(trial_times))