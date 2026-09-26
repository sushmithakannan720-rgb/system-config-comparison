# VIVA QUESTIONS & ANSWERS

Short, simple, correct answers — written so you can explain the project
naturally in a viva. (Answers are written in first person; adjust the wording
to your own.)

## About the project

**1. What is your project?**
It is a Python desktop application with a CustomTkinter GUI. It scans a
computer's configuration (OS, CPU, RAM, storage, network), saves it as a JSON
file, and compares two configurations, showing every difference in a
color-coded table with plain-English explanations.

**2. Why did you select this project?**
LPU EDU-Revolution lists "System Configuration Comparison Tool" as a project
example. It is the right size for a first-year project: real system
programming (psutil, platform), a visible GUI, file handling (JSON), and clear
logic I can fully explain.

**3. What problem does it solve?**
Manually checking what two computers have in common (RAM, CPU, storage, OS)
is slow and error-prone. This tool collects everything automatically and
highlights exactly what differs, in seconds.

**4. What is "system configuration"?**
The hardware and software setup of a computer: operating system and version,
CPU model, number of cores, installed RAM, disk capacity, hostname, network
address, etc.

**5. Why did you choose Python?**
It is readable, it has excellent system libraries (psutil, platform), and
tkinter/CustomTkinter let me build a desktop GUI without any web technology.
One language covers the whole project.

**6. What is a GUI?**
A Graphical User Interface — the user interacts with windows, buttons and
tables instead of typing commands in a terminal. My GUI has a sidebar with
Dashboard, System Details, Compare and About pages.

**7. What is CustomTkinter / Tkinter?**
Tkinter is Python's standard GUI library. CustomTkinter is a library built on
top of it that looks modern (rounded cards, themes) and gives built-in
light/dark mode. I used CustomTkinter for the main window and cards.

**8. What is psutil?**
A cross-platform Python library for system metrics. I use it for CPU count and
usage, virtual memory (total/used/available RAM) and disk usage.

**9. What is the platform module?**
A standard-library module that gives OS details without any extra install:
system name, release, version, architecture and machine type. It also gives
the Python version.

**10. How do you retrieve CPU information?**
Logical and physical core counts come from `psutil.cpu_count()`. The model
name is platform-specific: on Windows I run a small PowerShell command
(`Get-CimInstance Win32_Processor`), on Linux I read `/proc/cpuinfo`, on
macOS I use `sysctl`. If it cannot be read, I show "Not available".

**11. How do you retrieve RAM information?**
`psutil.virtual_memory()` returns total, used, available and percentage in one
call — no OS-specific code needed.

**12. How do you retrieve storage information?**
`psutil.disk_usage()` on the system drive (C:\ on Windows, / elsewhere)
returns total, used, free and percentage.

**13. How does the comparison algorithm work?**
I keep a fixed list of parameters (OS, version, architecture, hostname,
processor, cores, logical processors, RAM, storage total/free, IP). For each
parameter I read the value from config A and config B: equal → SAME,
different → DIFFERENT with a factual note, absent on either side → MISSING.
For numbers and byte values I compute the delta, e.g. "System B has 8 GB more
RAM". It is a straightforward parameter-by-parameter loop — easy to extend.

**14. Why did you use JSON for saving configurations?**
It is human readable (opens in Notepad), native to Python (json module),
platform independent, and small. A JSON file can be copied to any machine and
reopened in the app.

**15. What is JSON?**
JavaScript Object Notation — a text format for structured data using
objects/arrays and key–value pairs. My file maps sections ("system", "cpu",
"memory"…) to key–value settings.

**16. What is Git?**
A version-control system: it records every change to the project so I can go
back to older versions, see what changed, and work safely. I commit after each
working stage.

**17. What is GitHub?**
A hosting site for Git repositories. I use it to store the project code
online, keep a backup, and share a link with the faculty.

**18. What is the "frontend" in this project?**
`app/gui.py` — everything the user sees: the sidebar, the four pages, cards,
tables, buttons, colors, dark/light mode. It only displays; it does no
calculation itself.

**19. What is the "backend" / logic in this project?**
`app/system_info.py` (data collection), `app/comparison.py` (comparison,
difference notes, summary) and `app/report.py` (HTML report). No server is
involved — it is all local, which is why the layers are still separated so
each can be tested independently.

**20. How is error handling implemented?**
Every hardware read is wrapped in try/except and falls back to `None`, shown
as "Not available". File loading validates the JSON and raises a clear
ValueError, which the GUI shows in a message box. The GUI itself also wraps
scan/report actions, so no exception can ever crash the window.

**21. How are configurations saved?**
The collected dict is written with `json.dump` (indent=4, UTF-8) to a .json
file chosen by the user. Raw numbers (bytes, cores) are stored as numbers so
comparisons stay exact.

**22. How are configurations loaded?**
`storage.load_config` opens the chosen file, parses the JSON, and checks that
it contains at least one known section. Invalid files produce a friendly
error dialog instead of a crash.

**23. How is the difference calculated?**
For text fields it is a string equality check. For numeric/byte fields I
convert to numbers and subtract: `abs(B − A)`, then format it ("8 GB",
"2 cores") and pick "more" or "less" based on the sign. So the sentences are
computed, not hardcoded.

**24. What happens if some information is unavailable?**
The field is stored as None, displayed as "Not available", and in a
comparison the row is marked MISSING with a note like "Value not available on
System B". Nothing crashes.

**25. What testing did you perform?**
Unit tests for all 7 comparison cases (identical, different RAM/storage/CPU/OS,
missing value, empty config), core tests (scan sections, save/load round-trip,
invalid file rejection, report content), and a GUI smoke test that opens the
real app, clicks through every page, scans, saves, loads, compares and
generates a report — all automated, all passing.

**26. What are the limitations?**
It compares one system drive and total RAM (no per-stick/per-drive detail),
usage percentages are point-in-time and excluded from "configuration"
differences, CPU name may be unavailable on unusual systems, and reports are
HTML (print to PDF via the browser).

**27. What is the future scope?**
Remote comparison over a network, discovering machines on the LAN, more
hardware (GPU, battery, software), compatibility checking, benchmarks,
history tracking, multi-system comparison, a database backend, and a web
version.

**28. What was your contribution?**
I designed the module structure, wrote all the code — the scanner, the
comparison engine, the GUI, the report generator and the tests — and
documented the project in the README.

**29. Explain the architecture.**
Three layers. Data layer: `system_info.py` collects the configuration and
`storage.py` saves/loads JSON. Logic layer: `comparison.py` compares and
`report.py` builds the HTML. Presentation layer: `gui.py` shows the four
pages. Data flows up (scan → compare → display) and never crosses layers the
wrong way; `utils.py` holds shared helpers like bytes→GB formatting.

**30. Demonstrate the project.**
*(Demo script: start the app → "Scan Current System" → "View System Details"
→ Compare page: "Last scan" for A, "Load System B" with
data/sample/system_b.json → "Compare Systems" → point at the table, the
"System B has 8 GB more RAM" sentence, the ✓/✗ summary and the bar charts →
"Generate Report" and open the HTML.)*

## Extra questions faculty often ask

**31. Does the project need the internet?**
No. After `pip install`, it runs fully offline. Reading the local IP only
inspects addresses already assigned to this machine; no packets are sent.

**32. Does it collect or upload personal data?**
No. It reads hardware/OS info of the machine it runs on, saves files locally,
and makes no network calls at all. This is stated in the About page and the
README.

**33. Is this an official Smart India Hackathon project?**
No. I developed it as my academic LPU EDU-Revolution project using the entry
LPU lists as an example on its portal. I have no SIH participation or any
official association with SIH or any government body — the README states this
clearly.

**34. Why CustomTkinter instead of plain Tkinter?**
Plain Tkinter works, but CustomTkinter (built on Tkinter) gives a modern look
and light/dark mode with almost no extra code — better for a demo, while the
underlying widget concepts are still standard Tkinter.

**35. Why HTML for the report instead of PDF?**
PDF needs an extra library (reportlab/fpdf). HTML needs none, opens in any
browser, and any browser can print it to PDF with one click. Simpler is
better at this stage.

**36. What happens if both systems are identical?**
Every row is SAME, the difference list says "No differences detected", the
summary is all ✓, and total differences is 0 — covered by a unit test.

**37. How would you extend it to compare more than two systems?**
`compare_configs` stays pairwise; I would load N configurations, compare each
against a chosen reference, and add one column per system to the table and
report. The data model already supports any number of files.

**38. What does TRL 3 mean, and why is this project TRL 3?**
Technology Readiness Level 3 is "experimental proof of concept in a relevant
environment". This is exactly what I built: a working prototype proven on
real machines, not yet a polished commercial product.

**39. Which parts could go wrong on a different computer?**
Reading the CPU model name (tool may not exist) and the local IP (some
networks assign no IPv4). Both fall back to "Not available" — tested behavior.

**40. What would you improve first?**
Per-drive storage and per-memory-stick detail, plus a "better/worse" view
based only on the measurable deltas we already compute.

**41. What does "production level" mean in this project, and what did you add?**
It means the app behaves like a real released tool, not just a demo: the scan
runs on a background thread so the UI never freezes; every action is logged to
logs/app.log; an uncaught-exception hook logs the traceback and shows a dialog
instead of crashing; missing dependencies give a clear install message; and
the project is properly packaged (pyproject.toml, LICENSE, CHANGELOG,
one-click start.bat / run.sh launchers).

**42. Why do you run the scan in a background thread?**
Scanning takes 1–2 seconds (CPU usage is measured over 0.5 s and the CPU name
is queried from the OS). A Tkinter window only repaints when its main loop
runs, so doing it on the main thread would freeze the whole window. In a
worker thread the UI stays responsive. The worker never touches Tk directly
(tkinter is not thread-safe) — it puts the result into a `queue.Queue`, and
the UI thread polls that queue every 100 ms with `after()` and updates the
widgets there. Calling Tk from the worker thread, or from a thread that is
not the main one, can raise "main thread is not in main loop", which is why
the queue handoff is the safe pattern.

**43. Where does the app log, and why is that useful?**
To the console and to logs/app.log, with timestamps — scan start/finish,
file saves and loads, comparison results, report paths and any errors. In a
viva or a real deployment it proves what happened, and if a user reports a
problem the log file shows the exact failing step.
