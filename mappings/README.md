# Mappings

Mappings are versioned first-class objects. They are not simple label correspondences.

Every mapping entry records:

```text
source element and version
target element and version
direction
relation type
conditions
transformation
information loss
cardinality or datatype impact
evidence
review status and reviewer
```

Permitted relation types initially include `exact`, `close`, `broader`, `narrower`, `related`, `structural`, and `transformation`. Empty proposal mappings are plans, not interoperability claims.
