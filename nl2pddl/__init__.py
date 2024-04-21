"""
The NL2PDDL module acts as an API for the NL2PDDL pipeline. 
It exposes high level pipeline functions that can be used to
generate prompts, evaluate a language model on those prompts,
parse the outputs of the language model, compute metrics on
the parsed outputs, and plot figures and tables based on the
metric results.
"""
import os

# Cache Generation
from .utils.pddl_cache import generate_pddl_cache
from .utils.plan_cache import generate_plan_cache, load_original_plan_map

# Import all functions the module exposes
from .generate_prompts import generate_prompts
from .call_llm import eval_llm_on_prompts, save_llm_outputs_file
from .parse_llm_outputs import parse_llm_outputs_from_file, save_parsed_outputs_file
from .compute_metrics import compute_metrics, compute_metrics_from_file, save_metrics_results_file
from .parse_metric_results import parse_metric_results_to_file
from .plot_figures_and_tables import plot_all

#Generate PDDL and Plan Cache if they do not exist
if not os.path.exists("pddl_cache.pkl"):
    print("Generating PDDL Cache")
    generate_pddl_cache()

if not os.path.exists("plan_cache.pkl"):
    print("Generating Plan Cache")
    generate_plan_cache()
