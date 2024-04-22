(define (domain track-building)
    (:requirements :strips :typing)
    (:types location)

   (:predicates
		(agent-at ?loc - location)
		(train-at ?loc - location)
		(has-track ?loc - location)
        (forward ?loc1 - location ?loc2 - location)
	)

   (:action build-track
       :parameters  (?loc - location)
       :precondition (and (agent-at ?loc))
       :effect (and  (has-track ?loc)))

   (:action move-agent
       :parameters (?current-loc - location ?next-loc - location)
       :precondition (and (agent-at ?current-loc))
       :effect (and  (agent-at ?next-loc) (not (agent-at ?current-loc))))

   (:action move-train
       :parameters  (?current-loc - location ?next-loc - location)
       :precondition (and (train-at ?current-loc) (has-track ?next-loc)
                          (forward ?current-loc ?next-loc))
       :effect (and  (train-at ?next-loc) (not (train-at ?current-loc))))
)