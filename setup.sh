
#!/bin/bash

cmd_exists () {
    if [ ! type $1 > /dev/null ]; then
        printf "Did not find required command $1 on path,"\
               "please install $1 and ensure it is on PATH. \n"
        exit 127
    fi
}

if [ ! -f "setup.sh" ]; then
    print "setup.sh needs to be run from the NL2PDDL project root directory."\
          "please ensure you are in the NL2PDDL root director and "\
          "try to run again. \n"
    exit 1
fi 


#If you forgot to --recuse-submodules on clone, clone VAL it now
if [ ! -f "VAL/README.md" ]; then
    printf "Did not find VAL, initilizing submodule \n"
    git submodule update --init --recursive
fi

#If VAL has yet to be built, build VAL
if [ ! -f "VAL/build/bin/Validate" ]; then 
    cmd_exists cmake
    cmd_exists make
    printf "VAL not yet built, Building VAL \n"
    mkdir VAL/build
    cd VAL/build
    cmake ..
    make
    cd ../..
fi

#Setup a virtual enviorment for experiments
if [ ! -d ".venv" ]; then
    #Check if using python3 or python as python3 command and store
    #in a variable. if neither are on the system fail with error code 127.
    if type python3 > /dev/null; then 
        python3 -m venv .venv
    elif type python > /dev/null; then 
        python -m venv .venv
    else
        printf "Did not find python3 or python on path, \
                please install python 3 and ensure it is on PATH. \n"
        exit 127
    fi
    
    source .venv/bin/activate
    if [ ! -f ".venv/bin/pip" ]; then
        printf "Did not find pip in virtual enviorment, please ensure virtual enviorment is setup correctly. \n"
        exit 1
    fi 

    if ! pip install -r requirements.txt; then
        printf "Failed to install required packages, please ensure pip is working correctly.\n"
        exit 1
    fi
fi 

if [ ! -f ".env" ]; then
    printf "Did not find .env file creating one. \n"
    echo "GENAI_KEY=" > .env
    echo "GENAI_API=" >> .env
fi

printf "Setup completed successfully. Please note that to rerun the LLM PDDL generation you will need to enter your API keys for BAM in a .env file. You do not need this to run the experiments, as by default this will use the pregenerated PDDL files in the data directory. \n"
