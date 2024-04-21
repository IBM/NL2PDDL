
"""
This file contains code for getting predicates
and various properties from PDDL objects.
"""

from pddl.core import Domain, Action, Formula
from pddl.logic.predicates import Predicate
from pddl.logic.base import Not

def preds_pos_neg(p : Formula) -> tuple[set[Predicate], set[Predicate]]:
    """
    For an precondition or effect formula p, returns two sets,
    the first of non-negated predicate objects, and the latter of negated 
    predicate objects
    """
    pos : set[Predicate] = set()
    neg : set[Predicate] = set()
    def aux(pn : Formula) -> None:
        """Takes a formula and depending on its type, adds it to pos or neg sets"""
        if isinstance(pn, Predicate):
            pos.add(pn)
        elif isinstance(pn, Not):
            neg.add(pn.argument)
    aux(p)
    if hasattr(p, "operands"):
        for operand in p.operands:
            aux(operand)
    return pos, neg

def preds(p : Formula) -> set[Predicate]:
    """
    given a effect or precondition formula p, return the set of all
    predicates in the formula.
    """
    pos, neg = preds_pos_neg(p)
    return pos.union(neg)

def names(ps : set[Predicate]) -> set[str]:
    """Given a set of predicates ps, return a set of their names"""
    return {p.name for p in ps}

def names_with_params(ps : set[Predicate]) -> set[str]:
    """Given a set of predicates ps, return a set of formatted 
    strings containing their name and parameter names in an 
    S-Expression syntax"""
    return set(["(" + p.name + (" " if len(p.terms) > 0 else "") +
                 " ".join([t.name for t in p.terms]) + ")" for p in ps])

def has_contradiction(p : Formula) -> bool:
    """
    given a effect or precondition formula p, return if it contains
    a contradiction, (p n) and (not (p n)) 
    """
    pos, neg = preds_pos_neg(p)
    return len(list(pos.intersection(neg))) != 0

def domain_pred_names(domain : Domain) -> set[str]:
    """
    Given a domain, return the set of names of predicates
    in the domain.
    """
    predicate_list = list(domain.predicates)
    return {pred.name for pred in predicate_list}

def obvious_static(domain : Domain) -> set[str]:
    """
    Given a domain, return the obviously static predicates.
    That is, any predicates who do not appear in any
    action effects
    """
    dynamic = domain_pred_names(domain)
    for action in domain.actions:
        dynamic = dynamic.difference(names(preds(action.effect)))
    return dynamic

def possible_dynamic(domain) -> set[str]:
    """
    Given a domain, return the possible dynamic predicates.
    That is, any predicates who may appear in effects
    """
    static_predicates = obvious_static(domain)
    return domain_pred_names(domain).difference(static_predicates)

def pos_dynamic_for_action(d : Domain, a : Action) -> set[Predicate]:
    """
    Given a domain and an action, return the set
    of predicates that are dynamic and used
    in either a precondition or effect of that action.
    """
    pos_dynamic_action : set[str] = set()
    pos_dynamic_domain : set[str] = possible_dynamic(d)
    for pred in preds(a.precondition).union(preds(a.effect)):
        if pred.name in pos_dynamic_domain:
            pos_dynamic_action.add(pred)
    return pos_dynamic_action

def flipped(action : Action) -> set[Predicate]:
    """
    Given an action, return the set of predicates in the action
    that are explicitly flipped. That is,
    predicates that are positive in the precondition and negated
    in the effect OR negative in the precondition and 
    positive in the effect.
    """
    flipped_set : set[Predicate] = set()
    pre_p, pre_n = preds_pos_neg(action.precondition)
    eff_p, eff_n = preds_pos_neg(action.effect)
    for pre_pi in pre_p:
        if pre_pi in eff_n:
            flipped_set.add(pre_pi)
    for pre_ni in pre_n:
        if pre_ni in eff_p:
            flipped_set.add(pre_ni)
    return flipped_set
