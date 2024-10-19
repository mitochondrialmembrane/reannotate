import json

string = "matcher/laptop/2024-09-23-action-sudarshan-laptop2.json"

with open(string, "r") as infile:
    d = json.load(infile)

print(len(d))
for a in d:
    x = a["annotation"].split("\t")
    if len(x) > 1:
        a["annotation"] = x[1]

json_object = json.dumps(d, indent=4)

with open(string, "w") as outfile:
    outfile.write(json_object)