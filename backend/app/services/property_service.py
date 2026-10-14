"""
Property Service.

Module: Property
See: service_contracts.md → PropertyService
"""


class PropertyService:
    """
    Manages properties, rental units, and rental income.

    Responsibilities:
        - CRUD for properties and rental units
        - Record rental income (creates CREDIT transaction on rental income fund)

    Must NOT:
        - Attribute rental income to individual members
        - Bypass TransactionService for financial operations
    """

    async def list_properties(self, db, *, project_id=None, page=1, per_page=25):
        """TODO (Gemini): Implement"""
        pass

    async def get_property(self, db, property_id):
        """TODO (Gemini): Implement"""
        pass

    async def create_property(self, db, data, user_id):
        """TODO (Gemini): Implement"""
        pass

    async def update_property(self, db, property_id, data, user_id):
        """TODO (Gemini): Implement"""
        pass

    async def list_units(self, db, property_id):
        """TODO (Gemini): Implement"""
        pass

    async def create_unit(self, db, property_id, data, user_id):
        """TODO (Gemini): Implement"""
        pass

    async def update_unit(self, db, unit_id, data, user_id):
        """TODO (Gemini): Implement"""
        pass

    async def record_rental_income(self, db, data, user_id):
        """
        ATOMIC: RentalIncome record + CREDIT transaction on rental income fund + audit.
        TODO (Gemini): Implement per service_contracts.md
        """
        pass
