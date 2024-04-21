
"""
This file contains code for calling LLMs via IBM GenAI API, 
and saving the raw model outputs.
"""

#Standard Libs
import os
import time
import json
import copy
from typing import Any

#External Libs
from dotenv import load_dotenv
from genai.model import Credentials, Model
from genai.schemas import GenerateParams

from .generate_prompts import generate_prompts

# These defaults are used if no other model or parameters are provided
DEFAULT_MODEL = "bigcode/starcoder"
DEFAULT_PARAMS = {
    "decoding_method" : "greedy",  #Sample or greedy
    #The maximum number of tokens allowed in model output
    "max_new_tokens" : 300,
    "stop_sequences": ["Input:", "Allowed Predicates:"],
    "temperature" : 0.1,
}

def call_lmm(
    tasks : dict[str, Any], model_name = DEFAULT_MODEL,
    generation_parameters = None
) -> list[dict[str, Any]]:
    """
    Run the LLM provided by `model_name` with the given parameters 
    `generation_parameters` on the given prompts provided by `tasks`.
    returns a list of tasks with the LLMs outputs appended to the results.
    for ach  
    """
    #PEP8 way of handling default dict arguments
    if generation_parameters is None:
        generation_parameters = DEFAULT_PARAMS

    #Setup GenAI API credentials and settings
    load_dotenv()
    api_key = os.getenv("GENAI_KEY")
    api_endpoint = os.getenv("GENAI_API")
    creds = Credentials(api_key, api_endpoint)
    params : GenerateParams = GenerateParams(**generation_parameters)
    model : Model = Model(model_name, params=params, credentials=creds)
    task_results = []
    prompts = [t["prompt"] for t in tasks]
    #Note the unorthodox use of zip here to associate
    #prompt data with an asynchronous generator result.
    #The prompts still match with the correct task.
    for task, result in zip(tasks, model.generate_async(prompts)):
        task_copy = copy.deepcopy(task)
        try:
            task_copy["results"].append({
                "model" : model_name,
                "parameters" : generation_parameters,
                "output" : result.generated_text,
                "error" : False,
                "errorMsg" : ""
            })
        except AttributeError as e:
            task_copy["results"].append({
                "model" : model_name,
                "parameters" : generation_parameters,
                "output" : "",
                "error" : True,
                "errorMsg" : str(e)
            })
        task_results.append(task_copy)
    return task_results

def eval_llm_on_prompts(
    prompts_file_path : str,
    model_name : str = DEFAULT_MODEL,
    generation_parameters = None
) -> dict[str, Any]:
    """
    call_lmm except takes a json file task instead of a task list
    """
    #PEP8 way of handling default dict arguments
    if generation_parameters is None:
        generation_parameters = DEFAULT_PARAMS
    with open(prompts_file_path, "r", encoding="utf-8") as prompts_file:
        prompts_data = json.load(prompts_file)
        return call_lmm(prompts_data, model_name, generation_parameters)

def save_llm_outputs_file(outputs : list[dict[str, Any]]) -> None:
    """
    Given a list of tasks with LLM outputs, save the outputs to a file.
    """
    timestamp = int(time.time())
    outfile_name = f"outputs-{timestamp}.json"
    with open("llmOutputs/" + outfile_name, "w", encoding="utf-8") as outfile:
        json.dump(outputs, outfile, indent=2)

#This is what is called to actually generate the prompts
if __name__ == "__main__":
    prompt_tasks = generate_prompts(60, 3, "data/domainNL", "Base-HC.csv", [])
    greedy_params = {
        "decoding_method" : "greedy",  #Sample or greedy
        #The maximum number of tokens allowed in model output
        "max_new_tokens" : 300,       
        "stop_sequences": ["Input:", "Allowed Predicates:"],
        "temperature" : 0.1,
    }
    results = call_lmm(prompt_tasks, "bigcode/starcoder", greedy_params)
    save_llm_outputs_file(results)
    results = call_lmm(results, "meta-llama/llama-2-7b", greedy_params)
    results = call_lmm(results, "meta-llama/llama-2-7b-chat", greedy_params)
    save_llm_outputs_file(results)
    results = call_lmm(results, "meta-llama/llama-2-13b", greedy_params)
    results = call_lmm(results, "meta-llama/llama-2-13b-chat", greedy_params)
    save_llm_outputs_file(results)
    results = call_lmm(results, "meta-llama/llama-2-70b-chat", greedy_params)
    results = call_lmm(results, "meta-llama/llama-2-70b", greedy_params)
    save_llm_outputs_file(results)
