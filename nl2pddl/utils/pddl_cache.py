"""
Parsing PDDL Domains and problems is expensive and time consuming, to help
speed up the process we cache all domains and problems 
in their object form and pickle them.

This file creates PDDL ASTs for all domains and problems
in the pddl-domains folder and reads and catches them as a
.pkl file. It is far faster to load the pickled domain ASTs
than to reparse the domains each time they are needed. 
"""

import os
import pickle
from pathlib import Path
from typing import Generator

from pddl.parser.domain import DomainParser
from pddl.parser.problem import ProblemParser
from pddl.core import Domain, Problem

PDDL_CACHE_PATH = "pddl_cache.pkl"
PROBLEM_DIR = "data/pddlData/pddl-problems"
PRED_NL_DIR = "data/pddlData/predicate-descriptions"

#List of domain names
domainNames : list[str] = []
#Map of domain names to domain objects
domainObjMap : dict[str, Domain] = {}
#Map of domain names to domain file paths
domainPathMap : dict[str, str] = {}
#Map of domain names to domain predicate NL descriptions
domainPredMap : dict[str, str] = {}
#Map of domain names to list of problem objects for that domain
domainProblemMap : dict[str, list[Problem]] = {}
#Map of domain names to list of problem file paths
domainProblemPathMap : dict[str, list[str]] = {}


def all_files(root : str) -> Generator[str, None, None]:
    """ Generator for the paths of all files in root and all its subdirs"""
    for base_path, _, file_names in os.walk(root):
        for file_name in file_names:
            yield os.path.join(base_path, file_name)

def extract_domains_and_problems(file_contents : dict[str, str]) \
-> tuple[dict[str, tuple[str, Domain]], dict[str, tuple[str,Problem]]]:
    """
    Given a map of file names to file contents this function will parse
    the contents and return a tuple of two dictionaries, the first
    containing domain names mapped to their file paths and domain objects,
    and the second containing problem names mapped to their file paths
    and problem objects.
    """
    problem_parser = ProblemParser()
    domain_parser = DomainParser()
    domains : dict[str, tuple[str, Domain]] = {}
    problems : dict[str, tuple[str,Problem]] = {}
    for file_path, file_content in file_contents.items():
        if "(define (domain" in file_content:
            domain : Domain = domain_parser(file_content)
            domains[domain.name] = (file_path, domain)
        elif "(define (problem" in file_content:
            problem : Problem = problem_parser(file_content)
            problems[problem.name] = (file_path, problem)
        else:
            raise f"Could not identify {file_path} as valid pddl"
    return domains, problems


def associate_problems_with_domains(domains, problems) \
-> dict[str, list[tuple[str, Problem]]]:
    """
    Given a dictionary of domains and problems, this function will
    associate each problem with its domain and return a dictionary
    mapping domain names to a list of tuples containing the path
    and object of each problem in that domain.
    """
    domain_problems : dict[str, list[tuple[str, Problem]]] = {}
    for _, (p_path, p_obj) in problems.items():
        for domain_name, _ in domains.items():
            if p_obj.domain_name in domain_name:
                domain_problems.setdefault(p_obj.domain_name, [])\
                               .append((p_path, p_obj))
            # else:
            #     print(f"Could not find domain {p_obj.domain_name} for {p_path}")
            #     raise RuntimeError()
    return domain_problems

def generate_pddl_cache(filename : str = PDDL_CACHE_PATH) -> None:
    """
    Given a filename, this function will parse all the PDDL files in 
    the PROBLEM_DIR and PRED_NL_DIR directories and save the parsed
    objects in a pickle file with the given filename.
    """
    #Extract all the file contents
    file_contents : dict[str, str] = {}
    for full_path in all_files(PROBLEM_DIR):
        with open(full_path, "r", encoding="utf-8") as file:
            file_contents[full_path] = file.read()

    #Map domain names to domain paths and objects &
    #problem names to problem paths and objects
    domains, problems = extract_domains_and_problems(file_contents)

    #Associate each problem with its domain
    domain_problems = associate_problems_with_domains(domains, problems)

    #Associate each domain with its predicate NL description
    #Assumes all domains have associated predicate descriptions
    #in the PRED_NL_DIR. will raise if false.
    domain_pred_nl : dict[str, str] = {}
    for domain_name, (domain_path, _) in domains.items():
        domain_stem : str = Path(domain_path).stem
        d_pred_nl_path = Path(PRED_NL_DIR, domain_stem + ".txt")
        if Path.exists(d_pred_nl_path):
            with open(d_pred_nl_path, "r", encoding="utf-8") as pred_nl_file:
                domain_pred_nl[domain_name] = pred_nl_file.read()
        else:
            raise f"{d_pred_nl_path} was not found but is required to exist"
    with open(filename, "wb") as domain_cache:
        pickle.dump((domains, domain_pred_nl, domain_problems), domain_cache)

if __name__ == "__main__":
    generate_pddl_cache()
else:
    if not os.path.exists(PDDL_CACHE_PATH):
        print(f"Could not find {PDDL_CACHE_PATH}, generating now...")
        generate_pddl_cache()
        print("Done, cache generated.")
    domainObjMap = {}
    domainPathMap = {}
    domainPredMap = {}
    domainProblemMap = {}
    domainProblemPathMap = {}
    with open(PDDL_CACHE_PATH, "rb") as domain_data:
        _domain_map, domainPredMap, _problem_map = pickle.load(domain_data)
    for d_name, (d_path, d_obj) in _domain_map.items():
        domainPathMap[d_name] = d_path
        domainObjMap[d_name] = d_obj
    for d_name, p_list in _problem_map.items():
        #unzip list of tuples into problem objects and path lists
        domainProblemPathMap[d_name], domainProblemMap[d_name] = zip(*p_list)
    domainNames = domainObjMap.keys()
