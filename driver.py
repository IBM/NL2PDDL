"""
This driver script starts with the raw LLM data we used for the
experiments in the paper, located in /data/output directory, generating
`parsedOutput`, `results`, and `parsedResults` files. 
"""

import nl2pddl as n2p

if __name__ == "__main__":
    # Compute Syntax and Semantic Errors on LLM outputs
    print("Computing Syntax and Semantic Errors on LLM outputs...")
    parsed_llm_outputs = n2p.parse_llm_outputs_from_file("data/llmOutputs/Greedy-All.json")
    n2p.save_parsed_outputs_file(parsed_llm_outputs, "data/parsedOutputs/Greedy-All.json")

    # Compute DiffDomain and Equiv classes and ARE scores
    print("Computing DiffDomain and EQDomain classes and ARE scores...")
    metrics = n2p.compute_metrics(parsed_llm_outputs)
    n2p.save_metrics_results_file(metrics, "data/results/Greedy-All.json")

    # Parse and clean final results into a CSV for plotting
    print("Cleaning Data and Plotting")
    n2p.parse_metric_results_to_file(metrics, "data/parsedResults/Greedy-All.csv")
    n2p.plot_all("data/parsedResults/Greedy-All.csv")
