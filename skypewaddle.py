#for print style
#import os

import json

# Opening JSON file
f = open('messages.json',"r",encoding='utf-8')

# returns JSON object as
# a dictionary
data = json.load(f)

def extract_values(obj, key):
    """Pull all values of specified key from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    results = extract(obj, arr, key)
    return results

def extract_durations(obj):
    arr = []
    days = 0
    for item in obj:
        beg_duration = item.find("<duration>")
        end_duration= item.find("</duration>")
        if (beg_duration!=-1 & end_duration !=-1):
            duration = float(item[beg_duration+10:end_duration])
            days += duration
            arr.append(duration)
    return arr, days/60/60/24

"""extract message content into array"""
#begin recursion
message_content=extract_values(data, "content")

"""extract call durations"""
durations, days = extract_durations(message_content)
print(durations)
print("Number of calls: ",len(durations))
print("Total skype-time in days: ",days)
print("That is " + str(round(days*24,2)) + " hours!")
print("     or " + str(round(days*24*60)) + " days!")
print("        " + str(round(days*24*60*60)) + " seconds!")
# Closing file
f.close()
