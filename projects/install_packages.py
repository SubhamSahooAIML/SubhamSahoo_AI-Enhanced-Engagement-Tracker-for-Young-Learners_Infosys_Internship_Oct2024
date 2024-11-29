import subprocess
import sys

# Define the libraries and their required versions
libraries = {
    'tkinter': None,  # Part of the standard library, no need to install
    'Pillow': '8.3.1',
    'opencv-python': '4.10.0',
    'face_recognition': '1.2.3',
    'dlib': '19.24.6',
    'pandas': '2.2.3',
    'numpy': '2.1.2',
    'datetime': None,  # Part of the standard library, no need to install
    'os': None,  # Part of the standard library, no need to install
    'winsound': None,  # Part of the standard library, no need to install
    'subprocess': None,  # Part of the standard library, no need to install
    'ttkthemes': '3.2.2',
    'keyboard': '0.13.5',
    'time': None,  # Part of the standard library, no need to install
    'threading': None,  # Part of the standard library, no need to install
    'pywin32': '303',  # For win32api, win32con, and win32gui
}

# Function to install packages using pip
def install_package(package, version=None):
    try:
        if version:
            subprocess.check_call([sys.executable, "-m", "pip", "install", f"{package}=={version}"])
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError as e:
        print(f"Error installing package {package}: {e}")

# Install the required libraries
for lib, ver in libraries.items():
    if ver:
        install_package(lib, ver)
    elif lib:  # If no version specified, install the latest
        install_package(lib)

print("All required packages have been installed successfully.")
 