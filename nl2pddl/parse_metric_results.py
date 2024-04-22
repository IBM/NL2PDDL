"""
This file contains code for cleaning up the raw metric results
"""

import csv

def parse_metric_results_to_file(results, out_path):
    """
    Cleans up the raw metric results and writes them to a CSV file at out_path
    """
    with open(out_path, "w", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["domain", "action", "class", "model", "resultClass",
                          "subClass", "actionDif", "planDif"])
        #results = json.load(open(results_file, "r"))
        for task in results:
            for result in task["results"]:
                if "google" in result["model"]:
                    continue
                if "errorClass" in result.keys() and result["errorClass"] != "":
                    result["resultClass"] = result["errorClass"]
                    result["errorSubclass"] = ""
                #Accidentally marked these type errors and syntax errors, this fixes this
                if result["resultClass"] == "SyntaxError" and "VisitError" in result["errorMsg"]:
                    result["resultClass"] = "SemanticError"
                    result["errorSubclass"] = "TypeError"
                if result["resultClass"] == "ModelError":
                    continue
                if result["resultClass"] == "PlanError":
                    continue
                writer.writerow([
                    task["domain"], task["action"],
                    task["class"], result["model"], result["resultClass"],
                    result["errorSubclass"], result["actionDif"], result["workingPlans"]])
            