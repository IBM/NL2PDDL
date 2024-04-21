"""
This file includes utilities for caching plans to prevent 
the need to replan. If run standalone it will generate a plan
cache file for every problem contained in the problem cache. 

Can import load_original_plan_map to extract the cache
"""

#Standard Libs
import pickle
from typing import Any

#Internal Libs
from .pddl_cache import domainProblemPathMap, domainPathMap
from .plan_and_val import plan_file, validate, plan_to_string

PLAN_CACHE_PATH = "plan_cache.pkl"

def load_original_plan_map() -> dict[str, list[dict[str, Any]]]:
    """
    Loads the plan cache, a map from domain names to lists of
    json object plan outputs from kstar for each plan in that domain
    """
    with open(PLAN_CACHE_PATH, "rb") as cache:
        plan_map = pickle.load(cache)
        return plan_map

def generate_plan_cache(k : int = 100, cache_path : str = PLAN_CACHE_PATH):
    """
    Given a k and a cache path, this function will generate the top k plans and
    cache them in a file at cache_path for all the problems in the pddl
    problem cache. 
    """
    plan_map : dict[str, list[dict[str, Any]]]  = {}
    for domain_name, problem_paths in domainProblemPathMap.items():
        domain_path = domainPathMap[domain_name]
        plan_map[domain_name] = []
        for problem_path in problem_paths:
            print(domain_name, problem_path.split("/")[-1])
            plans, err_class, _, err_msg = plan_file(domain_path, problem_path, k)
            if err_class != "":
                print(f"Error: {err_class}, {err_msg}")
                raise RuntimeError()
            #Validate all plans
            for plan in plans["plans"]:
                plan_str = plan_to_string(plan)
                valid, err = validate(domain_path, problem_path, plan_str)
                if not valid:
                    raise f"plan produced by K* not valid: {err}"
            plan_map[domain_name].append(plans)
    with open(cache_path, "wb") as cache:
        pickle.dump(plan_map, cache)

#Generate the plan cache if run directly
if __name__ == "__main__":
    generate_plan_cache()
    