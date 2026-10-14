"""
Property, RentalUnit, and RentalIncome Pydantic Schemas.

Module: Property
See: api_contract.md → Properties, Rental Units, Rental Income

TODO (Gemini):
    - PropertyCreate: project_id?, name, address?, property_type, notes?
    - PropertyUpdate: project_id?, name?, address?, property_type?, is_active?, notes?
    - PropertyResponse: all fields + unit_count, occupied_count

    - RentalUnitCreate: unit_identifier, tenant_name?, monthly_rent?, lease_start?, lease_end?
    - RentalUnitUpdate: unit_identifier?, tenant_name?, monthly_rent?,
                        lease_start?, lease_end?, is_occupied?, notes?
    - RentalUnitResponse: all fields

    - RentalIncomeCreate: rental_unit_id (UUID), amount (Decimal), income_date (date),
                          period_label (str), bank_reference?, notes?
    - RentalIncomeResponse: all fields + unit_identifier, property_name
"""

# class PropertyCreate(BaseModel): ...
# class RentalUnitCreate(BaseModel): ...
# class RentalIncomeCreate(BaseModel): ...
