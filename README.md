# Experiments to evaluate PADRAIG

PADRAIG (Precise AnDRoid Automated Input Generation) is a model-based framework that generates test suites for Android applications consisting of a sequence of user inputs. This repository contains the code and results that evaluate and compare PADRAIG with the state of the art in automated test input generation.  

Please note that this repository will be maintained but not regularly.

### Installation

Simply download the artefact [here](https://github.com/jordan2doyle1/QRS-2024-Padraig/archive/cbb772ec017f44db8add539e5621cb7cc151a9ad.zip) and apply the following environment configuration.

#### Environment Configration

For simplisity, it is highly recommended that you use the Docker image provided. The code was last used with Docker Desktop v4. For native installs please refer to the dependencies listed in the provided Docker files.

### Usage

The experiments are split into tasks, and each task is performed independenlty. Specific tasks may require output files from another task. Below is the basic format for running a task:

    ./execute_task -o <output-directory> -f <count> <task-option>

where output-directory is the path to a directory where task outputs will be stored, count is the number of iterations of the task to perform and task-option specifies which task to execute.

#### Output

Each input APK is given its own output sub-directory (APK file name) and each task outputs to the following sub-directories with the following content:

    /androguard - Androguard output GML file.
    /instrument - Instrumented APK file.
    /traversal - DroidGraph dynamic analsis traversal log.
    /model - DroidGraph model in JSON format.
    /padraig - ACVTool coverage report for PADRAIG tests. 
    /monkey - ACVTool coverage report for Monkey (all input types) tests.
    /monkey-click - ACVTool coverage report for Monkey (click input only) tests.
    /s-smog - ACVTool coverage report for STGFA-SMOG tests.
    /stoat - ACVTool coverage report for Stoat tests.

Results for tasks with multiple iterations are split int sub-directories for each test. Results are archived in the TAR format and compressed using BZIP2, in order to reduce the overall size of the project. 

### Contact
<jordan.doyle@ucdconnect.ie>
