"""Package marker for the research assistant library.

Deliberately empty of behaviour. Re-exporting the leaf modules here would make
``import src`` pull in pypdf, scikit-learn and (from Phase 5) streamlit, which
slows every test collection and hides import errors. Callers import the module
they actually need: ``from src.pdf_ingestion import load_document``.
"""

__version__ = "0.2.0"
__all__ = ["__version__"]