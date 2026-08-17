# Release Model

One portable source tree produces a source zip and one package per adapter.
`tools/build_release.py` validates source and staging trees, writes relative
paths and checksums to the release manifest, and must run after the fixtures.
