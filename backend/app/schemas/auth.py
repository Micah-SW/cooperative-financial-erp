"""
Authentication Pydantic Schemas.

Module: Core
See: api_contract.md → Authentication

TODO (Gemini):
    - LoginRequest: username (str), password (str)
    - LoginResponse: access_token (str), token_type (str), user (UserResponse)
    - TokenPayload: sub (str/UUID), username (str), role (UserRole), exp (int)
    - ChangePasswordRequest: current_password (str), new_password (str, min_length=8)
"""

# class LoginRequest(BaseModel): ...
# class LoginResponse(BaseModel): ...
# class TokenPayload(BaseModel): ...
# class ChangePasswordRequest(BaseModel): ...
