/**
 * Authentication Context Provider.
 *
 * Responsibility:
 *   - Store current user and JWT token in React state
 *   - Provide login/logout functions to child components
 *   - Expose user role for conditional UI rendering
 *   - Persist token across page refreshes (httpOnly cookie or in-memory)
 *
 * Exposes:
 *   - user: User | null
 *   - token: string | null
 *   - isAuthenticated: boolean
 *   - login(username, password): Promise<void>
 *   - logout(): void
 *   - hasRole(...roles: UserRole[]): boolean
 *
 * TODO (Gemini): Implement AuthProvider and useAuth hook
 */

// export const AuthContext = createContext<AuthContextType>(...);
// export const AuthProvider: React.FC = ({ children }) => { ... };
// export const useAuth = () => useContext(AuthContext);
