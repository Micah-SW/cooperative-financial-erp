"""
SystemConfig ORM Model.

Entity: SystemConfig
Schema: coop.system_config
Module: Core

See: database_schema.md → coop.system_config
See: domain_model.md → SystemConfig

Business Rules:
    - Effective-dated: each record has effective_from and effective_to
    - Only one active record per key (effective_to IS NULL)
    - Changing a value closes the current record and creates a new one
    - Config keys: SHARE_VALUE, SHARES_PER_MEMBER, MEMBER_CONTRIBUTION_AMOUNT,
                   OPERATING_CONTRIBUTION_AMOUNT, COOPERATIVE_NAME, CURRENCY_CODE

TODO (Gemini):
    - Implement using SQLAlchemy 2.0 Mapped[] style
    - Inherit from CoopBase
    - Fields: id, config_key, config_value, value_type, description,
              effective_from, effective_to, created_at, created_by (FK→users)
    - Unique partial index: (config_key) WHERE effective_to IS NULL
"""

# class SystemConfig(CoopBase):
#     __tablename__ = "system_config"
#     __table_args__ = {"schema": "coop"}
#     ...
