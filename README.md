# NL2PDDL : Large Language Models as Planning Domain Generators

Code and data for the paper [*Large Language Models as Planning Domain Generators*](https://openreview.net/forum?id=C88wQIv0aJ)
accepted for publication at [ICAPS 2024](https://icaps24.icaps-conference.org/).

## Installation and Setup

For automatic setup use the `setup.sh` script. This will
init submodules, create a virtual environment, and install
all python dependencies and build other dependencies (VAL). 

Alternatively you can use the manual setup instructions. 

<details>

<summary> Manual Setup Instructions </summary>

### Clone the repo
Clone the repository with submodules
```bash
git clone --recurse-submodules <Link to this repo>
```
If you have already cloned without submodules,
you can get the submodules with
```bash
git submodule update --init --recursive
```

### Create a virtual python environment (Recommended)
We suggest creating a virtual python environment for the project. 
This will help ensure that the large list of pip dependencies required 
for this project do not conflict with alternate versions on your system.

Here is an example using python's built in `venv` module, but you could
also use `anaconda` or `pipenv`. 
```bash
# Create the virtual environment 
python -m venv .venv
# Activate the virtual environment
source .venv/bin/activate
```
Once the virtual environment is activated you are free to install 
pip dependencies. 

### Install Required Python Packages
Note that all code in this repository has only
been tested on Python 3.11.4
```bash
pip install -r requirements.txt 
```

### Build VAL into /VAL/build/bin
The VAL submodule must be built into `/VAL/build/bin`. To build VAL we need
CMake and Make. You can run the following commands to build it.
```
cd VAL
mkdir build
cd build
cmake ..
make
```

</details>

### Setup Credentials for Model Inference (Required For New Generation)

We use IBM Generative AI Python SDK. 
Create a `.env` file in the top level repo with the following
credentials.
```
GENAI_KEY=<your GENAI key>
GENAI_API=<your API endpoint>
```
*Note: Models supported by known ibm-genai endpoints change frequently, you may need to change models evaluated against or host a custom endpoint.*

## Running Experiments

Use `driver.py` to run the experiments on the raw LLM outputs
located in `data/outputs`. It will generate a `.json` file with new output
at each stage of the pipeline, and end by generating the figures and tables
used by the paper in `figures_and_tables`.

Make sure to activate your virtual environment first if necessary!
```bash
source .venv/bin/activate
python driver.py
```