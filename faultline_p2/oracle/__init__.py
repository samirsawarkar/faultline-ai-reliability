"""faultline_p2.oracle

Re-exports the byte-for-byte pinned copy of day01/faultline/oracle.py.
Provenance: copied from day01/faultline/oracle.py, verified by test_frozen_copies.py.
"""
from faultline_p2.oracle._day01_oracle import normalize, oracle_check

__all__ = ["oracle_check", "normalize"]
