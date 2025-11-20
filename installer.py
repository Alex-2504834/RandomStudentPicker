#!/usr/bin/env python3
from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Optional

import urllib.request


RAW_MAIN_URL: str = ("https://raw.githubusercontent.com/Alex-2504834/RandomStudentPicker/main/main.py")

REQUIREMENTS_CONTENT: str = """
customtkinter>=5.2,<6
pywin32>=306; platform_system == "Windows"
"""

APP_NAME: str = "Random Student Picker"
APP_FOLDER_NAME: str = "randomStudentPicker"
MAIN_FILE_NAME: str = "main.py"

def downloadFile(url: str, destinationPath: Path) -> bool:
    print(f"Downloading: {url}")
    try:
        urllib.request.urlretrieve(url, destinationPath)
        print(f"Saved to: {destinationPath}")
        return True
    except Exception as error:
        print(f"Failed to download {url}: {error}")
        return False

def writeFile(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    print(f"Wrote file: {path}")

def pipInstallRequirements(requirementsFile: Path) -> None:
    print("\nInstalling Python dependencies...\n")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirementsFile)])
        print("\nDependencies installed successfully.\n")
    except subprocess.CalledProcessError as error:
        print(f"Failed to install dependencies: {error}")
        print("You may need to run pip manually:")
        print(f"  {sys.executable} -m pip install -r {requirementsFile}")


def getDesktopDirectory() -> Path:
    homeDirectory: Path = Path.home()
    if sys.platform.startswith("win"):
        userProfile: str = os.environ.get("USERPROFILE", str(homeDirectory))
        desktopDirectory: Path = Path(userProfile) / "Desktop"
    else:
        desktopDirectory = homeDirectory / "Desktop"
    return desktopDirectory


def createWindowsShortcutLnk(
    shortcutPath: Path, targetScript: Path, workingDirectory: Path) -> None:
    try:
        import win32com.client
    except ImportError:
        print("pywin32 is not installed; cannot create .lnk shortcut.")
        return

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcutPath))

    shortcut.TargetPath = str(sys.executable)
    shortcut.Arguments = f'"{targetScript}"'
    shortcut.WorkingDirectory = str(workingDirectory)

    shortcut.Save()
    print(f"Created Windows shortcut: {shortcutPath}")

def createDesktopShortcut(mainPyPath: Path, appDirectory: Path) -> None:
    desktopDirectory: Path = getDesktopDirectory()
    desktopDirectory.mkdir(parents=True, exist_ok=True)

    if sys.platform.startswith("win"):
        shortcutPath: Path = desktopDirectory / f"{APP_NAME}.lnk"
        createWindowsShortcutLnk(shortcutPath, mainPyPath, appDirectory)

    elif sys.platform.startswith("darwin"):
        shortcutPath = desktopDirectory / "RandomStudentPicker.command"
        scriptContent: str = (
            f'#!/bin/bash\n'
            f'cd "{appDirectory}"\n'
            f'"{sys.executable}" "{mainPyPath.name}"\n'
        )
        writeFile(shortcutPath, scriptContent)
        shortcutPath.chmod(
            shortcutPath.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"Created macOS launcher: {shortcutPath}")

    else:
        shortcutPath = desktopDirectory / "RandomStudentPicker.desktop"
        desktopEntry: str = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={APP_NAME}\n"
            f'Exec="{sys.executable}" "{mainPyPath}"\n'
            "Terminal=false\n"
            "Categories=Education;\n"
        )
        writeFile(shortcutPath, desktopEntry)
        shortcutPath.chmod(shortcutPath.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"Created Linux .desktop launcher: {shortcutPath}")


def createStartMenuEntry(mainPyPath: Path, appDirectory: Path) -> None:
    if sys.platform.startswith("win"):
        appData: Optional[str] = os.environ.get("APPDATA")
        if not appData:
            print("Could not locate APPDATA; skipping Start Menu entry.")
            return

        startMenuDirectory: Path = (Path(appData) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
        startMenuDirectory.mkdir(parents=True, exist_ok=True)

        shortcutPath: Path = startMenuDirectory / f"{APP_NAME}.lnk"
        createWindowsShortcutLnk(shortcutPath, mainPyPath, appDirectory)

    elif sys.platform.startswith("darwin"):
        print("macOS does not have a simple Start Menu equivalent. Skipping.")
        return

    else:
        applicationsDirectory: Path = (Path.home() / ".local" / "share" / "applications")
        applicationsDirectory.mkdir(parents=True, exist_ok=True)

        shortcutPath = applicationsDirectory / "random-student-picker.desktop"
        desktopEntry: str = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={APP_NAME}\n"
            f'Exec="{sys.executable}" "{mainPyPath}"\n'
            "Terminal=false\n"
            "Categories=Education;\n"
        )
        writeFile(shortcutPath, desktopEntry)
        shortcutPath.chmod(shortcutPath.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        print(f"Created application menu entry: {shortcutPath}")
        print("You may need to log out and back in, or refresh your desktop environment, for it to appear.")


def main() -> None:
    homeDirectory: Path = Path.home()
    documentsDirectory: Path = homeDirectory / "Documents"
    baseDirectory: Path = documentsDirectory / APP_FOLDER_NAME
    classesDirectory: Path = baseDirectory / "classes"
    mainPyPath: Path = baseDirectory / MAIN_FILE_NAME
    requirementsPath: Path = baseDirectory / "requirements.txt"

    print(f"Installing {APP_NAME} to: {baseDirectory}")

    classesDirectory.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {baseDirectory}")
    print(f"Created directory: {classesDirectory}")

    print("\nDownloading main.py...")
    if not downloadFile(RAW_MAIN_URL, mainPyPath):
        sys.exit(1)

    print("\nWriting requirements.txt...")
    writeFile(requirementsPath, REQUIREMENTS_CONTENT)

    pipInstallRequirements(requirementsPath)

    try:
        answerDesktop: str = input("\nCreate a Desktop shortcut? [y/N]: ").strip().lower()
    except EOFError:
        answerDesktop = "n"

    if answerDesktop == "y":
        createDesktopShortcut(mainPyPath, baseDirectory)

    try:
        answerMenu: str = input("Create a Start Menu / application menu entry? [y/N]: ").strip().lower()
    except EOFError:
        answerMenu = "n"

    if answerMenu == "y":
        createStartMenuEntry(mainPyPath, baseDirectory)

    print("\nInstallation complete.")
    print("\nYou can run the application with:")
    print(f"  {sys.executable} {mainPyPath}\n")
    print("Place your .json or .csv class files in:")
    print(f"  {classesDirectory}\n")


if __name__ == "__main__":
    main()
