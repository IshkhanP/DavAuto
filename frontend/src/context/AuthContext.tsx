// Auth context — derives roles / permissions from server (never trusts client claims).
import { createContext, useCallback, useContext, useEffect, useMemo, useState, ReactNode } from "react";
import { authService } from "@/services";
import { tokenStore } from "@/services/api";
import type { UserPrivate } from "@/types";

interface AuthContextValue {
  user: UserPrivate | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<UserPrivate>;
  register: (payload: { email: string; password: string; full_name: string; phone?: string }) => Promise<UserPrivate>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  hasRole: (...slugs: string[]) => boolean;
  hasPermission: (code: string) => boolean;
  hasAnyPermission: (...codes: string[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPrivate | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    if (!tokenStore.getAccess()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await authService.me();
      setUser(me);
    } catch {
      tokenStore.clear();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    await authService.login(email, password);
    const me = await authService.me();
    setUser(me);
    return me;
  }, []);

  const register = useCallback(async (payload: { email: string; password: string; full_name: string; phone?: string }) => {
    const u = await authService.register(payload);
    // auto-login
    await authService.login(payload.email, payload.password);
    const me = await authService.me();
    setUser(me);
    return u;
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  const hasRole = useCallback((...slugs: string[]) => {
    if (!user) return false;
    return user.roles.some((r) => slugs.includes(r));
  }, [user]);

  const hasPermission = useCallback((code: string) => {
    if (!user) return false;
    return user.permissions.includes(code);
  }, [user]);

  const hasAnyPermission = useCallback((...codes: string[]) => {
    if (!user) return false;
    return codes.some((c) => user.permissions.includes(c));
  }, [user]);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser, hasRole, hasPermission, hasAnyPermission }),
    [user, loading, login, register, logout, refreshUser, hasRole, hasPermission, hasAnyPermission]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}