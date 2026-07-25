# RELAY Core domain

**Domain ID:** `relay.domain.core`  
**Status:** proposal  
**Version:** 0.1.0

The Core domain is deliberately thin. It provides stable identities and relations required by all other Domains and Packages.

## Dataset identity

```text
Dataset
└── DatasetRelease
```

A Dataset is the stable conceptual collection. A DatasetRelease is an immutable, versioned snapshot. Package format is not part of DatasetRelease identity; the same release may be distributed through several ExchangePackages.

## Agents

```text
Agent
├── Person
├── Organization
├── SoftwareAgent
└── AutomatedService
```

Every Agent has a RELAY UID. External identifiers are attached through `EntityIdentifier`: ORCID for Persons, ROR for research Organizations, and DOI or repository identifiers for citable releases such as data, protocols, publications, and software.

A SoftwareAgent identifies versioned software. An AutomatedService identifies a deployed service instance and may link to the software it uses and the Organization that operates it.

## Affiliations and roles

`Affiliation` and `RoleAssignment` are distinct time-bounded relations. Institutional affiliation does not imply a study role, and a study role does not imply employment or affiliation.

## Locations and physical resources

`Location` is restricted to stable spatial contexts such as sites, buildings, facilities, rooms, and controlled areas.

Cages, racks, rack positions, instruments, cameras, sensors, force meters, freezers, and storage containers are PhysicalResources. A time-bounded `ResourcePlacement` locates a PhysicalResource in a Location or on, in, or within another PhysicalResource.

Domain-specific details remain elsewhere:

```text
cages and rack occupancy       → housing-cages
instruments and sensors        → assays-acquisition
environmental sensors/readings → environment
biospecimen containers         → biospecimens
```

## Provenance

Metadata creation, import, migration, correction, validation, and release are represented as `ProvenanceEvent` objects with typed `ProvenanceLink` participation. Scientific analysis provenance remains in `analysis-qc`.

## Boundary

Core does not contain Investigation, Study, Assay, subject, cage, environment measurement, protocol, observation, scientific data asset, or package-serialization detail. It supplies the stable identities those Domains reuse.
