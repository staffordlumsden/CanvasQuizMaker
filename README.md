# Canvas Quiz Maker
### Create quizzes in QTI format from plain text with `text2qti` from [gpoore](https://github.com/gpoore/text2qti) 
This tool runs a webUI that will help you create a quiz and convert it into QTi format, ready for uploading to Canvas.

## Quick Start (Non-Technical)
Use this if you just want the app running with the least setup steps.

1. Download this project folder to your computer.
2. Open `Terminal` on macOS or `PowerShell` on Windows.
3. Change into the project folder.

macOS:
1. Run:
```bash
./install_from_github_mac.command
```
2. Wait for setup to finish.
3. Double-click `Canvas Quiz Builder.command` on your Desktop.
4. Your browser should open the app. If it does not, open:
`http://localhost:8001`

Windows:
1. Run:
```powershell
.\install_from_github_windows.ps1
```
2. Wait for setup to finish.
3. Double-click `Canvas Quiz Builder` on your Desktop.
4. Your browser should open the app. If it does not, open:
`http://localhost:8001`

### Manual Run (If Needed)
```bash
./run_text2qti_web.sh
```
Then open `http://localhost:8001`

---

## Text2QTI

Originally by [gpoore](https://github.com/gpoore/text2qti), Text2qti converts [Markdown](https://daringfireball.net/projects/markdown/)-based plain text files into quizzes in QTI format (version 1.2), which can be imported by [Canvas](https://www.instructure.com/canvas/) and other educational software. It supports multiple-choice, true/false, multiple-answers, numerical, short-answer (fill-in-the-blank), essay, and file-upload questions.  
Text2QTI also includes basic support for LaTeX math within Markdown, and allows a limited subset of [siunitx](https://ctan.org/pkg/siunitx) notation for units and for numbers in scientific notation.

## Local Web App (This Repo)

This repo includes a local web app that converts quizzes to Canvas QTI `.zip`
files. It supports `.txt` input in the Text2QTI format and a guided quiz
builder for creating new quizzes.

## Local tools (Text2QTi)

This repository includes local CLI and web helpers for converting pasted quiz
text into Canvas QTI `.zip` files.

- Web UI: `./run_text2qti_web.sh` then open `http://localhost:8001`
- CLI: `./run_text2qti_cli.sh`
- Validator: `./run_text2qti_validate.sh /path/to/quiz.txt`
- Setup: `./setup_text2qti.sh` (creates `.venv`, installs deps)
- macOS installer: `./install_from_github_mac.command`
- Windows installer: `.\install_from_github_windows.ps1`

The web UI includes a guided quiz builder for creating Text2QTI content
directly, plus strict validate and convert actions.

### What It Does
* Accepts `.txt` input in a browser UI.
* For `.txt`: runs `text2qti` directly after optional validation.
* Includes a guided quiz builder for composing questions, answers, and
  feedback directly into valid Text2QTI format.
* Includes a `Validate Format` action that checks Text2QTI syntax before
  conversion and reports line-specific errors.
* Saves the resulting `.zip` to your Desktop.

### Requirements
* Python with a virtual environment already created in `.venv`.
* `text2qti` installed in `.venv`.

### Install Dependencies
If you already installed them, you can skip this.
```
.venv/bin/python -m pip install .
```

### One-Step Installers (GitHub Clone + Desktop Shortcut)
macOS:
```
./install_from_github_mac.command
```
Windows PowerShell:
```powershell
.\install_from_github_windows.ps1
```
Both scripts clone or update the repo, install dependencies, and create a
Desktop launcher for the web app.
To install from a different GitHub repo URL, pass it as the first argument.
Example:
```bash
./install_from_github_mac.command https://github.com/<your-org>/<your-repo>.git
```

### Validating Text2QTI Before Conversion
Run:
```
./run_text2qti_validate.sh /path/to/quiz.txt
```
This performs a strict Text2QTI parse and in-memory QTI build, then reports
`VALID` or `INVALID` with details.

### Files Added
* `text2qti_web.py` – local web server and conversion pipeline
* `run_text2qti_web.sh` – launcher for the web server
* `text2qti_cli.py` – local CLI file picker conversion
* `run_text2qti_cli.sh` – launcher for the CLI tool
* `text2qti_validate.py` – strict Text2QTI format validator
* `run_text2qti_validate.sh` – launcher for the validator
* `install_from_github_mac.command` – macOS bootstrap installer + Desktop shortcut
* `install_from_github_windows.ps1` – Windows bootstrap installer + Desktop shortcut

### Notes
* The web server is local-only (`127.0.0.1`).
* The UI is plain HTML rendered by the server; no external assets required.

---

## Full Installation

Install **Python 3.8+** if it is not already available on your machine.  See
https://www.python.org/, or use the package manager or app store for your
operating system.  Depending on your use case, you may want to consider a
Python distribution like [Anaconda](https://www.anaconda.com/distribution/)
instead.

Install
[setuptools](https://packaging.python.org/tutorials/installing-packages/)
for Python if it is not already installed.  This can be accomplished by
running
```
python -m pip install setuptools
```
on the command line.  Depending on your system, you may need to use `python3`
instead of `python`.  This will often be the case for Linux and OS X.

Install text2qti by running this on the command line:
```
python -m pip install text2qti
```
Depending on your system, you may need to use `python3` instead of `python`.
This will often be the case for Linux and OS X.


### Upgrading

```
python -m pip install text2qti --upgrade
```
Depending on your system, you may need to use `python3` instead of `python`.
This will often be the case for Linux and OS X.

--- 

For examples, installing a development version of Text2QTi and formatting fot TXT files see 
`text2qti` from [GitHub](https://github.com/gpoore/text2qti)****

--- 
# Other Notes: 

## Usage

text2qti has been designed to create QTI files for use with
[Canvas](https://www.instructure.com/canvas/).  Some features may not be
supported by other educational software.  You should **always preview**
quizzes or assessments after converting them to QTI and importing them.

Write your quiz or assessment in a plain text file.  You can use a basic
editor like Notepad or gedit, or a code editor like
[VS Code](https://code.visualstudio.com/).  You can even use Microsoft Word,
as long as you save your file as plain text (*.txt).

text2qti includes a graphical application and a command-line application separate from the one in this repo. [More >](https://github.com/gpoore/text2qti)

## Instructions for using the QTI file with Canvas:
  * Go to the course in which you want to use the quiz.
  * Go to Settings, click on "Import Course Content", select "QTI .zip file",
    choose your file, and click "Import".  Typically you should not need to
    select a question bank; that should be managed automatically.
  * While the quiz upload will often be very fast, there is an additional
    processing step that can take up to several minutes.  The status will
    probably appear under "Current Jobs" after upload.
  * Once the quiz import is marked as "Completed", the imported quiz should be
    available under Quizzes.  If the imported quiz does not appear after
    several minutes, there may be an error in your quiz file or a bug in
    `text2qti`.  When Canvas encounters an invalid quiz file, it tends to fail
    silently; instead of reporting an error in the quiz file, it just never
    creates a quiz based on the invalid file.
  * You should **always preview the quiz before use**.  text2qti can detect a
    number of potential issues, but not everything.

Typically, you should start your quizzes with a title, like this:
```
Quiz title: Title here
```
Otherwise, all quizzes will have the default title "Quiz", so it will be
difficult to tell them apart.  Another option is to rename quizzes after
importing them.  Note that unlike most other text, the title is treated as
plain text, not Markdown, due to the QTI format.

### Additional quiz options

There are additional quiz options that can be set immediately after the quiz
title and quiz description.  These all take values `true` or `false`.  For
example, `shuffle answers: true` could be on the line right after the quiz
description.

* `shuffle answers` — Shuffle answer order for questions.
* `show correct answers` — Show correct answers after submission.
* `one question at a time` — Only show one question at a time.
* `can't go back` — Don't allow going back to the previous question when in
  `one question at a time` mode.

---
