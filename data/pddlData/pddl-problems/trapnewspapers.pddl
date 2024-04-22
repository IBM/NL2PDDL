(define (domain trapnewspapers)
    (:requirements :strips :typing)
    (:types location paper)
    (:predicates 
        (at ?loc - location)
        (isHomeBase ?loc - location)
        (satisfied ?loc - location)
        (wantsPaper ?loc - location)
        (safe ?loc - location)
        (unpacked ?paper - paper)
        (carrying ?paper - paper)
    )
    
    (:action pick-up
        :parameters (?paper - paper ?loc - location)
        :precondition (and
            (at ?loc)
            (isHomeBase ?loc)
            (unpacked ?paper)
        )
        :effect (and
            (not (unpacked ?paper))
            (carrying ?paper)
        )
    )
    
    (:action move
        :parameters (?from - location ?to - location)
        :precondition (and
            (at ?from)
            (safe ?from)
        )
        :effect (and
            (not (at ?from))
            (at ?to)
        )
    )
    
    (:action deliver
        :parameters (?paper - paper ?loc - location)
        :precondition (and
            (at ?loc)
            (carrying ?paper)
        )
        :effect (and
            (not (carrying ?paper))
            (not (wantsPaper ?loc))
            (satisfied ?loc)
        )
    )
    
)