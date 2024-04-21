(define (problem newspaper1) (:domain trapnewspapers)
  (:objects
        loc-0 - location
	loc-1 - location
	loc-2 - location
	loc-3 - location
	loc-4 - location
	loc-5 - location
	loc-6 - location
	loc-7 - location
	loc-8 - location
	paper-0 - paper
	paper-1 - paper
	paper-2 - paper
  )
  (:init 
	(at loc-0)
	(ishomebase loc-0)
	(safe loc-0)
	(safe loc-2)
	(safe loc-3)
	(safe loc-8)
	(unpacked paper-0)
	(unpacked paper-1)
	(unpacked paper-2)
	(wantspaper loc-2)
	(wantspaper loc-3)
	(wantspaper loc-8)
  )
  (:goal (and
	(satisfied loc-2)
	(satisfied loc-3)
	(satisfied loc-8)))
)