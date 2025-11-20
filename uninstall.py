#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import List


APP_NAME: str = "Random Student Picker"
APP_FOLDER_NAME: str = "randomStudentPicker"
MAIN_FILE_NAME: str = "main.py"


def getDesktopDirectory() -> Path:
    homeDirectory: Path = Path.home()
    if sys.platform.startswith("win"):
        userProfile: str = os.environ.get("USERPROFILE", str(homeDirectory))
        desktopDirectory: Path = Path(userProfile) / "Desktop"
    else:
        desktopDirectory = homeDirectory / "Desktop"
    return desktopDirectory


def getBaseDirectory() -> Path:
    homeDirectory: Path = Path.home()
    documentsDirectory: Path = homeDirectory / "Documents"
    baseDirectory: Path = documentsDirectory / APP_FOLDER_NAME
    return baseDirectory


def getShortcutPaths() -> List[Path]:
    shortcutPaths: List[Path] = []
    desktopDirectory: Path = getDesktopDirectory()

    if sys.platform.startswith("win"):

        desktopShortcut: Path = desktopDirectory / f"{APP_NAME}.lnk"
        shortcutPaths.append(desktopShortcut)

        appData: str | None = os.environ.get("APPDATA")
        if appData:
            startMenuDirectory: Path = (Path(appData) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
            startMenuShortcut: Path = startMenuDirectory / f"{APP_NAME}.lnk"
            shortcutPaths.append(startMenuShortcut)

    elif sys.platform.startswith("darwin"):
        desktopShortcut = desktopDirectory / "RandomStudentPicker.command"
        shortcutPaths.append(desktopShortcut)

    else:
        desktopShortcut = desktopDirectory / "RandomStudentPicker.desktop"
        shortcutPaths.append(desktopShortcut)

        applicationsDirectory: Path = (Path.home() / ".local" / "share" / "applications")
        applicationsShortcut: Path = applicationsDirectory / "random-student-picker.desktop"
        shortcutPaths.append(applicationsShortcut)

    return shortcutPaths


def removeFileIfExists(path: Path) -> None:
    if path.exists():
        try:
            path.unlink()
            print(f"Removed file: {path}")
        except Exception as error:
            print(f"Failed to remove file {path}: {error}")


def removeShortcuts() -> None:
    shortcutPaths: List[Path] = getShortcutPaths()
    print("Removing shortcuts (if present):")
    for shortcutPath in shortcutPaths:
        removeFileIfExists(shortcutPath)


def removeBaseDirectory() -> None:
    baseDirectory: Path = getBaseDirectory()

    if not baseDirectory.exists():
        print(f"Base directory does not exist: {baseDirectory}")
        return

    print(f"\nBase application directory to remove: {baseDirectory}")
    try:
        answer: str = input(
            "Delete this folder and all of its contents? [y/N]: "
        ).strip().lower()
    except EOFError:
        answer = "n"

    if answer != "y":
        print("Skipping removal of application directory.")
        return

    try:
        shutil.rmtree(baseDirectory)
        print(f"Removed directory: {baseDirectory}")
    except Exception as error:
        print(f"Failed to remove directory {baseDirectory}: {error}")


def main() -> None:
    print("Uninstalling Random Student Picker.")
    removeShortcuts()
    removeBaseDirectory()

    print("\nUninstall completed. Python packages installed for this app were not removed.")
    print("If you want to uninstall them manually, you can run (on your own responsibility):")
    print("  pip uninstall customtkinter pywin32")


if __name__ == "__main__":
    main()
