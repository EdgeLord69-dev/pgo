#! /usr/bin/env python3
import argparse
import configparser
import glob
import os
import random
import string
import subprocess


if not os.path.exists("encode_settings.conf"):
    print("encode_settings.conf not found.")
    exit(1)

# Setup the config parser and read the config file.
config = configparser.ConfigParser()
config.read("encode_settings.conf")

# Setup the argument parser.
parser = argparse.ArgumentParser()
parser.add_argument(
    "--svt-repo", required=True, help="The path to the SVT-AV1 repository."
)
# parser.add_argument("--bolt", required=True, help="Whether or not to use BOLT.")
args = parser.parse_args()


def get_objective_folder() -> str | None:
    """Returns the full path to the objective-* folder if it exists."""

    obj_folder: list[str] = glob.glob(f"{os.getcwd()}/objective-*")
    if obj_folder != []:
        return obj_folder[0]
    else:
        return None


# video-input folder

# objective folder
objective_folder: str | None = get_objective_folder()

# video file extensions to look for
file_extensions: list[str] = [".mkv", ".mp4", ".y4m"]

# Store the encode settings in a dictionary.
svt_settings = {}
for section in config.sections():
    for key, value in config.items("svt-settings"):
        svt_settings[key] = value


def random_string() -> str:
    """Returns a random string of 5 characters."""
    return "".join([random.choice(string.ascii_letters) for _ in range(5)])


def av1an(svt_options: str, workers: int, file_path: str, iteration: int) -> None:
    # Form the av1an command.
    # ? Does Av1an make sense? FFMpeg would work too, and not require installing Av1an + it's deps.
    av1an_cmd = f"ffmpeg -i {file_path} -map 0:v:0 -f yuv4mpegpipe -strict -1 - | SvtAv1EncApp -i stdin -b {file_path}.{iteration}.ivf {svt_options}"

    # If the user has set a custom number of workers, add it to the command.

    # Add the new svt-av1 binary to the $PATH
    # Wished Av1an allowed for the user to set the binary path.
    env: dict[str, str] = os.environ.copy()
    env["PATH"] = f"{args.svt_repo}/Bin/Release:{env['PATH']}"

    subprocess.run(av1an_cmd, env=env, shell=True)
    
    if os.path.exists(f"{file_path}.{iteration}.ivf"):
        os.remove(f"{file_path}.{iteration}.ivf")


def main() -> None:
    """Runs Av1an on all files in either the user input folder or the objective-* folder."""
    directories = []

    if objective_folder is None:
        # If objective folder is not found, use the user input folder.
       print("Download XIPH Test archives")
    else:
        # If objective folder is found, use it, along with the user input folder.
        directories.append(objective_folder)

    for directory in directories:
        length = len(os.listdir(directory))
        for file_path in glob.glob(os.path.join(os.getcwd(), directory, "*")):
            done = False
            if any(file_path.endswith(ext) for ext in file_extensions) and done == False:
                iter = 0
                for command in svt_settings:
                    if iter <= length:
                        iter += 1
                        av1an(
                            svt_options=svt_settings[command].replace('"', ""),
                            workers=config.getint("av1an-settings", "AV1AN_WORKERS"),
                            file_path=file_path,
                            iteration=iter,
                        )
                    else:
                        done = True
                        break
            else:
                break

if __name__ == "__main__":
    main()
else:
    print("main not detected")
