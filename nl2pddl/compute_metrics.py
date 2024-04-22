
"""
This file contains code for metric computation and evaluation of the parsed
LLM output, including computing the Action Reconstruction Error, and 
Heuristic Domain Equivalence Metric.
"""

#Standard Libs
import json
import copy
import time
from typing import Any

#External Libs
from tqdm import tqdm     #For progress bar
from pddl.core import Action, Formula
from pddl.logic.terms import Variable
from pddl.logic.predicates import Predicate

#Internal Libs
from .parse_llm_outputs import str_to_action
from .utils.plan_cache import load_original_plan_map
from .utils.pddl_cache import domainProblemPathMap, domainPathMap
from .utils.pddl_properties import preds_pos_neg, names_with_params
from .utils.plan_and_val import plan_str, can_apply_plan, plan_to_string

#Action Reconstruction Error Metric ============================================

def param_map(original : Action, reconstructed : Action) -> dict[str, str]:
    """
    Creates a parameter map between the parameter names in the original action
    and the reconstructed action. Any extra parameters
    are mapped to their own names.

    This Assumes parameters are in the same order in both actions, for this 
    work, all NL descriptions are careful to list the parameters in the order
    they appear in the PDDL for the context examples.  
    """
    correct_params : list[Variable] = original.parameters
    new_params = reconstructed.parameters
    result_map = {c.name : n.name for c, n in zip(correct_params, new_params)}
    #Handle any extra parameters
    new_longer : bool = len(correct_params) > len(new_params)
    longer = correct_params if new_longer else new_params
    shorter = correct_params if not new_longer else new_params
    for i in range(len(shorter), len(longer)):
        name = longer[i].name
        result_map[name] = name
    return result_map

def mapped_pred_strs(predicates : set[Predicate],
                    parameter_map : dict[str, str])-> set[str]:
    """
    Given a set of predicates ps, map them to their parameterized s-expression
    strings using the new parameter names specified by the parameter map.

    Example:
    predicates: {P(a,x), Q(x), R(b)}
    parameter_map: {"x":"z"}
    returns {"(P a z)", "(Q z)", "(R b)"}
    """
    return {"(" + p.name + (" " if len(p.terms) > 0 else "") +
            " ".join([parameter_map[t.name] for t in p.terms]) + 
            ")" for p in predicates}

# def _negatePredStrs(predicate_strs : list[str]):
#     """
#     Given a set of predicates in their string s-expression form,
#     wrap them in an enclosing (not ...)
#     """
#     return set(["(not " + p + ")" for p in predicate_strs])

def mapped_sym_dif_names(ps1 : set[Predicate], ps2 : set[Predicate],
                       parameter_map : dict[str, str]):
    """
    Returns the names of symmetric difference of ps1 and ps2 after ps1 has had
    its parameter names mapped to those of ps2.

    Example:
    ps1: {P(a,x), Q(x), R(b)}
    ps2: {P(a,z), Q(z), R(b), S(z)}
    """
    ps1_mapped : set[str] = mapped_pred_strs(ps1, parameter_map)
    ps2_strs : set[str]  = names_with_params(ps2)
    return ps1_mapped.symmetric_difference(ps2_strs)

def formula_recons_err(original : Formula, reconstructed : Formula, \
                         parameter_map : dict[str, str]) -> int:
    """
    Scores difference between two formulas by counting the number of
    differences in predicates between them after mapping the variable names.
    """
    o_pos, o_neg = preds_pos_neg(original)
    r_pos, r_neg = preds_pos_neg(reconstructed)
    pre_pos_dif = mapped_sym_dif_names(o_pos, r_pos, parameter_map)
    pre_neg_dif = mapped_sym_dif_names(o_neg, r_neg, parameter_map)
    return len(pre_pos_dif) + len(pre_neg_dif)

def action_recons_err(original : Action, recons : Action) -> int:
    """
    This metric measures the difference between two PDDL actions by counting
    the number of differences in the number of preconditions and effects
    between them. 
    
    * A negated version of a predicated is counted as a different predicate
    * The order the predicates appear in the precondition and effect is not
      relevant
    * Assumes action parameters appear in the same order, but they need not
      have the same names. 
    """
    p_map = param_map(original, recons)
    pre_dif = formula_recons_err(original.precondition, recons.precondition, p_map)
    eff_dif = formula_recons_err(original.effect, recons.effect, p_map)
    total_dif = eff_dif + pre_dif
    return total_dif

    # #Precondition Difference
    # o_pre_pos, o_pre_neg = preds_pos_neg(original.precondition)
    # r_pre_pos, r_pre_neg = preds_pos_neg(reconstructed.precondition)
    # pre_pos_dif = mapped_sym_dif_names(o_pre_pos, r_pre_pos, parameter_map)
    # pre_neg_dif = mapped_sym_dif_names(o_pre_neg, r_pre_neg, parameter_map)
    # pre_dif = len(pre_pos_dif) + len(pre_neg_dif)

    # #Effect Difference
    # o_eff_pos, o_eff_neg = preds_pos_neg(original.effect)
    # r_eff_pos, r_eff_neg = preds_pos_neg(reconstructed.effect)
    # eff_pos_dif = mapped_sym_dif_names(o_eff_pos, r_eff_pos, parameter_map)
    # eff_neg_dif = mapped_sym_dif_names(o_eff_neg, r_eff_neg, parameter_map)
    # eff_dif = len(eff_pos_dif) + len(eff_neg_dif)

def task_action_recons_err(task : list[dict[str, Any]], result ) \
-> tuple[int, str, str, str]:
    """
    This function wraps the action_recons_err function to compute the difference
    between the original action and the reconstructed action in a task
    """
    ast, err1, err2, err_msg = str_to_action(result["output"], task["domain"])
    if ast is None:
        return float('nan'), err1, err2, err_msg
    correct_ast, err1, err2, err_msg = str_to_action(task["pddl"], task["domain"])
    if correct_ast is None:
        print("Original PDDL Tree failure, THIS SHOULD NEVER HAPPEN")
        raise RuntimeError()
    are_score = action_recons_err(correct_ast, ast)
    return are_score, "", "", ""

#Heuristic Domain Equivalence Metric ===========================================

def heuristic_equiv(domain_name : str, new_domain : str) \
-> tuple[int, str, str, str]:
    """
    Returns a tuple of 
    1) the result class string (EqDomain or DifDomain)
    2) An optional subclass string of the error if DifDomain
    3) An optional error message about why the domains are different
    """
    num_working = 0 #the number of plans that worked
    original_domain_plans : list[dict[str, Any]] = \
        load_original_plan_map()[domain_name]
    for problem_path, original_plans_obj in \
    zip(domainProblemPathMap[domain_name], original_domain_plans):
        plans_obj, err1, err2, err_msg = plan_str(new_domain, problem_path)
        if plans_obj is None:
            return 0, err1, err2, err_msg
        plans = plans_obj["plans"]
        original_plans = original_plans_obj["plans"]
        if len(plans) != len(original_plans):
            #The size of a cached len(original_plans) plans list did
            #not match the size of generated plans len(plans) list for the
            #this means the domains were different
            return num_working, "DifDomain", "OriginalToNew", "k diff error"
        for original_plan, new_plan in zip(original_plans, plans):
            #convert the plan to a format VAL can accept it in
            can_apply, err1, err2, err_msg = \
                can_apply_plan(domainPathMap[domain_name] , new_domain, \
                               problem_path, plan_to_string(original_plan), \
                               plan_to_string(new_plan))
            if not can_apply:
                if err2 == "OriginalToNew":
                    num_working += 1
                return num_working, err1, err2, err_msg
            num_working += 1
    return num_working, "EqDomain", "", ""

# Evaluation ===================================================================

def compute_metrics(tasks : list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Adds metric computations to the plan objects
    """
    updated = []
    for task in tqdm(tasks, "Tasks"):
        task_copy = copy.deepcopy(task)
        domain_name = task_copy["domain"]
        for result in task_copy["results"]:
            #result["planDif"] = float('nan')
            result["actionDif"] = float('nan')
            result["workingPlans"] = 0
            if not result["error"]:
                #Compute Action Reconstruction Error
                are_score, result_class, result_subclass, err_msg = \
                    task_action_recons_err(task_copy, result)
                if result_class == "":
                    result["actionDif"] = are_score
                else:
                    result["error"] = True
                    result["resultClass"] = result_class
                    result["errorSubclass"] = result_subclass
                    result["errorMsg"] = err_msg
                    continue
                #Determine Heuristic Domain Equivalence
                new_domain = result["newDomain"]
                work_count, result_class, result_subclass, err_msg = \
                    heuristic_equiv(domain_name, new_domain)
                result["workingPlans"] = work_count
                result["resultClass"] = result_class
                result["errorSubclass"] = result_subclass
                result["errorMsg"] = err_msg
                result["error"] = not result_class == "EqDomain"
        updated.append(task_copy)
    return updated

def compute_metrics_from_file(parsed_outputs_file_path : str) \
-> list[dict[str, Any]]:
    """
    Given a file path to parsed file outputs, use them to compute the metrics
    and return the updated task list.
    """
    with open(parsed_outputs_file_path, "r", encoding="utf-8") as json_file:
        results = json.load(json_file)
    return compute_metrics(results)

def save_metrics_results_file(metric_results : list[dict[str, Any]], \
                              metrics_file_path : str = None) -> None:
    """
    Save the metric results to a file at an optional metrics_file_path
    """
    if metrics_file_path is None:
        timestamp = int(time.time())
        metrics_file_path = f"results/metrics-{timestamp}.json"
    with open(metrics_file_path, "w", encoding="utf-8") as outfile:
        json.dump(metric_results, outfile, indent=2)

#For Testing
if __name__ == "__main__":
    with open("parsedOutputs/Greedy-All.json", "r", encoding="utf-8") as greedy_file:
        task_list = json.load(greedy_file)
        tasks_with_metrics = compute_metrics(task_list)
        save_metrics_results_file(tasks_with_metrics)
