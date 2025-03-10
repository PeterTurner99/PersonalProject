import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent


def run_tailwind_watch():
    print("Starting Tailwind CSS watcher...\n")
    global tailwind_process
    tailwind = BASE_DIR / "tailwind.exe"
    input_file = BASE_DIR / "firstProjectApp" / "static" / "firstProjectApp" / "css" / "input.css"
    output_file = BASE_DIR / "firstProjectApp" / "static" / "firstProjectApp" / "css" / "output.css"
    tailwind_process = subprocess.Popen(
        f"{tailwind} -i {input_file} -o {output_file} --watch",
        shell=True,

    )


run_tailwind_watch()
