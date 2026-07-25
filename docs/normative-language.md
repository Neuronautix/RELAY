# Normative language

The capitalized terms MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are interpreted as requirement levels only in content explicitly classified as normative.

* **MUST / MUST NOT** — required for conformance.
* **SHOULD / SHOULD NOT** — expected unless a documented, justified exception applies.
* **MAY** — permitted but optional.

Every normative requirement receives a stable Rule identifier. Validation reports refer to that identifier and record at least:

```text
rule_id
outcome: pass | fail | warning | not_applicable | not_tested
message
target entity or file
evidence or location
validator and version
```

Informative examples, rationale, and implementation advice do not add conformance obligations.

References: RFC 2119 and RFC 8174.
