(define (domain hiking)
  (:requirements :strips :typing)
  (:types location)

(:predicates
  (at ?loc - location)
  (isWater ?loc - location)
  (isHill ?loc - location)
  (adjacent ?loc1 - location ?loc2 - location)
  (onTrail ?from - location ?to - location)
)

(:action walk
  :parameters (?from - location ?to - location)
  :precondition (and
    (not (isHill ?to))
    (at ?from)
    (adjacent ?from ?to)
    (not (isWater ?from)))
  :effect (and (at ?to) (not (at ?from)))
)

(:action climb
  :parameters (?from - location ?to - location)
  :precondition (and
    (isHill ?to)
    (at ?from)
    (adjacent ?from ?to)
    (not (isWater ?from)))
  :effect (and (at ?to) (not (at ?from)))
)
)