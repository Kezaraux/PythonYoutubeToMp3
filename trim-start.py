import sys
import subprocess
import glob
import os

def getFiles():
    for i, file in enumerate(os.listdir("./output")):
        print(str(i) + ") " + file)
    ind = input("Choose a file to be trimmed: ")
    try:
        val = int(ind)
        if (val < 0):
            print("Enter an number from 0 to specified!")
            exit(1)
        else:
            return os.listdir("./output")[int(ind)]
    except ValueError:
        print("Make sure you entered a number!")

def trim(file, amt):
    os.chdir("./output")
    os.getcwd()
    subprocess.call(['ffmpeg', '-i', file, '-ss', str(amt), '-acodec', 'copy', file[:-4] + '-trimmed.mp3'])
    print("Ran the trim on " + file)
    
def main():
    file = getFiles()
    print(file)
    amt = input("Enter number of seconds to be trimmed: ")
    try:
        val = float(amt)
        if (val < 1):
            print("Enter an amount greater than 0!")
            exit(1)
        print("Starting trim!")
        trim(file, val)
        print("Done!")
    except ValueError:
        print("Make sure you entered a number!")

if __name__ == "__main__":
    main()
