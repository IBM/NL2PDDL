"""
This file uses the NL descriptions to generate prompts for an LLM
"""

#System Libraries
import os
import time
import json
from typing import Any

#External Libraries
import pandas as pd

#Internal Libraries
from .utils.pddl_cache import domainPredMap

PROMPT_TEMPLATE_DIR : str = "data/promptTemplates"
MAIN_TEMPLATE_PATH = os.path.join(PROMPT_TEMPLATE_DIR, "main.txt")
CTX_TEMPLATE_PATH = os.path.join(PROMPT_TEMPLATE_DIR, "context.txt")

#This is the main template for all context based prompts to the LLM
MAIN_TEMPLATE : str = ""
with open(MAIN_TEMPLATE_PATH, "r", encoding="utf-8") as main_template_file:
    MAIN_TEMPLATE = main_template_file.read()

#This is the template for each individual context example in the main prompt
CTX_TEMPLATE : str = ""
with open(CTX_TEMPLATE_PATH, "r", encoding="utf-8") as ctx_template_file:
    CTX_TEMPLATE = ctx_template_file.read()

def description_class_name(file_name : str) -> pd.DataFrame:
    """
    Description class files are assumed to conform to 
    a naming convention in which everything before the first hyphen
    is the name of the description class, this function extracts this name.
    """
    return file_name.split('-')[0]

def description_class_df(nl_folder : str, file_name : str) -> pd.DataFrame:
    """
    Returns a parsed dataframe for a given CSV importance class
    drops the preds column and renames the NL column for future df merging.
    """
    path = os.path.join(nl_folder, file_name)
    df = pd.read_csv(path)
    df = df.drop("preds", axis=1)
    df = df.rename(columns={"NL" : f"{file_name.split('-')[0]}"})
    return df

def input_gen(row : pd.Series, description_class : str) -> tuple[str, str]:
    """
    Using a row containing [Domain, Action, Base, ..., importanceCol, ...]
    "generate" / extract the NL for it.
    """
    allowed_predicates = domainPredMap[row["domain"]]
    input_nl = row["Base"]
    if description_class == "Base":
        input_nl += "."
    else:
        input_nl += " " + row[description_class]
    return allowed_predicates, input_nl

def context_gen(samples : pd.DataFrame, description_class) -> str:
    """
    generate a context (example string) from a dataframe of sampled actions.
    """
    context_string = ""
    for _, row in samples.iterrows():
        allowed_predicates, input_nl = input_gen(row, description_class)
        output_pddl = row["pddl"]
        context_string += CTX_TEMPLATE.format(
            allowed=allowed_predicates,
            input=input_nl,
            output=output_pddl)
    return context_string

def generate_prompts(
    # Number of prompts with different context generated for each action
    num_context_samples : int = 1,
    # Number of actions to sample and include in the context
    sample_size : int = 3,
    # Where to find the NL CSV files
    domain_nl_folder : str = "data/domainNL",
    # Where to find the base action descriptions
    base_nl_file : str = "Base-HC.csv",
    # Other files including action descriptions
    importance_class_files : list[str] = None
) -> list[dict[str, Any]]:
    """
    Generates a set of prompts. If N is the number of actions in the
    base_nl_file and importance_class_files, and M
    is the the total number of 
    generated will be N*context_samples.

    The object returned is a list of dicts meant to be a json objects
    representing a task that has the following schema:
        {
            "domain" : the name of the domain,
            "action" : the name of the action,
            "pddl" : the pddl representation of the action,
            "class" : the name of the importance class,
            "context" : list of objects stating what domains and actions
                        were used for the context
            [{
                "domain" : the domain the context was taken from,
                "action" : the action the context was taken from.
            }],
            "prompt" : the full prompt with context,
            "results" : [] an empty array for future run data on this task
        }
    """
    #PEP8 way of handling default array arguments
    if importance_class_files is None:
        importance_class_files = ["Flipped-HC.csv", "Rand-HC.csv"]

    importance_class_names = [description_class_name(file) \
                              for file in importance_class_files]
    importance_class_names.append("Base")
    #Merge the importance class CSV files using a dataframe
    #Final dataframe will have the following header format:
    # domain, action, pddl, base NL, class 1 NL, class 2 NL, ..., class n NL
    # where base NL is the NL description of the action with no predicates
    # and class n NL is NL information about the predicates specified by
    # class n.
    df = description_class_df(domain_nl_folder, base_nl_file)
    for file_name in importance_class_files:
        importance_df = description_class_df(domain_nl_folder, file_name)
        df = pd.merge(df, importance_df, "inner", ["domain", "action", "pddl"])

    #Loop through each action and create samples for it.
    prompts = []
    for _, row in df.iterrows():
        for importance_class_name in importance_class_names:
            #Ensure context samples are only from rows outside of our domain
            #but in our class
            remaining_rows = df[df.domain != row.domain]
            for _ in range(num_context_samples):
                context_samples : pd.DataFrame = \
                    remaining_rows.sample(n=sample_size)
                allowed_predicates, input_nl = \
                    input_gen(row, importance_class_name)
                context_string = \
                    context_gen(context_samples, importance_class_name)
                #use the prompt template to generate the final prompt
                prompt = MAIN_TEMPLATE.format(
                    allowed = allowed_predicates,
                    context = context_string,
                    input = input_nl
                )
                prompts.append({
                    "domain" : row["domain"],
                    "action" : row["action"],
                    "pddl" : row["pddl"],
                    "class" : importance_class_name,
                    "context" : [{
                        "domain" : ctx_row["domain"],
                        "action" : ctx_row["action"]
                    } for _, ctx_row in context_samples.iterrows()],
                    "prompt" : prompt,
                    "results" : []
                })
    return prompts

if __name__ == "__main__":
    generated_prompts = generate_prompts()
    timestamp = int(time.time())
    outfile_name = f"prompts-{timestamp}.json"
    with open("data/prompts/" + outfile_name, "w", encoding="utf-8") as outfile:
        json.dump(generated_prompts, outfile, indent=2)
