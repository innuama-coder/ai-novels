# Adapter Authoring Guide

An adapter may translate instructions but cannot weaken the portable stage graph,
completion gate, plan/evidence rules or approval rules. Mark unavailable event
APIs as `manual`; do not imply that the runtime can supply external provenance.
