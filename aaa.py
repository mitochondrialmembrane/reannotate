import json

string = "tablet/2024-08-26-action-angela-tablet.json"

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