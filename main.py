from __future__ import annotations

import csv
import json
import random
import traceback
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

import customtkinter as ctk
from tkinter import messagebox


@dataclass
class Student:
    name: str
    weight: float = 0.5
    count: int = 0


@dataclass
class AppSettings:
    appearanceMode: str = "dark"
    colorTheme: str = "blue"
    weightDecreaseAmount: float = 0.1
    spinnerSpeedValue: float = 50.0
    selectedClassFileName: str = ""


def getSettingsFilePath() -> Path:
    homeDirectoryPath: Path = Path.home()
    documentsDirectoryPath: Path = homeDirectoryPath / "Documents"
    settingsDirectoryPath: Path = documentsDirectoryPath / "randomStudentPicker"
    settingsDirectoryPath.mkdir(parents=True, exist_ok=True)
    settingsFilePath: Path = settingsDirectoryPath / "settings.json"
    return settingsFilePath


def getClassesDirectoryPath() -> Path:
    settingsDirectoryPath: Path = getSettingsFilePath().parent
    classesDirectoryPath: Path = settingsDirectoryPath / "classes"
    classesDirectoryPath.mkdir(parents=True, exist_ok=True)
    return classesDirectoryPath


def loadAppSettingsFromDisk() -> AppSettings:
    settingsFilePath: Path = getSettingsFilePath()

    if not settingsFilePath.exists():
        return AppSettings()

    try:
        with settingsFilePath.open("r", encoding="utf-8") as settingsFile:
            rawData = json.load(settingsFile)

        return AppSettings(
            appearanceMode=str(rawData.get("appearanceMode", "dark")),
            colorTheme=str(rawData.get("colorTheme", "blue")),
            weightDecreaseAmount=float(rawData.get("weightDecreaseAmount", 0.1)),
            spinnerSpeedValue=float(rawData.get("spinnerSpeedValue", 50.0)),
            selectedClassFileName=str(rawData.get("selectedClassFileName", "")),
        )
    except Exception as e:
        print("Error loading app settings:", e)
        traceback.print_exc()
        return AppSettings()


def saveAppSettingsToDisk(appSettings: AppSettings) -> None:
    settingsFilePath: Path = getSettingsFilePath()
    try:
        with settingsFilePath.open("w", encoding="utf-8") as settingsFile:
            json.dump(asdict(appSettings), settingsFile, indent=4)
    except Exception as e:
        print("Error saving app settings:", e)
        traceback.print_exc()


class StudentManager:
    def __init__(self, studentDictionary: Optional[Dict[int, Student]] = None) -> None:
        if studentDictionary is None:
            studentDictionary = {}
        self.studentDictionary: Dict[int, Student] = studentDictionary
        self.weightDecreaseAmount: float = 0.1

    def pickRandomStudent(self) -> Optional[Student]:
        activeStudentList: List[Student] = [student for student in self.studentDictionary.values() if student.weight > 0.0]
        if not activeStudentList:
            return None

        weightList: List[float] = [student.weight for student in activeStudentList]
        selectedStudent: Student = random.choices(population=activeStudentList, weights=weightList, k=1)[0]

        selectedStudent.count += 1
        selectedStudent.weight = max(selectedStudent.weight - self.weightDecreaseAmount, 0.0)

        return selectedStudent

    def getStudentNameList(self) -> List[str]:
        return [student.name for student in self.studentDictionary.values()]

    def resetAllStudents(self, defaultWeight: float = 0.5) -> None:
        for student in self.studentDictionary.values():
            student.count = 0
            student.weight = defaultWeight

    def resetAllWeights(self, defaultWeight: float = 0.5) -> None:
        for student in self.studentDictionary.values():
            student.weight = defaultWeight

    def getStudentSummaryLines(self) -> List[str]:
        summaryLineList: List[str] = []
        for student in self.studentDictionary.values():
            summaryLine: str = f"{student.name}: picks={student.count}, weight={student.weight:.2f}"
            summaryLineList.append(summaryLine)
        return summaryLineList

    def setStudentsFromList(self, studentList: List[Student]) -> None:
        self.studentDictionary = {index: student for index, student in enumerate(studentList)}


class RandomStudentPickerApp(ctk.CTk):
    def __init__(self, studentManager: StudentManager) -> None:
        super().__init__()

        self.studentManager: StudentManager = studentManager
        self.appSettings: AppSettings = loadAppSettingsFromDisk()

        self.currentStudentFilePath: Optional[Path] = None
        self.currentStudentFileType: Optional[str] = None

        self.classDropdownPlaceholderText: str = "Select class file..."
        self.classFileOptions: Dict[str, Path] = {}

        self.resetWeightsButtonVisible: bool = False

        ctk.set_appearance_mode(self.appSettings.appearanceMode)
        ctk.set_default_color_theme(self.appSettings.colorTheme)

        self.currentAppearanceMode: str = self.appSettings.appearanceMode
        self.currentColorTheme: str = self.appSettings.colorTheme

        self.studentManager.weightDecreaseAmount = self.appSettings.weightDecreaseAmount

        self.title("Random Student Picker")
        self.geometry("1000x550")

        self.protocol("WM_DELETE_WINDOW", self.onWindowClosing)

        self.baseMinDelaySlowMilliseconds: int = 80
        self.baseMinDelayFastMilliseconds: int = 10
        self.baseMaxDelaySlowMilliseconds: int = 400
        self.baseMaxDelayFastMilliseconds: int = 80

        self.minimumSpinDelayMilliseconds: int = 30
        self.maximumSpinDelayMilliseconds: int = 220

        self.updateSpinnerDelaysFromSpeed(self.appSettings.spinnerSpeedValue)

        self.tabView: ctk.CTkTabview = ctk.CTkTabview(self)
        self.tabView.pack(expand=True, fill="both", padx=10, pady=10)

        self.tabView.add("Instant")
        self.tabView.add("Spinner")
        self.tabView.add("Stats")
        self.tabView.add("Settings")

        self.instantTabFrame: ctk.CTkFrame = self.tabView.tab("Instant")
        self.spinnerTabFrame: ctk.CTkFrame = self.tabView.tab("Spinner")
        self.statsTabFrame: ctk.CTkFrame = self.tabView.tab("Stats")
        self.settingsTabFrame: ctk.CTkFrame = self.tabView.tab("Settings")

        self.buildInstantTab()
        self.buildSpinnerTab()
        self.buildStatsTab()
        self.buildSettingsTab()

        self.refreshClassFileList()
        self.autoLoadSavedClassIfAvailable()
        self.updateUiForStudentAvailability()

    def buildInstantTab(self) -> None:
        self.instantSelectedStudentLabel: ctk.CTkLabel = ctk.CTkLabel(master=self.instantTabFrame, text="No students loaded.\nChoose a class list in Settings.", font=("Arial", 22))
        self.instantSelectedStudentLabel.pack(pady=30)

        self.instantPickStudentButton: ctk.CTkButton = ctk.CTkButton(master=self.instantTabFrame, text="Pick Student", command=self.onInstantPickStudentButtonClicked, font=("Arial", 20), width=200, height=50)
        self.instantPickStudentButton.pack(pady=10)

        self.resetWeightsButton: ctk.CTkButton = ctk.CTkButton(master=self.instantTabFrame, text="Reset weights", command=self.onResetWeightsButtonClicked, font=("Arial", 14))

        self.openSettingsForClassButton: ctk.CTkButton = ctk.CTkButton(master=self.instantTabFrame, text="Choose class list in Settings", command=self.goToSettingsAndHighlightClassSection, font=("Arial", 14))
        self.openSettingsForClassButton.pack(pady=10)

    def onInstantPickStudentButtonClicked(self) -> None:
        if not self.studentManager.studentDictionary:
            self.goToSettingsAndHighlightClassSection()
            return

        selectedStudent: Optional[Student] = self.studentManager.pickRandomStudent()

        if selectedStudent is None:
            self.instantSelectedStudentLabel.configure(text="All student weights are 0.\nNo one left to pick!")
            self.instantPickStudentButton.configure(state="disabled")
            self.spinnerPickStudentButton.configure(state="disabled")
            self.showResetWeightsButton()
            return

        self.instantSelectedStudentLabel.configure(text=f"Selected: {selectedStudent.name}")

        self.refreshStatsTab()

        if self.allWeightsZero():
            self.instantPickStudentButton.configure(state="disabled")
            self.spinnerPickStudentButton.configure(state="disabled")
            self.showResetWeightsButton()

    def buildSpinnerTab(self) -> None:
        self.slotCount: int = 7
        self.centerSlotIndex: int = self.slotCount // 2

        self.isSpinning: bool = False
        self.currentSpinFrameIndex: int = 0
        self.totalSpinFrameCount: int = 60

        self.spinNameList: List[str] = []
        self.currentCenterNameIndex: int = 0
        self.selectedStudentForSpin: Optional[Student] = None

        self.slotFrames: List[ctk.CTkFrame] = []
        self.slotLabels: List[ctk.CTkLabel] = []

        self.spinnerSlotStripFrame: ctk.CTkFrame = ctk.CTkFrame(master=self.spinnerTabFrame)
        self.spinnerSlotStripFrame.pack(pady=30)

        self.buildSpinnerSlotFrames()

        self.spinnerSelectedStudentLabel: ctk.CTkLabel = ctk.CTkLabel(master=self.spinnerTabFrame, text="No student selected yet.", font=("Arial", 18))
        self.spinnerSelectedStudentLabel.pack(pady=5)

        self.spinnerPickStudentButton: ctk.CTkButton = ctk.CTkButton(master=self.spinnerTabFrame, text="Spin", command=self.onSpinnerPickStudentButtonClicked, font=("Arial", 20), width=200, height=50)
        self.spinnerPickStudentButton.pack(pady=10)

        self.initializeSpinNameList()
        self.updateSpinnerSlotLabelsFromCenterIndex()

    def buildSpinnerSlotFrames(self) -> None:
        for columnIndex in range(self.slotCount):
            slotFrame: ctk.CTkFrame = ctk.CTkFrame(master=self.spinnerSlotStripFrame, corner_radius=12, border_width=2, border_color="gray50")
            slotFrame.grid(row=0, column=columnIndex, padx=8, pady=8, sticky="nsew")

            slotLabel: ctk.CTkLabel = ctk.CTkLabel(master=slotFrame, text="", font=("Arial", 18), width=120, height=50, anchor="center")
            slotLabel.pack(expand=True, fill="both", padx=4, pady=4)

            self.slotFrames.append(slotFrame)
            self.slotLabels.append(slotLabel)

        for columnIndex in range(self.slotCount):
            self.spinnerSlotStripFrame.grid_columnconfigure(columnIndex, weight=1)

    def initializeSpinNameList(self) -> None:
        studentNameList: List[str] = self.studentManager.getStudentNameList()
        if not studentNameList:
            self.spinNameList = []
        else:
            repeatCount: int = 10
            self.spinNameList = studentNameList * repeatCount

        self.currentCenterNameIndex = 0

    def updateSpinnerSlotLabelsFromCenterIndex(self) -> None:
        if not self.spinNameList:
            for label in self.slotLabels:
                label.configure(text="No students")
            return

        totalNames: int = len(self.spinNameList)

        for slotIndex in range(self.slotCount):
            offsetFromCenter: int = slotIndex - self.centerSlotIndex
            nameIndex: int = (self.currentCenterNameIndex + offsetFromCenter) % totalNames
            studentName: str = self.spinNameList[nameIndex]

            label: ctk.CTkLabel = self.slotLabels[slotIndex]
            frame: ctk.CTkFrame = self.slotFrames[slotIndex]

            if slotIndex == self.centerSlotIndex:
                frame.configure(border_color="yellow")
                label.configure(font=("Arial", 20, "bold"))
            else:
                frame.configure(border_color="gray50")
                label.configure(font=("Arial", 18, "normal"))

            label.configure(text=studentName)

    def onSpinnerPickStudentButtonClicked(self) -> None:
        if not self.studentManager.studentDictionary:
            self.goToSettingsAndHighlightClassSection()
            return

        if self.isSpinning:
            return

        selectedStudent: Optional[Student] = self.studentManager.pickRandomStudent()

        if selectedStudent is None:
            self.spinnerSelectedStudentLabel.configure(text="All student weights are 0.\nNo one left to pick!")
            self.spinnerPickStudentButton.configure(state="disabled")
            self.instantPickStudentButton.configure(state="disabled")
            self.showResetWeightsButton()
            return

        self.selectedStudentForSpin = selectedStudent
        self.startSpinnerSpinAnimation()

        self.refreshStatsTab()

        if self.allWeightsZero():
            self.spinnerPickStudentButton.configure(state="disabled")
            self.instantPickStudentButton.configure(state="disabled")
            self.showResetWeightsButton()

    def startSpinnerSpinAnimation(self) -> None:
        self.isSpinning = True
        self.spinnerPickStudentButton.configure(state="disabled")
        self.currentSpinFrameIndex = 0

        totalNames = len(self.spinNameList)

        if totalNames > 0:
            self.currentCenterNameIndex = random.randint(0, totalNames - 1)

            if self.selectedStudentForSpin is not None:
                targetName = self.selectedStudentForSpin.name
                indices = [i for i, name in enumerate(self.spinNameList) if name == targetName]

                if indices:
                    def forwardDistance(targetIndex: int, startIndex: int, size: int) -> int:
                        return (targetIndex - startIndex) % size

                    minForward = min(forwardDistance(idx, self.currentCenterNameIndex, totalNames) for idx in indices)
                    minFullSpins = 2
                    self.totalSpinFrameCount = minFullSpins * totalNames + minForward
                else:
                    self.totalSpinFrameCount = totalNames * 2
            else:
                self.totalSpinFrameCount = totalNames * 2
        else:
            self.totalSpinFrameCount = 0

        self.animateSpinnerSpinFrame()

    def animateSpinnerSpinFrame(self) -> None:
        if self.currentSpinFrameIndex >= self.totalSpinFrameCount:
            self.finishSpinnerSpinAnimation()
            return

        if not self.spinNameList:
            self.finishSpinnerSpinAnimation()
            return

        self.currentCenterNameIndex = (self.currentCenterNameIndex + 1) % len(self.spinNameList)
        self.updateSpinnerSlotLabelsFromCenterIndex()

        progress: float = self.currentSpinFrameIndex / float(self.totalSpinFrameCount) if self.totalSpinFrameCount > 0 else 1.0
        delayRange: int = self.maximumSpinDelayMilliseconds - self.minimumSpinDelayMilliseconds
        currentDelay: int = int(self.minimumSpinDelayMilliseconds + delayRange * (progress ** 2))

        self.currentSpinFrameIndex += 1
        self.after(currentDelay, self.animateSpinnerSpinFrame)

    def finishSpinnerSpinAnimation(self) -> None:
        if self.selectedStudentForSpin is not None and self.spinNameList:
            centerLabel: ctk.CTkLabel = self.slotLabels[self.centerSlotIndex]
            centerFrame: ctk.CTkFrame = self.slotFrames[self.centerSlotIndex]

            centerFrame.configure(border_color="lime")
            centerLabel.configure(text=self.selectedStudentForSpin.name, font=("Arial", 22, "bold"))

            self.spinnerSelectedStudentLabel.configure(text=f"Selected: {self.selectedStudentForSpin.name}")

        self.isSpinning = False
        self.spinnerPickStudentButton.configure(state="normal")

    def buildStatsTab(self) -> None:
        self.statsLabel: ctk.CTkLabel = ctk.CTkLabel(master=self.statsTabFrame, text="No students loaded.\nChoose a class list in the Settings tab.", font=("Consolas", 14), justify="left")
        self.statsLabel.pack(pady=20, padx=10, anchor="w")

        self.statsButtonFrame: ctk.CTkFrame = ctk.CTkFrame(master=self.statsTabFrame)
        self.statsButtonFrame.pack(pady=10)

        self.refreshStatsButton: ctk.CTkButton = ctk.CTkButton(master=self.statsButtonFrame, text="Refresh Stats", command=self.refreshStatsTab, font=("Arial", 16))
        self.refreshStatsButton.grid(row=0, column=0, padx=10)

        self.resetStatsButton: ctk.CTkButton = ctk.CTkButton(master=self.statsButtonFrame, text="Reset Weights & Counts", command=self.onResetStatsButtonClicked, font=("Arial", 16))
        self.resetStatsButton.grid(row=0, column=1, padx=10)

        self.refreshStatsTab()

    def refreshStatsTab(self) -> None:
        if not self.studentManager.studentDictionary:
            self.statsLabel.configure(text="No students loaded.\nChoose a class list in the Settings tab.")
            return

        nameWidth: int = 20
        picksWidth: int = 7
        weightWidth: int = 8

        header: str = f"{'Name':<{nameWidth}} {'Picks':>{picksWidth}} {'Weight':>{weightWidth}}"
        separator: str = "─" * len(header)

        lineList: List[str] = [header, separator]

        for student in self.studentManager.studentDictionary.values():
            line: str = f"{student.name:<{nameWidth}} {student.count:>{picksWidth}d} {student.weight:>{weightWidth}.2f}"
            lineList.append(line)

        statsText: str = "\n".join(lineList)
        self.statsLabel.configure(text=statsText)

    def onResetStatsButtonClicked(self) -> None:
        self.studentManager.resetAllStudents(defaultWeight=0.5)

        self.initializeSpinNameList()
        self.updateSpinnerSlotLabelsFromCenterIndex()

        self.refreshStatsTab()

        self.instantSelectedStudentLabel.configure(text="Press the button to pick a student instantly.")
        self.spinnerSelectedStudentLabel.configure(text="No student selected yet.")

        self.instantPickStudentButton.configure(state="normal")
        self.spinnerPickStudentButton.configure(state="normal")
        self.hideResetWeightsButton()

    def allWeightsZero(self) -> bool:
        if not self.studentManager.studentDictionary:
            return False
        return all(student.weight <= 0.0 for student in self.studentManager.studentDictionary.values())

    def showResetWeightsButton(self) -> None:
        if not self.resetWeightsButtonVisible:
            self.resetWeightsButton.pack(pady=5)
            self.resetWeightsButtonVisible = True

    def hideResetWeightsButton(self) -> None:
        if self.resetWeightsButtonVisible:
            self.resetWeightsButton.pack_forget()
            self.resetWeightsButtonVisible = False

    def onResetWeightsButtonClicked(self) -> None:
        self.studentManager.resetAllWeights(defaultWeight=0.5)

        self.instantSelectedStudentLabel.configure(text="Weights reset to 0.5.\nPress the button to pick a student.")
        self.spinnerSelectedStudentLabel.configure(text="No student selected yet.")

        self.instantPickStudentButton.configure(state="normal")
        self.spinnerPickStudentButton.configure(state="normal")

        self.initializeSpinNameList()
        self.updateSpinnerSlotLabelsFromCenterIndex()
        self.refreshStatsTab()

        self.hideResetWeightsButton()

    def buildSettingsTab(self) -> None:
        settingsContainer: ctk.CTkFrame = ctk.CTkFrame(master=self.settingsTabFrame)
        settingsContainer.pack(pady=20, padx=20, fill="both", expand=True)

        appearanceFrame: ctk.CTkFrame = ctk.CTkFrame(master=settingsContainer)
        appearanceFrame.pack(fill="x", pady=10)

        appearanceLabel: ctk.CTkLabel = ctk.CTkLabel(master=appearanceFrame, text="Appearance mode:", font=("Arial", 14))
        appearanceLabel.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.appearanceModeSegmented: ctk.CTkSegmentedButton = ctk.CTkSegmentedButton(master=appearanceFrame, values=["Light", "Dark"], command=self.onAppearanceModeChanged)
        if self.appSettings.appearanceMode.lower() == "light":
            self.appearanceModeSegmented.set("Light")
        else:
            self.appearanceModeSegmented.set("Dark")
        self.appearanceModeSegmented.grid(row=0, column=1, padx=10, pady=10)

        themeFrame: ctk.CTkFrame = ctk.CTkFrame(master=settingsContainer)
        themeFrame.pack(fill="x", pady=10)

        themeLabel: ctk.CTkLabel = ctk.CTkLabel(master=themeFrame, text="Color theme:", font=("Arial", 14))
        themeLabel.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.themeOptionMenu: ctk.CTkOptionMenu = ctk.CTkOptionMenu(master=themeFrame, values=["blue", "green", "dark-blue"], command=self.onThemeChanged)
        self.themeOptionMenu.set(self.appSettings.colorTheme)
        self.themeOptionMenu.grid(row=0, column=1, padx=10, pady=10)

        weightFrame: ctk.CTkFrame = ctk.CTkFrame(master=settingsContainer)
        weightFrame.pack(fill="x", pady=10)

        weightLabel: ctk.CTkLabel = ctk.CTkLabel(master=weightFrame, text="Weight decrease per pick:", font=("Arial", 14))
        weightLabel.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.weightDecreaseEntry: ctk.CTkEntry = ctk.CTkEntry(master=weightFrame, width=120)
        self.weightDecreaseEntry.insert(0, str(self.appSettings.weightDecreaseAmount))
        self.weightDecreaseEntry.grid(row=0, column=1, padx=10, pady=10)

        self.applyWeightDecreaseButton: ctk.CTkButton = ctk.CTkButton(master=weightFrame, text="Apply", width=80, command=self.onWeightDecreaseApplyClicked)
        self.applyWeightDecreaseButton.grid(row=0, column=2, padx=10, pady=10)

        speedFrame: ctk.CTkFrame = ctk.CTkFrame(master=settingsContainer)
        speedFrame.pack(fill="x", pady=10)

        speedLabel: ctk.CTkLabel = ctk.CTkLabel(master=speedFrame, text="Spinner speed (higher = faster):", font=("Arial", 14))
        speedLabel.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.spinnerSpeedSlider: ctk.CTkSlider = ctk.CTkSlider(master=speedFrame, from_=0, to=100, number_of_steps=100, command=self.onSpinnerSpeedChanged, width=200)
        self.spinnerSpeedSlider.set(self.appSettings.spinnerSpeedValue)
        self.spinnerSpeedSlider.grid(row=0, column=1, padx=10, pady=10)

        self.spinnerSpeedValueLabel: ctk.CTkLabel = ctk.CTkLabel(master=speedFrame, text=f"{self.appSettings.spinnerSpeedValue:.0f}", font=("Consolas", 14))
        self.spinnerSpeedValueLabel.grid(row=0, column=2, padx=10, pady=10)

        self.classFileFrame: ctk.CTkFrame = ctk.CTkFrame(master=settingsContainer, border_width=1, border_color="gray30", corner_radius=8)
        self.classFileFrame.pack(fill="x", pady=20)

        studentFileLabelTitle: ctk.CTkLabel = ctk.CTkLabel(master=self.classFileFrame, text="Student list from classes folder:", font=("Arial", 14))
        studentFileLabelTitle.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.classFileOptionMenu: ctk.CTkOptionMenu = ctk.CTkOptionMenu(master=self.classFileFrame, values=[self.classDropdownPlaceholderText], command=self.onClassFileOptionChanged, width=220)
        self.classFileOptionMenu.set(self.classDropdownPlaceholderText)
        self.classFileOptionMenu.grid(row=0, column=1, padx=10, pady=10)

        self.refreshClassFilesButton: ctk.CTkButton = ctk.CTkButton(master=self.classFileFrame, text="Refresh", width=100, command=self.refreshClassFileList)
        self.refreshClassFilesButton.grid(row=0, column=2, padx=10, pady=10)

        self.studentFileLabel: ctk.CTkLabel = ctk.CTkLabel(master=self.classFileFrame, text="No class files found yet.", font=("Consolas", 12), justify="left")
        self.studentFileLabel.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="w")

    def saveSettings(self) -> None:
        saveAppSettingsToDisk(self.appSettings)

    def updateSpinnerDelaysFromSpeed(self, sliderValue: float) -> None:
        time: float = sliderValue / 100.0
        minDelay: float = self.baseMinDelaySlowMilliseconds + (self.baseMinDelayFastMilliseconds - self.baseMinDelaySlowMilliseconds) * time
        maxDelay: float = self.baseMaxDelaySlowMilliseconds + (self.baseMaxDelayFastMilliseconds - self.baseMaxDelaySlowMilliseconds) * time
        self.minimumSpinDelayMilliseconds = int(minDelay)
        self.maximumSpinDelayMilliseconds = int(maxDelay)

    def onAppearanceModeChanged(self, value: str) -> None:
        normalizedValue: str = value.lower()
        if normalizedValue == "light":
            self.currentAppearanceMode = "light"
        else:
            self.currentAppearanceMode = "dark"

        self.appSettings.appearanceMode = self.currentAppearanceMode
        ctk.set_appearance_mode(self.currentAppearanceMode)
        self.saveSettings()

    def onThemeChanged(self, value: str) -> None:
        self.currentColorTheme = value
        self.appSettings.colorTheme = value
        ctk.set_default_color_theme(self.currentColorTheme)
        self.saveSettings()

    def onWeightDecreaseApplyClicked(self) -> None:
        try:
            value: float = float(self.weightDecreaseEntry.get())
            if value <= 0:
                raise ValueError

            self.studentManager.weightDecreaseAmount = value
            self.appSettings.weightDecreaseAmount = value
            self.saveSettings()
        except ValueError:
            messagebox.showerror("Invalid value", "Weight decrease must be a positive number.", parent=self)
            self.weightDecreaseEntry.delete(0, "end")
            self.weightDecreaseEntry.insert(0, str(self.appSettings.weightDecreaseAmount))

    def onSpinnerSpeedChanged(self, value: float) -> None:
        sliderValue: float = float(value)
        self.spinnerSpeedValueLabel.configure(text=f"{sliderValue:.0f}")
        self.appSettings.spinnerSpeedValue = sliderValue
        self.updateSpinnerDelaysFromSpeed(sliderValue)
        self.saveSettings()

    def refreshClassFileList(self) -> None:
        classesDirectoryPath: Path = getClassesDirectoryPath()
        allFiles: List[Path] = sorted(path for path in classesDirectoryPath.iterdir() if path.is_file() and path.suffix.lower() in (".json", ".csv"))

        self.classFileOptions = {filePath.name: filePath for filePath in allFiles}

        if not allFiles:
            values: List[str] = [self.classDropdownPlaceholderText, "No class files found"]
            self.classFileOptionMenu.configure(values=values)
            self.classFileOptionMenu.set(self.classDropdownPlaceholderText)
            self.studentFileLabel.configure(text=("No class files found.\n" "Add .json or .csv files to:\n" f"{classesDirectoryPath}"))

            self.currentStudentFilePath = None
            self.currentStudentFileType = None
            return

        values = [self.classDropdownPlaceholderText] + [filePath.name for filePath in allFiles]
        self.classFileOptionMenu.configure(values=values)
        self.classFileOptionMenu.set(self.classDropdownPlaceholderText)
        self.studentFileLabel.configure(text=f"Found {len(allFiles)} class file(s) in:\n{classesDirectoryPath}")

    def autoLoadSavedClassIfAvailable(self) -> None:
        if not self.appSettings.selectedClassFileName:
            return

        savedName: str = self.appSettings.selectedClassFileName
        if savedName not in self.classFileOptions:
            return

        self.classFileOptionMenu.set(savedName)
        self.onClassFileOptionChanged(savedName)

    def onClassFileOptionChanged(self, value: str) -> None:
        if value not in self.classFileOptions:
            self.updateUiForStudentAvailability()
            return

        filePath: Path = self.classFileOptions[value]
        extension: str = filePath.suffix.lower()

        try:
            if extension == ".json":
                studentList: List[Student] = self.loadStudentsFromJsonFile(filePath)
                self.currentStudentFileType = "json"
            elif extension == ".csv":
                studentList = self.loadStudentsFromCsvFile(filePath)
                self.currentStudentFileType = "csv"
            else:
                messagebox.showerror("Unsupported file type", "Please use a .json or .csv file.", parent=self)
                return
        except Exception as error:
            messagebox.showerror("Error loading students", f"Could not load students:\n{error}", parent=self)
            return

        self.studentManager.setStudentsFromList(studentList)

        self.initializeSpinNameList()
        self.updateSpinnerSlotLabelsFromCenterIndex()
        self.refreshStatsTab()

        self.instantSelectedStudentLabel.configure(text="Press the button to pick a student instantly.")
        self.spinnerSelectedStudentLabel.configure(text="No student selected yet.")

        self.currentStudentFilePath = filePath
        self.appSettings.selectedClassFileName = filePath.name
        self.saveSettings()

        self.studentFileLabel.configure(text=f"Loaded: {filePath.name}")

        self.updateUiForStudentAvailability()

    def updateUiForStudentAvailability(self) -> None:
        hasStudents: bool = bool(self.studentManager.studentDictionary)

        if not hasStudents:
            self.instantPickStudentButton.configure(state="disabled")
            self.spinnerPickStudentButton.configure(state="disabled")
            self.instantSelectedStudentLabel.configure(text="No students loaded.\nChoose a class list in Settings.")
            self.statsLabel.configure(text="No students loaded.\nChoose a class list in the Settings tab.")

            self.openSettingsForClassButton.configure(state="normal")
            self.hideResetWeightsButton()
        else:
            self.instantPickStudentButton.configure(state="normal")
            self.spinnerPickStudentButton.configure(state="normal")
            self.openSettingsForClassButton.configure(state="disabled")
            self.hideResetWeightsButton()
            self.refreshStatsTab()
            self.initializeSpinNameList()
            self.updateSpinnerSlotLabelsFromCenterIndex()

    def goToSettingsAndHighlightClassSection(self) -> None:
        self.tabView.set("Settings")
        self.highlightClassFileFrame()

    def highlightClassFileFrame(self) -> None:
        try:
            self.classFileFrame.configure(border_color="orange", border_width=3)
            self.after(1000, lambda: self.classFileFrame.configure(border_color="gray30", border_width=1))
        except Exception:
            pass

    def loadStudentsFromJsonFile(self, filePath: Path) -> List[Student]:
        with filePath.open("r", encoding="utf-8") as jsonFile:
            rawData = json.load(jsonFile)

        studentList: List[Student] = []

        if isinstance(rawData, dict):
            iterable = rawData.values()
        else:
            iterable = rawData

        for item in iterable:
            if isinstance(item, dict):
                name: str = str(item.get("name", "")).strip()
                weightValue = item.get("weight", 0.5)
                countValue = item.get("count", 0)
            else:
                name = str(item).strip()
                weightValue = 0.5
                countValue = 0

            if not name:
                continue

            try:
                weight = float(weightValue)
            except (TypeError, ValueError):
                weight = 0.5

            try:
                count = int(countValue)
            except (TypeError, ValueError):
                count = 0

            studentList.append(Student(name=name, weight=weight, count=count))

        if not studentList:
            raise ValueError("No valid students found in JSON file. Each item should have at least a 'name'.")

        return studentList

    def loadStudentsFromCsvFile(self, filePath: Path) -> List[Student]:
        studentList: List[Student] = []

        with filePath.open("r", encoding="utf-8", newline="") as csvFile:
            csvReader = csv.DictReader(csvFile)
            for row in csvReader:
                name: str = str(row.get("name", "")).strip()
                if not name:
                    continue

                weightRaw = row.get("weight", "")
                countRaw = row.get("count", "")

                try:
                    weight = float(weightRaw) if weightRaw != "" else 0.5
                except ValueError:
                    weight = 0.5

                try:
                    count = int(countRaw) if countRaw != "" else 0
                except ValueError:
                    count = 0

                studentList.append(Student(name=name, weight=weight, count=count))

        if not studentList:
            raise ValueError("No valid students found in CSV file. Make sure it has a 'name' column and optionally 'weight' and 'count' columns.")

        return studentList

    def saveStudentsToFile(self) -> None:
        if self.currentStudentFilePath is None or self.currentStudentFileType is None:
            return

        studentList: List[Student] = list(self.studentManager.studentDictionary.values())

        if self.currentStudentFileType == "json":
            data = [{"name": student.name, "weight": student.weight, "count": student.count} for student in studentList]
            with self.currentStudentFilePath.open("w", encoding="utf-8") as jsonFile:
                json.dump(data, jsonFile, indent=4)
        elif self.currentStudentFileType == "csv":
            with self.currentStudentFilePath.open("w", encoding="utf-8", newline="") as csvFile:
                fieldnames = ["name", "weight", "count"]
                writer = csv.DictWriter(csvFile, fieldnames=fieldnames)
                writer.writeheader()
                for student in studentList:
                    writer.writerow({"name": student.name, "weight": student.weight, "count": student.count})

    def onWindowClosing(self) -> None:
        if self.currentStudentFilePath is not None:
            result = messagebox.askyesnocancel("Save student stats?", "Do you want to save current weights and stats back to " f"'{self.currentStudentFilePath.name}'?", parent=self)

            if result is None:
                return
            if result is True:
                try:
                    self.saveStudentsToFile()
                except Exception as error:
                    messagebox.showerror("Error saving students", f"Could not save students:\n{error}", parent=self)
                    return

        self.saveSettings()
        self.destroy()


def mainFunction() -> None:
    studentManager: StudentManager = StudentManager()
    randomStudentPickerApplication: RandomStudentPickerApp = RandomStudentPickerApp(studentManager=studentManager)
    randomStudentPickerApplication.mainloop()


if __name__ == "__main__":
    mainFunction()
