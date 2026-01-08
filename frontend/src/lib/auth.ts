/**
 * Fake Authentication System for MVP
 * TODO: Replace with real auth (Supabase Auth) later
 */

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
}

// IMPORTANT: This ID must match the user in Supabase database
// and the mock user ID in backend/core/auth.py
const FAKE_USER: User = {
  id: "0495dca6-fd8a-471a-9a82-0ed3eb2b3b83",  // Real Supabase user ID
  email: "test@notiq.app",
  name: "Demo User",
  avatar: "👤"
};

const AUTH_STORAGE_KEY = "notiq_auth_user";

export const authService = {
  /**
   * Fake login - just stores user in localStorage
   */
  login(): User {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(FAKE_USER));
    return FAKE_USER;
  },

  /**
   * Continue as guest (same as login for now)
   */
  loginAsGuest(): User {
    const guestUser = { ...FAKE_USER, name: "Guest User" };
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(guestUser));
    return guestUser;
  },

  /**
   * Logout
   */
  logout(): void {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  },

  /**
   * Get current user
   */
  getCurrentUser(): User | null {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!stored) return null;

    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  },

  /**
   * Check if user is logged in
   */
  isAuthenticated(): boolean {
    return this.getCurrentUser() !== null;
  }
};
