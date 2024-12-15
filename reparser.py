import json
import os

root_folder = "reannotate/reannotation_tmp"

# Loop through all subfolders and files
for dirpath, dirnames, filenames in os.walk(root_folder):
    for file in filenames:
        if file.endswith(".json"):  # Check if the file is a JSON file
            try:
                file_path = os.path.join(dirpath, file)  # Get the full path to the file
                
                with open(file_path, "r") as infile:
                    d = json.load(infile)

                for a in d:
                    print(a)
                    x = a["annotation"].split("\t")
                    if len(x) > 1:
                        a["annotation"] = x[1]

                json_object = json.dumps(d, indent=4)

                with open(file_path, "w") as outfile:
                    outfile.write(json_object)
            except:
                continue