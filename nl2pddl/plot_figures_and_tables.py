"""
This file contains code for generating figures and tables from the cleaned
metric results.
"""
# pylint: disable=too-many-locals

# Standard Libraries
import os

# External Libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.legend_handler import HandlerBase
from matplotlib.text import Text

# Various Data For Figure Generation ===========================================

#Colors for different result classes
RESULT_CLASS_COLOR_MAP = {
    "SyntaxError" : "lightcoral",
    "SemanticError" : "orange",
    "DifDomain" : "gold",
    "EqDomain" : "lightgreen"
}

#Human readable result class names
RESULT_CLASS_NAME_MAP = {
    "SyntaxError" : "Syntax Error",
    "SemanticError": "Semantic Error",
    "DifDomain": "Diff Domain",
    "EqDomain" : "Equiv Domain"
}

#Human readable Description Class Names
DESC_CLASS_NAME_MAP = {
    "Base" : "Base",
    "Flipped" : "Flipped",
    "Rand" : "Random"
}

#Human readable Result Subclass Class Names
SUBCLASS_NAME_MAP = {
    "NoPlan" : "No Plan",
    "BadPDDL" : "Bad Predicate Arg #",
    "NewToOriginal" : "Could Not Apply New Plan",
    "OriginalToNew" : "Could Not Apply Original Plan",
    "ParseError" : "Bad PDDL Token",
    "DifActionName" : "Wrong Action Name",
    "ParenMismatch" : "Parenthesis Mismatch",
    "NegPrecond" : "Negated Precondition",
    "NoEffect" : "Missing keyword",
}

SUBCLASS_COLOR_MAP = {
    "NoPlan" : "sandybrown",  #DifDomain
    "NewToOriginal" : "gold", #DifDomain
    "OriginalToNew" : "khaki", #DifDomain
}

#List of all MODEL_NAMES used in figures
MODEL_NAMES = ['bigcode/starcoder',
          'meta-llama/llama-2-7b', 'meta-llama/llama-2-7b-chat',
            'meta-llama/llama-2-13b', 'meta-llama/llama-2-13b-chat',
           'meta-llama/llama-2-70b', 'meta-llama/llama-2-70b-chat']

#Size of the LLaMA MODEL_NAMES in billions of parameters
MODEL_SIZES = {
    "meta-llama/llama-2-7b" : 7,
    "meta-llama/llama-2-7b-chat" : 7,
    "meta-llama/llama-2-13b" : 13 ,
    "meta-llama/llama-2-13b-chat" : 13 ,
    "meta-llama/llama-2-70b" : 70,
    "meta-llama/llama-2-70b-chat" : 70,
}

#String replacement dictionary for table 1
TABLE_STRINGS = {
    "bigcode/starcoder" : "SC",
    "meta-llama/llama-2-7b-chat" : "7bC",
    "meta-llama/llama-2-13b-chat" : "13bC",
    "meta-llama/llama-2-70b-chat" : "70bC",
    "meta-llama/llama-2-7b" : "7b",
    "meta-llama/llama-2-13b" : "13b",
    "meta-llama/llama-2-70b" : "70b",

    "SyntaxError" : "Syntax",
    "ParseError" : "UToken",
    "ParenMismatch" : "PError",
    "NoEffect" : "NoPDDL",

    "SemanticError": "Semantics",
    "BadPDDL" : "PAError",
    "DifActionName" : "NError",
    "TypeError" : "TError",
    "NegPrecond" : "BPError",

    "DifDomain": "Diff",
    "NoPlan" : "NoPlan",
    "NewToOriginal" : "NPApp",
    "OriginalToNew" : "OPApp",

    "EqDomain" : "Equiv"
}

RESULT_CLASS_TABLE_ORDER = {
    "SyntaxError" : ["SyntaxError", "NoEffect", "ParenMismatch", "ParseError"],
    "SemanticError": ["SemanticError", "BadPDDL", "DifActionName", "TypeError", "NegPrecond"],
    "DifDomain" : ["DifDomain", "NoPlan", "NewToOriginal", "OriginalToNew"],
}

RESULT_CLASS_COLUMN_ORDER = [
    "bigcode/starcoder",
    "meta-llama/llama-2-7b",
    "meta-llama/llama-2-7b-chat",
    "meta-llama/llama-2-13b",
    "meta-llama/llama-2-13b-chat",
    "meta-llama/llama-2-70b",
    "meta-llama/llama-2-70b-chat"
]

#Scale of the pie charts
PIE_CHART_SIZE = 2

# Helpers ======================================================================


class GreenStarHandler(HandlerBase):
    """
    This pyplot legend handler adds the green star used to 
    mark the top performing model in each description class 
    to the legend
    """
    # pylint: disable=too-many-arguments
    def create_artists(self, legend, orig_handle ,xdescent, ydescent,
                        width, height, fontsize, trans):
        text_obj = Text(width/4.,height/4, orig_handle, fontsize=20,
                color="green", ha="center", va="center", fontweight="bold")
        return [text_obj]

def plot_pie_array(data, classes):
    """
    Creates a pie chart for each model in each class in the provided
    description class list `classes`
    """
    fig, axes = plt.subplots(nrows=len(classes), ncols=len(MODEL_NAMES),
                            figsize=(len(MODEL_NAMES)*PIE_CHART_SIZE + PIE_CHART_SIZE,
                            len(classes)*PIE_CHART_SIZE))

    #Labeling the rows and columns of the plot
    if len(classes) == 1 :
        #If we are plotting a single class, we only want to label the columns
        for ax, col in zip(axes, MODEL_NAMES):
            ax.set_title(col.split("/")[-1])
    else:
        #If we are plotting multiple classes, we want to label
        #both the rows and columns
        for ax, col in zip(axes[0], MODEL_NAMES):
            ax.set_title(col.split("/")[-1], x=0.5, y=1.1)
        for ax, row in zip(axes[:,0], classes):
            ax.set_ylabel(DESC_CLASS_NAME_MAP[row], rotation=90, size='large')

    # Plot the data
    vs = np.zeros((len(classes), len(MODEL_NAMES)))
    for i, class_name in enumerate(classes):
        cur_class = data[data["class"] == class_name]
        for j, model_name in enumerate(MODEL_NAMES):
            model_group = cur_class[cur_class["model"] == model_name]
            counts : pd.Series = model_group.value_counts("resultClass")
            ax = axes[i, j] if len(classes) > 1 else axes[j]
            ax.pie(
                x = counts,
                colors = [RESULT_CLASS_COLOR_MAP[c] for c, _ in counts.items()],
                autopct= lambda x: f"{x:.0f}%",
                textprops={'fontsize': 10},
                pctdistance=1.0
            )
            if len(classes) > 1:
                vs[i, j] = counts.loc["EqDomain"]

    handles = [mpatches.Patch(color=v, label=RESULT_CLASS_NAME_MAP[k]) \
               for k, v in RESULT_CLASS_COLOR_MAP.items()]
    if len(classes) == 1:
        fig.legend(handles=handles,
            labels = (list(RESULT_CLASS_NAME_MAP.values()) + ["Best in Class"]),
            ncol = 5,
            loc="lower center"
        )
    else:
        #Green Star Proxy Artist for legend
        for i, j in enumerate(np.argmax(vs, axis=0)):
            axes[j, i].text(0, 0, "*", fontdict={'fontsize': 30, "color" : "green"})
        handles.append("*")
        fig.legend(handles=handles,
            handler_map={str: GreenStarHandler()},
            labels=(list(RESULT_CLASS_NAME_MAP.values()) + ["Best in Class"]),
            ncol = 5,
            loc="lower center"
        )
    return fig

# Plotters for individual figures and tables ===================================

def fig_2_top(data):
    """
    Generate a figure with pie charts over result classes for each model in 
    the Base description class
    """
    plt.clf()
    fig = plot_pie_array(data, ["Base"])
    fig.savefig("figures_and_tables/Fig2Top.png", bbox_inches='tight')

def fig_2_bottom(data):
    """
    Generate a figure with pie charts over the diff domain result subclasses
    for each model in the Base description class
    """
    classes = ["Base"]
    res_class = "DifDomain"
    fig_width = len(MODEL_NAMES)*PIE_CHART_SIZE + PIE_CHART_SIZE
    fig_height = len(classes)*PIE_CHART_SIZE
    fig, axes = plt.subplots(nrows=len(classes), ncols=len(MODEL_NAMES),
                             figsize=(fig_width, fig_height))

    for ax, col in zip(axes, MODEL_NAMES):
        ax.set_title(col.split("/")[-1])

    for class_name in classes:
        cur_class = data[data["class"] == class_name]
        for j, model_name in enumerate(MODEL_NAMES):
            model_group = cur_class[cur_class["model"] == model_name]
            model_group = model_group[model_group["resultClass"] == res_class]
            counts : pd.Series = model_group.value_counts("subClass")
            axes[j].pie(
                x = counts,
                colors = [SUBCLASS_COLOR_MAP[c] for c, _ in counts.items()], \
                autopct= lambda x: f"{x:.0f}%",
                textprops={'fontsize': 10},
                pctdistance=1.0
            )
    handles = [mpatches.Patch(color=v, label=SUBCLASS_NAME_MAP[k]) \
               for k, v in SUBCLASS_COLOR_MAP.items()]
    fig.legend(handles=handles,
        ncol = 5,
        loc="lower center"
    )
    fig.savefig("figures_and_tables/Fig2Bottom.png", bbox_inches='tight')

def fig_3(data):
    """
    Generate a figure with line plots showing LLaMA model parameter counts
    on the x-axis and the percentage of each result class on the y-axis
    """
    plt.clf()
    fig, ax = plt.subplots(figsize=[6.4, 4.8])
    yss2 = {key : [] for key in RESULT_CLASS_NAME_MAP}
    yss1 = {key : [] for key in RESULT_CLASS_NAME_MAP}
    xs1 = []
    xs2 = []
    #Iterate over llama models and group by model size and class
    for model_name, model_size in MODEL_SIZES.items():
        model = data[data["model"] == model_name]
        (xs1 if "chat" in model_name else xs2).append(model_size)
        for result_name, i in model.value_counts("resultClass").items():
            (yss1 if "chat" in model_name else yss2)[result_name].append(i/1920*100)
    #Plot the data
    for (lbl, ys1), (_, ys2) in zip(yss1.items(), yss2.items()):
        ax.plot(xs2, ys2, "o-", label=RESULT_CLASS_NAME_MAP[lbl] + "-base",
                color=RESULT_CLASS_COLOR_MAP[lbl])
        ax.plot(xs1, ys1, "o--", label=RESULT_CLASS_NAME_MAP[lbl] + "-chat",
                color=RESULT_CLASS_COLOR_MAP[lbl])
    ax.set_xlabel("LLaMA Parameter Count (Billions)")
    ax.set_ylabel("% in Class")
    ax.legend(ncols = 2, loc="center", bbox_to_anchor=[0.5,  -0.3])
    fig.savefig("figures_and_tables/Fig3.png", bbox_inches='tight')

def fig_4(data):
    """
    Generate a figure with a pie chart matrix of result classes for each model and
    each description class.
    """
    plt.clf()
    fig = plot_pie_array(data, list(data["class"].unique()))
    fig.savefig("figures_and_tables/Fig4.png", bbox_inches='tight')

def fig_5(data):
    """
    Generate a figure with histograms of action reconstruction error color 
    coded by result class for each model
    """
    plt.clf()
    classes = ["Base"] #Can be changed to generate a matrix of histograms for all classes
    data = data[data["actionDif"].notna()]
    models = MODEL_NAMES #list(data["model"].sort_index().unique())
    fig, axes = plt.subplots(
        nrows=len(classes),
        ncols=len(models),
        figsize=(
            len(models)*PIE_CHART_SIZE + 2*PIE_CHART_SIZE,
            len(classes)*PIE_CHART_SIZE
        ),
        sharey=True
    )
    if len(classes) > 1 :
        for ax, col in zip(axes[0], models):
            ax.set_title(col.split("/")[-1])
        for ax, row in zip(axes[:,0], classes):
            ax.set_ylabel(DESC_CLASS_NAME_MAP[row], rotation=90, size='large')
    else:
        for ax, col in zip(axes, models):
            ax.set_title(col.split("/")[-1])
    for i, class_name in enumerate(classes):
        cur_class = data[data["class"] == class_name]
        for j, model_name in enumerate(MODEL_NAMES):
            model_group = cur_class[cur_class["model"] == model_name]
            colors = []
            vals = []
            for e_name in ["EqDomain", "DifDomain", "SemanticError"] :
                e_class = model_group[model_group["resultClass"] == e_name]
                colors.append(RESULT_CLASS_COLOR_MAP[e_name])
                vals.append(e_class["actionDif"])
            ax = axes[i, j] if len(classes) > 1 else axes[j]
            ax.hist(vals, stacked=True, color=colors)
    handles = [mpatches.Patch(color=v, label=RESULT_CLASS_NAME_MAP[k])
                for k, v in RESULT_CLASS_COLOR_MAP.items()]
    axes[0].set_ylabel("# Actions")
    fig.supxlabel("Action Reconstruction Error (ARE)")
    fig.legend(handles=handles,
        labels=(list(RESULT_CLASS_NAME_MAP.values())),
        loc="lower center",
        bbox_to_anchor=[0.5, -0.2],
        ncol = 4
    )
    fig.subplots_adjust(bottom=0.25)
    fig.savefig("figures_and_tables/Fig5.png", bbox_inches='tight')

def table_1(data):
    """
    Generate a table of the percentages of each result class and
    result subclass for each model
    """
    base_data = data[data["class"] == "Base"]
    output_string = ""
    for result_class in RESULT_CLASS_NAME_MAP:
        results = base_data[base_data["resultClass"] == result_class].copy()
        totals = results.groupby(["model"]).value_counts(["resultClass"])\
                        .unstack(fill_value=0).stack().unstack()
        subtotals = results.groupby(["model"]).value_counts(["subClass"])\
                           .unstack(fill_value=0).stack().unstack()
        #Multiply by 3 since base class is 1/3 of the data
        subtotals = subtotals.multiply(3).divide(1920).multiply(100).astype(float)\
                             .round(2).applymap(lambda x : f"{x:.2f}")
        totals = totals.multiply(3).divide(1920).multiply(100).astype(float)\
                       .round(2).applymap(lambda x : f"{x:.2f}")
        if result_class == "EqDomain":
            joint = totals.transpose()
        else:
            joint = subtotals.join(totals, how="left").transpose()
        #Rearrange the cols to the order we want
        joint = joint[RESULT_CLASS_COLUMN_ORDER]
        #Append chunks of rows to the csv string result class by result class
        indexing_order : list[str]
        if result_class != "EqDomain":
            indexing_order = RESULT_CLASS_TABLE_ORDER[result_class]
        if result_class == "SyntaxError":
            output_string += joint.reindex(index=indexing_order).to_csv(header=True)
        elif result_class == "SemanticError":
            reindexed = joint.reindex(index=indexing_order)
            output_string += reindexed.to_csv(header=False)
        elif result_class == "DifDomain":
            output_string += joint.reindex(index=indexing_order).to_csv(header=False)
        elif result_class == "EqDomain":
            output_string += joint.to_csv(header=False)

    for k, v in TABLE_STRINGS.items():
        output_string = output_string.replace(k, v)
    with open("figures_and_tables/Table1.csv", "w", encoding="utf-8") as f:
        f.write(output_string)

# Plot All =====================================================================

def plot_all(filename):
    """
    Plot all figures and tables from the cleaned metric results and
    write them to their respective files in the figures_and_tables directory.
    """
    os.makedirs("figures_and_tables", exist_ok=True)
    data = pd.read_csv(filename)
    fig_2_top(data)
    fig_2_bottom(data)
    fig_3(data)
    fig_4(data)
    fig_5(data)
    table_1(data)
