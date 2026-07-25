# RELAY RO-Crate Exchange Package

**Package ID:** `relay.package.ro-crate`  
**Base specification:** RO-Crate 1.3  
**Status:** proposal

The Root Data Entity represents exactly one RELAY DatasetRelease. The stable Dataset concept is linked separately. Attached and detached crates are permitted unless an application Profile narrows the choice.

RELAY will publish a persistent, versioned RO-Crate Profile URI and Profile Crate before candidate release. Until then, GitHub paths are provisional documentation locations rather than permanent conformance identifiers.

The package imposes stronger inventory and integrity requirements than the open-ended base crate: included immutable payload files are listed with content role, media type, byte size, and SHA-256 checksum. An external repository or transfer process records the checksum of the final archive.

ISA-JSON or ISA-Tab may be included. Mapping to ISA RO-Crate/ISA-Crate is explicit and versioned; it does not redefine the RELAY crate root or Core model.
