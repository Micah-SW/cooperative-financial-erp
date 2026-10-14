"""
RentalUnit and RentalIncome ORM Models.

Entities: RentalUnit, RentalIncome
Schema: coop.rental_units, coop.rental_income
Module: Property

See: database_schema.md → coop.rental_units, coop.rental_income
See: domain_model.md → RentalUnit, RentalIncome

Business Rules:
    - RentalIncome recording creates CREDIT transaction on Rental Income Fund
    - Rental income belongs to the cooperative, NOT individual members
    - period_label format: "YYYY-MM"

TODO (Gemini):
    RentalUnit:
    - Fields: id, property_id (FK→properties), unit_identifier, tenant_name,
              monthly_rent, lease_start, lease_end, is_occupied, notes, created_at

    RentalIncome:
    - Fields: id, rental_unit_id (FK→rental_units), fund_id (FK→funds),
              amount, income_date, period_label, bank_reference, notes,
              created_at, created_by (FK→users)
    - CHECK: amount > 0
"""

# class RentalUnit(CoopBase):
#     __tablename__ = "rental_units"
#     __table_args__ = {"schema": "coop"}
#     ...

# class RentalIncome(CoopBase):
#     __tablename__ = "rental_income"
#     __table_args__ = {"schema": "coop"}
#     ...
