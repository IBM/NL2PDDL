(define (problem newspaper2) (:domain trapnewspapers)
  (:objects
        loc-0 - location
	loc-1 - location
	loc-2 - location
	loc-3 - location
	loc-4 - location
	loc-5 - location
	loc-6 - location
	paper-0 - paper
	paper-1 - paper
  )
  (:init 
	(at loc-0)
	(ishomebase loc-0)
	(safe loc-0)
	(safe loc-2)
	(safe loc-4)
	(unpacked paper-0)
	(unpacked paper-1)
	(wantspaper loc-2)
	(wantspaper loc-4)
  )
  (:goal (and
	(satisfied loc-2)
	(satisfied loc-4)))
)