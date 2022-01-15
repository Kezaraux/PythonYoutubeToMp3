import sys
import subprocess
import re
import glob
import os
import shutil
import unidecode
import urllib.parse
import youtube_dl as yt
from yt_dlp import YoutubeDL
from googletrans import Translator


#Constants
temp_directory = os.getcwd() + "\\temp"
output_directory = os.getcwd() + "\\output"
ydl_options = {"outtmpl":  "temp/%(title)s-%(id)s.%(ext)s", 'format': 'bestaudio'}
supported_video_extensions = ["*.mkv", "*.mp4", "*.webm"]

#Problem storage
skipped_conversions = []
rename_problems = []
move_problems = []
delete_problems = []

def handle_url(url):
    print("\nAttempting process on url: " + url)
    if (check_id_exists(get_video_id(url))):
        print("\tSkipping mp3 conversion of " + url + " since a song file already exists for it in the output folder.")
        skipped_conversions.append(url)
        return
    download_video(url)
    for file in get_file_glob(supported_video_extensions):
        name_check(file, url)
    for file in get_file_glob(supported_video_extensions):
        convert_to_mp3(file, url)
    for file in get_file_glob(["*.mp3"]):
        move_song_to_output(file, url)
    for file in glob.glob(os.path.join(temp_directory, "*.*")):
        clean_temp_dir(file, url)
    print("\nFinished handling the song for " + url)

def download_video(url):
    print("\tDownloading " + url)
    with YoutubeDL(ydl_options) as ydl:
        ydl.download([url])

def get_video_id(url):
    url_data = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(url_data.query)
    return query["v"][0]

def check_id_exists(video_id):
    for filename in os.listdir(output_directory):
        if video_id in filename:
            return True
    return False

#Only attempts translation if unicode characters are present
#Naive assumption, fails for languages such as French or Spanish
def name_check(file, url):
    print("\tChecking file " + trim_path(file) + " for unicode")
    decoded = unidecode.unidecode(file)
    if (file != decoded):
        print("\tFile had unicode characters, attempting to translate the song")
        translator = Translator()
        try:
            english = translator.translate(file[file.rindex("\\")+1:], dest="en").text
            stripped_english = re.sub(r'[\\/:"*?<>|]+', "", english)
        except Exception as e:
            print("An exception occured while attempting to translate a file name")
            print("\tSkipping translation, continuing with conversion")
            print(e)
            return
        try:
            print("\tRenaming the song to what was determined to be the translation")
            os.rename(os.path.join(temp_directory, file), os.path.join(temp_directory, stripped_english))
        except Exception as e:
            print("An exception occured while attempting to rename a file")
            print(e)
            rename_problems.append((url, e))
            pass
    else:
        print("\tThe song didn't have any unicode characters, no need to attempt translation")

def convert_to_mp3(file, url):
    print("\nChecking if the converted song file already exists...")
    mp3_file = get_mp3_filename(file)
    if os.path.exists(os.path.join(output_directory, mp3_file[mp3_file.rindex("\\")+1:])):
        print("\tSkipping mp3 conversion of " + trim_path(file) + " since a song file already exists for it in the output folder.")
        skipped_conversions.append(url)
    else:
        print("\tAttempting to convert " + trim_path(file) + " to an mp3")
        subprocess.run(args=get_ffmpeg_commands(file), stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        print("\tFinished converting " + trim_path(file))

def move_song_to_output(file, url):
    print("\tAttempting to move " + trim_path(file) + " to the output directory\n")
    try:
        shutil.move(file, output_directory)
        print("\tFinished moving " + trim_path(file))
    except Exception as e:
        print("\tAn exception occured while attempting to move a song to the output directory")
        print(e)
        move_problems.append((url, e))
        pass

def clean_temp_dir(file, url):
    print("\tAttempting to remove " + trim_path(file) + " from the temp directory")
    try:
        os.remove(file)
    except Exception as e:
        print("\tAn exception occured while attempting to delete a file in the temp directory")
        print(e)
        delete_problems.append((url, e))
        pass
    print("\tFinished cleaning up the temp directory")

def relay_errors():
    if (len(skipped_conversions) != 0):
        print("List of URLs that were not converted to an mp3 as an output file for them already existed.")
        for s in skipped_conversions:
            print("\t" + s)
            #print(s + " was not converted to an mp3 since an output file already existed for it.")
    if len(rename_problems) != 0:
        for problem in rename_problems:
            print("\nAn issue occured with url " + problem[0] + " while attempting to rename it due to translation.\n")
            print(problem[1])
            print("\tPlease double check that you have an output for this url.")
            print("\tEnsure the temp directory is empty and try converting this song again.")
    if len(move_problems) != 0:
        for problem in move_problems:
            print("\nAn issue occured with url " + problem[0] + " while attempting to move it to the output directory.\n")
            print(problem[1])
            print("\tA copy of this song might already exist there, please double check this.")
            print("\tIf there is no output, ensure the temp directory is empty and try conversion again.")
    if len(delete_problems) != 0:
        for problem in delete_problems:
            print("\nAn issue occured with url " + problem[0] + " while attempting to delete its files in the temp directory.\n")
            print(problem[1])
            print("\tIf there are any files remaining in the temp directory, please delete them.")

def get_mp3_filename(file):
    return file[:file.rindex(".")] + ".mp3"

def get_ffmpeg_commands(file):
    return [
        'ffmpeg',
        '-n',
        '-i',
        file,
        '-f',
        'mp3',
        '-ab',
        '192000',
        '-af',
        'silenceremove=stop_periods=-1:stop_duration=1:stop_threshold=-90dB',
        '-vn',
        get_mp3_filename(file)
    ]

def get_file_glob(extensions):
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(temp_directory, ext)))
    return files
    
def trim_path(file):
    return file.split("\\")[-1]
        
if __name__ == "__main__":
    if not os.path.exists(temp_directory):
        print("The temp directory does not exist, creating it now.")
        os.makedirs(temp_directory)
    if not os.path.exists(output_directory):
        print("The output directory does not exist, creating it now.")
        os.makedirs(output_directory)
    urls = sys.argv[1:]
    for url in urls:
        handle_url(url)
    # This commented out code is for the old slightly more efficient method without error reporting
    # download_video(sys.argv[1:])
    # handle_unicode()
    # convert_videos_to_mp3_and_cleanup(get_file_glob(supported_video_extensions))
    relay_errors()
    input("Press enter to exit")


# def handle_unicode():
#     print("\nChecking downloaded files for unicode\n")
#     for file in os.listdir(temp_directory):
#         decoded = unidecode.unidecode(file)
#         if (file != decoded):
#             print("\tFile had unicode, attempting to translate")
#             translator = Translator()
#             english = translator.translate(file, dest="en").text
#             stripped_english = re.sub(r'[\\/:"*?<>|]+', "", english)
#             try:
#                 print("\tRenaming the file " + file)
#                 os.rename(os.path.join(temp_directory, file), os.path.join(temp_directory, stripped_english))
#             except Exception as e:
#                 print("\tAn exception occured while attempting to rename a file")
#                 print(e)
#                 print("Skipping " + file)
#                 pass
#         else:
#             print("\tNo unicode, moving to the next file")

# def convert_videos_to_mp3_and_cleanup(file_glob):
#     print("\nAttempting to convert videos in the temp directory to music files\n")
#     for file in file_glob:
#         print("\tConverting " + file + " to an mp3")
#         subprocess.run(get_ffmpeg_commands(file))
#         print("\tFinished conversion, moving to next file")
#     print("\nFinished converting all files\n")
#     print("Attempting to move songs to the output directory\n")
#     try:
#         for file in glob.glob(os.path.join(temp_directory, "*.mp3")):
#             shutil.move(file, output_directory)
#     except Exception as e:
#         print("\tAn exception occured while attempting to move a song to the output directory")
#         print(e)
#         pass
#     print("\nAttempting to clean up the temp directory\n")
#     try:
#         for file in glob.glob(os.path.join(temp_directory, "*.*")):
#             os.remove(file)
#     except Exception as e:
#         print("\tAn exception occured while attempting to delete a file in the temp directory")
#         print(e)
#         pass
#     print("Finished cleaning up the temp directory")
