import os
import glob

output_directory = os.getcwd() + "\\output"

def rename_files(files):
    for file in files:
        if (file[-16] == "-"):
            newName = file[:-16] + file[-4:] 
            os.rename(file, newName)

if __name__ == "__main__":
    print("Gathering files to remove video ID from")
    files = glob.glob(os.path.join(output_directory, "*"))
    with_id = list(filter(lambda f: f[-16] == "-", files))
    print("Found " + str(len(with_id)) + " to work on")
    if (len(with_id) == 0):
        print("Nothing to do here, bye!")
    else:
        rename_files(files)
        print("Done renaming files!")
