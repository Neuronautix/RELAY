# Profiles

Profiles select and constrain existing Terms and Domains for one use case. They state required, recommended, optional, conditional, and excluded content.

`requirements` classifies Terms, while `rule_requirements` independently
classifies conformance Rules. A Term or Rule belongs to only one category;
conditional requirements are evaluated when their stated condition applies.

A Profile may:

* import several Domains;
* narrow cardinalities or controlled values;
* add conditional requirements;
* require a particular Package;
* add profile-specific Rules and examples.

A Profile must not redefine a Term, weaken a claimed parent Profile without declaring non-conformance, or copy a Domain schema into a private fork.
