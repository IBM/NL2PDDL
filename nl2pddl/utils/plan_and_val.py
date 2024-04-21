"""
This file contains a subprocess based interface for calling 
the K* planner and VAL plan validator. It is important to note
that as val is not a python package, it is expected to be at 
VAL_PATH, which is set to where it is expected to be 
built in a git submodule during setup.
"""

#Standard Libs
import os
import sys
import json
import shutil
import tempfile
import subprocess
from typing import Any
from subprocess import CalledProcessError

#The location of VAL relative to where this is being run from
VAL_PATH = "VAL/build/bin/Validate"

def new_pipe(tmpdir : str, pipe_name : str, contents : str) -> str:
    """
    Creates a new pipe in the tempdir at tmpdir with filename,
    writes contents to the pipe, and returns a path to it.
    """
    pipe_path = os.path.join(tmpdir, pipe_name)
    with open(pipe_path, "w", encoding="utf-8") as pipe:
        pipe.write(contents)
    return pipe_path

def plan_file(domain_path : str, problem_path : str, k : int = 100) \
-> tuple[dict[str, Any], str, str, str]:
    """
    Given a domain path and a problem invoke K* and produce k optimal plans as
    a json plans object.
    """
    tmpdir = tempfile.mkdtemp()
    plan_pipe_path = os.path.join(tmpdir, 'plan.json')
    args = [
        sys.executable,
        "-m", "kstar_planner.driver.main",
        "--search-time-limit", "30s",
        domain_path, problem_path,
        "--search", f"kstar(lmcut(),k={k},"
        + f"dump_plan_files=false,json_file_to_dump={plan_pipe_path})"
    ]
    plan_obj = None
    errs = "", "", ""
    try:
        _ = subprocess.check_output(args, stderr=subprocess.DEVNULL)
        with open(plan_pipe_path, 'r', encoding="utf-8") as json_plan_pipe:
            plan_obj = json.load(json_plan_pipe)
    except CalledProcessError as err:
        #These error codes from KStar seem to line up with the error codes
        #that FD uses, see: https://www.fast-downward.org/ExitCodes
        return_code = err.returncode
        if return_code == 12:
            errs = "DifDomain", "NoPlan", err.output.decode()
        elif return_code == 23:
            #We get this if the planner runs out of time while searching
            #This is extraordinarily rare for the data we look at,
            #we give search 30s and only 1 out of all 13000 the new domains
            #we look at causes it.
            errs = "DifDomain", "NoPlan", err.output.decode()
        elif return_code == 30:
            #Translation error into SAS+, happens when the PDDL is not well formed
            errs = "SemanticError", "BadPDDL", err.output.decode()
        elif return_code == 34:
            #We get this if it tries to put a negated precondition in the STRIPS
            errs = "SemanticError", "NegPrecond", err.output.decode()
        else:
            print("Unexpected Error occurred " + err.output.decode())
            errs = "PlanError", "", f"Error code {return_code}" + err.output.decode()
    shutil.rmtree(tmpdir)
    return plan_obj, *errs

def plan_str(domain_str : str, problem_path : str, k : int = 100) \
-> tuple[dict[str, Any], str, str, str]:
    """
    Given a domain string and a problem path, invoke K* and produce a json
    plans object. This is useful since generated domains come to us as
    strings without their own files.
    """
    tmpdir = tempfile.mkdtemp()
    domain_pipe_path = os.path.join(tmpdir, 'domain.pddl')
    with open(domain_pipe_path, "w", encoding="utf-8") as domain_pipe:
        domain_pipe.write(domain_str)
    return plan_file(domain_pipe_path, problem_path, k)

def plan_to_string(plan_obj : dict[str, Any]) -> str:
    """
    Return a VAL parsable plan from json object output by K*
    """
    plan_actions = plan_obj["actions"]
    result_plan_string : str = ""
    for action_str in plan_actions:
        result_plan_string += "(" + action_str + ")\n"
    return result_plan_string

def validate(domain_path : str, problem_path : str, plan : str) \
-> tuple[bool, str]:
    """
    Validate a plan on a domain and problem, returns a tuple of
    a boolean indicating if the plan is valid and a string
    containing an error message if the plan is invalid.
    """
    tmpdir = tempfile.mkdtemp()
    new_plan_path = new_pipe(tmpdir, 'new_plan.pddl', plan)
    try:
        #Forward direction, try plan from the new domain in the original domain
        args = [VAL_PATH, domain_path, problem_path, new_plan_path]
        _ = subprocess.check_output(args, stderr=subprocess.DEVNULL)
        shutil.rmtree(tmpdir)
        return True, ""
    except CalledProcessError as err:
        shutil.rmtree(tmpdir)
        return False, err.output.decode()


def can_apply_plan(
    original_domain_path : str, new_domain : str,
    problem_path : str,
    original_plan : str, new_plan : str,
) -> tuple[bool, str, str, str]:
    """
    Given an original domain (path) and a new domain (string) problem,
    check if the the plan from the original can be used in
    the new domain and vice versa.
    """
    tmpdir = tempfile.mkdtemp()
    new_domain_path = new_pipe(tmpdir, 'new_domain.pddl', new_domain)
    new_plan_path = new_pipe(tmpdir, 'new_plan.pddl', new_plan)
    original_plan_path = new_pipe(tmpdir, 'original_plan.pddl', original_plan)
    try:
        #Forward direction, try plan from the new domain in the original domain
        args = [VAL_PATH, original_domain_path, problem_path, new_plan_path]
        _ = subprocess.check_output(args, stderr=subprocess.DEVNULL)
    except CalledProcessError as err:
        shutil.rmtree(tmpdir)
        return False, "DifDomain", "NewToOriginal", err.output.decode()
    try:
        #Backward direction, try plan from the original domain in the new domain
        args = [VAL_PATH, new_domain_path, problem_path, original_plan_path]
        _ = subprocess.check_output(args, stderr=subprocess.DEVNULL)
    except CalledProcessError as err:
        shutil.rmtree(tmpdir)
        return False, "DifDomain", "OriginalToNew", err.output.decode()
    shutil.rmtree(tmpdir)
    if os.path.exists("found_plans"):
        shutil.rmtree("found_plans")
    return True, "EqDomain", "", ""
