import json

with open("2024-06-28-action-noodle.json", "r") as infile:
    d = json.load(infile)

print(len(d))
for a in d:
    if type(a["sequence"]) is list:
        a["sequence"] = a["sequence"][0]

json_object = json.dumps(d, indent=4)

with open("2024-06-28-action-noodle.json", "w") as outfile:
    outfile.write(json_object)