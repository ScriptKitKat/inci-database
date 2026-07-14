"""User-submitted product verification pipeline.

Standalone package: verifies submitted products and ingredient tokens
against authoritative sources before anything reaches the canonical
catalog. Canonical spellings only ever come from authoritative-source
strings, never from LLM output.
"""
