"""
Base model with standard audit columns.

All domain models MUST inherit from CoopBase.
This ensures consistent:
  - UUID primary keys
  - created_at timestamps
  - Schema targeting (coop schema)

Models that track mutations should also include updated_at.
Models that track authorship should include created_by (FK to users).

IMPLEMENTATION NOTE FOR GEMINI:
  - Use SQLAlchemy 2.0 Mapped[] style (not legacy Column())
  - Use server_default for timestamps, not Python-side defaults
  - All monetary fields: Numeric(15, 2)
  - All tables go in schema='coop'
"""

# --- SKELETON — Gemini implements ---
# class CoopBase(DeclarativeBase):
#     """Abstract base with UUID PK and created_at."""
#     pass
