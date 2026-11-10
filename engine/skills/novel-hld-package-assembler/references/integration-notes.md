# Integration notes

## HK1 identifier boundary

The canonical boundary is:

- HK1 designs `lld_work_requirements` identified by `LWR-*`.
- HP1 projects each accepted requirement to `LWK-*` with the identical suffix.
- HP1 rejects an HK1 input already named `LWK-*`; accepting it would erase owner provenance and make bijection ambiguous.

Some pre-HP1 HK1 prose or validation may still describe the requirement as `LWK-*`. That is a producing-stage contract defect for the main-chain owner to correct. HP1 deliberately does not edit HK1.

## Release portability follow-up

The HLD release builder must ultimately archive the Harness plus every skill named by the routing contract, including the three HH1 subskills. An archive containing only the Harness is not an installable chain. This is an integration/release concern, not HP1 package semantics.
