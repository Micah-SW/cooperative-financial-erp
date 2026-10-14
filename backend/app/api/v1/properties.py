"""
Properties, Rental Units, and Rental Income API Router.

Endpoints:
    GET    /properties                   — List properties (ALL roles)
    GET    /properties/{id}              — Property detail (ALL roles)
    POST   /properties                   — Create property (ADMIN, TREASURER)
    PATCH  /properties/{id}              — Update property (ADMIN, TREASURER)
    GET    /properties/{pid}/units       — List units (ALL roles)
    POST   /properties/{pid}/units       — Create unit (ADMIN, TREASURER)
    GET    /units/{id}                   — Unit detail (ALL roles)
    PATCH  /units/{id}                   — Update unit (ADMIN, TREASURER)
    GET    /rental-income                — List rental income (ALL roles)
    POST   /rental-income                — Record rental income (ADMIN, TREASURER)

See: api_contract.md → Properties, Rental Units, Rental Income
Depends: PropertyService
"""

# router = APIRouter()
# TODO (Gemini): Implement endpoints
