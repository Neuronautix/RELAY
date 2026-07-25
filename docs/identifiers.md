# Identifiers and agents

**Classification:** normative draft  
**Status:** proposal

## Internal identity

Every canonical research entity has a RELAY UID. A UID is independent of labels, local spreadsheet row numbers, and mutable database keys. Application profiles may constrain the UID representation to a UUID, URI, repository accession, or another globally unique form.

## External identifiers

External identifiers are represented through a generic `EntityIdentifier` object with:

```text
identifier scheme
lexical value
canonical URI
identifier role
issuing agent
assignment date
status
source or evidence
```

An external identifier is never inferred only from a label.

Preferred identifier patterns include:

| Entity | Preferred external identifier when available |
|---|---|
| Person | ORCID |
| Research organization | ROR |
| Dataset concept | Concept DOI or repository concept PID |
| DatasetRelease | Version-specific DOI or repository release PID |
| Protocol release | DOI or versioned repository accession |
| Software release | DOI and/or immutable source release identifier |
| Source code state | Repository URI plus commit SHA |
| Repository deposit | DOI or repository accession |
| Automated service | Stable service URI and RELAY UID |

A repository platform such as Zenodo or GitHub is represented as an Organization or AutomatedService. A DOI normally identifies a deposited dataset, protocol, publication, or software release—not the platform itself.

## Dataset and DatasetRelease

```text
Dataset
  stable conceptual identity
    └── DatasetRelease
          immutable versioned snapshot
```

A concept DOI may identify the Dataset. A version DOI may identify a DatasetRelease. Once a DatasetRelease has status `released`, corrections create a new DatasetRelease linked to the previous release.

## Agent model

```text
Agent
├── Person
├── Organization
├── SoftwareAgent
└── AutomatedService
```

A SoftwareAgent is a versioned software component capable of acting in a process. An AutomatedService is a deployed service or operating instance that uses software and is operated by an Agent.

## Affiliations and roles

An `Affiliation` is a time-bounded Person–Organization relationship. A `RoleAssignment` states what an Agent did in a particular context. They are separate and neither is inferred from the other.

Example:

```text
Person A affiliated with Organization X from 2024 to 2027
Person A acted as study principal investigator
Person A acted as assay operator for execution E17
Person A curated DatasetRelease 1.2
```
