/**
 * Core TypeScript Type Definitions.
 *
 * These types mirror the backend Pydantic schemas.
 * They are the SINGLE SOURCE OF TRUTH for frontend type safety.
 *
 * TODO (Gemini): Define all interfaces matching backend schemas:
 *
 * Pagination:
 *   - PaginatedResult<T> { items: T[], total, page, per_page, pages }
 *
 * Auth:
 *   - LoginRequest, LoginResponse, User
 *
 * Members:
 *   - MemberSummary, MemberDetail, MemberCreate, MemberUpdate, MemberExit
 *
 * Finance:
 *   - ContributionCreate, ContributionResponse
 *   - WithdrawalCreate, WithdrawalResponse
 *   - TransactionResponse
 *   - FundResponse, FundTransferCreate
 *
 * Property:
 *   - ProjectResponse, PropertyResponse, RentalUnitResponse, RentalIncomeCreate
 *
 * Expense:
 *   - ExpenseCreate, ExpenseResponse
 *
 * Reports:
 *   - MemberBalanceReport, ContributionSummaryReport, FundSummaryReport
 *   - MemberStatement, DashboardMetrics
 *
 * Enums (as string union types):
 *   - MemberStatus, TransactionType, FundType, ContributionStatus
 *   - WithdrawalStatus, WithdrawalType, ExpenseCategory, ProjectStatus, UserRole
 */

// Example pattern:
// export interface MemberSummary {
//   id: string;
//   member_number: string;
//   full_name: string;
//   status: MemberStatus;
//   accumulated_balance: string;  // decimal as string
// }

// export type MemberStatus = 'ACTIVE' | 'EXITED' | 'SUSPENDED';
