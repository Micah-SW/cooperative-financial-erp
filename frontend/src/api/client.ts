/**
 * API Client — Centralized HTTP wrapper.
 *
 * Responsibility:
 *   - Configure base URL and default headers
 *   - Attach JWT token to all authenticated requests
 *   - Handle 401 responses (redirect to login)
 *   - Standardize error response handling
 *
 * Dependencies:
 *   - axios or fetch
 *   - AuthContext (for token retrieval)
 *
 * TODO (Gemini):
 *   - Create axios instance with baseURL = '/api/v1'
 *   - Add request interceptor to attach Authorization header
 *   - Add response interceptor for 401 handling
 *   - Export typed helper methods: get, post, patch, put, delete
 */

// export const apiClient = axios.create({ baseURL: '/api/v1' });
// TODO: Implement
