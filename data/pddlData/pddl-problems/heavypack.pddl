(define (domain heavy-pack)
    (:requirements :typing)
   (:types item)
   (:predicates
		(heavier ?item1 - item ?item2 - item)
        (packed ?item - item)
        (unpacked ?item - item)
        (nothing-above ?item - item)
        (box-empty)
	)

   (:action pack-first
       :parameters (?item - item)
       :precondition (and (box-empty))
       :effect (and (not (box-empty)) (packed ?item) (nothing-above ?item) (not (unpacked ?item))))

   (:action stack
       :parameters (?bottom - item ?top - item)
       :precondition (and (packed ?bottom) (nothing-above ?bottom) (heavier ?bottom ?top) (unpacked ?top))
       :effect (and (packed ?top) (nothing-above ?top) (not (nothing-above ?bottom)) (not (unpacked ?top))))
)