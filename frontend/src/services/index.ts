// Domain-specific API helpers.
import { api, tokenStore } from "./api";
import type {
  AuthTokens, CarCard, CarDetail, Category, Conversation, Dealer, Location,
  Make, Message, Model, Notification, PaginatedResponse, Report, Role,
  SearchFilters, UserPrivate, UserPublic, PromotionPackage, Permission,
  AdminUser, DashboardStats, AuditLog, SiteSetting, CarDailyView,
} from "@/types";

export const authService = {
  async register(payload: {
    email: string;
    password: string;
    full_name: string;
    phone?: string;
    city?: string;
    country?: string;
  }): Promise<UserPrivate> {
    const res = await api.post("/auth/register", payload);
    return res.data;
  },
  async login(email: string, password: string): Promise<AuthTokens> {
    const res = await api.post("/auth/login", { email, password });
    tokenStore.set(res.data.access_token, res.data.refresh_token);
    return res.data;
  },
  async me(): Promise<UserPrivate> {
    const res = await api.get("/auth/me");
    return res.data;
  },
  async updateMe(payload: Partial<UserPublic>): Promise<UserPrivate> {
    const res = await api.patch("/auth/me", payload);
    return res.data;
  },
  async logout(): Promise<void> {
    const refresh = tokenStore.getRefresh();
    try {
      if (refresh) await api.post("/auth/logout", { refresh_token: refresh });
    } catch {
      /* ignore */
    }
    tokenStore.clear();
  },
  async changePassword(current: string, next: string): Promise<void> {
    await api.post("/auth/change-password", { current_password: current, new_password: next });
  },
  async forgotPassword(email: string): Promise<void> {
    await api.post("/auth/forgot-password", { email });
  },
  async resetPassword(token: string, new_password: string): Promise<void> {
    await api.post("/auth/reset-password", { token, new_password });
  },
};

export const carsService = {
  async search(filters: SearchFilters): Promise<PaginatedResponse<CarCard>> {
    const cleaned: Record<string, any> = {};
    for (const [k, v] of Object.entries(filters)) {
      if (v !== undefined && v !== null && v !== "") cleaned[k] = v;
    }
    const res = await api.get("/cars", { params: cleaned });
    return res.data;
  },
  async featured(limit = 12): Promise<CarCard[]> {
    const res = await api.get("/cars/featured", { params: { limit } });
    return res.data;
  },
  async latest(limit = 12): Promise<CarCard[]> {
    const res = await api.get("/cars/latest", { params: { limit } });
    return res.data;
  },
  async similar(car_id: string, limit = 8): Promise<CarCard[]> {
    const res = await api.get(`/cars/similar/${car_id}`, { params: { limit } });
    return res.data;
  },
  async get(id: string): Promise<CarDetail> {
    const res = await api.get(`/cars/${id}`);
    return res.data;
  },
  async create(payload: Record<string, any>): Promise<CarDetail> {
    const res = await api.post("/cars", payload);
    return res.data;
  },
  async update(id: string, payload: Record<string, any>): Promise<CarDetail> {
    const res = await api.patch(`/cars/${id}`, payload);
    return res.data;
  },
  async setStatus(id: string, status: string): Promise<CarDetail> {
    const res = await api.post(`/cars/${id}/status`, { status });
    return res.data;
  },
  async duplicate(id: string): Promise<CarDetail> {
    const res = await api.post(`/cars/${id}/duplicate`);
    return res.data;
  },
  async remove(id: string): Promise<void> {
    await api.delete(`/cars/${id}`);
  },
  async mine(filters: { status?: string; page?: number; limit?: number } = {}): Promise<PaginatedResponse<CarCard>> {
    const res = await api.get("/cars/mine/all", { params: filters });
    return res.data;
  },
  /** Per-day view counts for a listing — powers the "views today / this
   * week" stats the seller sees on My Listings. Owner or admin only. */
  async dailyViews(carId: string, days = 14): Promise<CarDailyView[]> {
    const res = await api.get(`/cars/${carId}/views/daily`, { params: { days } });
    return res.data;
  },
};

export const favoritesService = {
  async toggle(carId: string): Promise<{ favorited: boolean; favorites_count: number }> {
    const existing = await api.get("/favorites", { params: { limit: 100 } });
    const found = (existing.data.items as CarCard[]).find((c) => c.id === carId);
    if (found) {
      const res = await api.delete(`/favorites/${carId}`);
      return res.data;
    }
    const res = await api.post(`/favorites/${carId}`);
    return res.data;
  },
  async add(carId: string) {
    const res = await api.post(`/favorites/${carId}`);
    return res.data;
  },
  async remove(carId: string) {
    const res = await api.delete(`/favorites/${carId}`);
    return res.data;
  },
  async list(page = 1, limit = 24): Promise<PaginatedResponse<CarCard>> {
    const res = await api.get("/favorites", { params: { page, limit } });
    return res.data;
  },
};

export const messagingService = {
  async list(): Promise<Conversation[]> {
    const res = await api.get("/conversations");
    return res.data;
  },
  async get(id: string): Promise<Conversation> {
    const res = await api.get(`/conversations/${id}`);
    return res.data;
  },
  async listMessages(id: string, page = 1, limit = 50): Promise<Message[]> {
    const res = await api.get(`/conversations/${id}/messages`, { params: { page, limit } });
    return res.data;
  },
  async sendMessage(id: string, body: string): Promise<Message> {
    const res = await api.post(`/conversations/${id}/messages`, { body });
    return res.data;
  },
  async createOrGet(payload: {
    car_id?: string;
    recipient_id: string;
    subject?: string;
    initial_message: string;
  }): Promise<Conversation> {
    const res = await api.post("/conversations", payload);
    return res.data;
  },
  async markRead(id: string): Promise<void> {
    await api.post(`/conversations/${id}/read`);
  },
};

export const notificationsService = {
  async list(page = 1, limit = 30): Promise<PaginatedResponse<Notification>> {
    const res = await api.get("/notifications", { params: { page, limit } });
    return res.data;
  },
  async unreadCount(): Promise<{ unread: number }> {
    const res = await api.get("/notifications/unread-count");
    return res.data;
  },
  async markRead(id: string): Promise<void> {
    await api.post(`/notifications/${id}/read`);
  },
  async markAllRead(): Promise<void> {
    await api.post("/notifications/read-all");
  },
};

export const catalogService = {
  async categories(): Promise<Category[]> {
    const res = await api.get("/catalog/categories");
    return res.data;
  },
  async makes(): Promise<Make[]> {
    const res = await api.get("/catalog/makes");
    return res.data;
  },
  async models(makeId: string): Promise<Model[]> {
    const res = await api.get(`/catalog/makes/${makeId}/models`);
    return res.data;
  },
  async locations(country?: string): Promise<Location[]> {
    const res = await api.get("/catalog/locations", { params: { country } });
    return res.data;
  },
  async countries(): Promise<string[]> {
    const res = await api.get("/catalog/locations/countries");
    return res.data;
  },
};

export const dealersService = {
  async list(): Promise<Dealer[]> {
    const res = await api.get("/dealers");
    return res.data;
  },
  async get(id: string): Promise<Dealer> {
    const res = await api.get(`/dealers/${id}`);
    return res.data;
  },
  async cars(id: string, page = 1, limit = 24): Promise<PaginatedResponse<CarCard>> {
    const res = await api.get(`/dealers/${id}/cars`, { params: { page, limit } });
    return res.data;
  },
  async create(payload: Record<string, any>): Promise<Dealer> {
    const res = await api.post("/dealers", payload);
    return res.data;
  },
  async update(id: string, payload: Record<string, any>): Promise<Dealer> {
    const res = await api.patch(`/dealers/${id}`, payload);
    return res.data;
  },
};

export const reportsService = {
  async create(payload: { car_id?: string; reported_user_id?: string; reason: string; description?: string }): Promise<Report> {
    const res = await api.post("/reports", payload);
    return res.data;
  },
};

export const uploadsService = {
  async uploadCarImage(carId: string, file: File): Promise<{ id: string; url: string }> {
    const fd = new FormData();
    fd.append("file", file);
    const res = await api.post(`/uploads/cars/${carId}/images`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },
  async deleteCarImage(imageId: string): Promise<void> {
    await api.delete(`/uploads/cars/images/${imageId}`);
  },
  async reorderImages(carId: string, imageIds: string[]): Promise<void> {
    await api.put(`/uploads/cars/${carId}/images/reorder`, { image_ids: imageIds });
  },
  async uploadAvatar(file: File): Promise<{ url: string }> {
    const fd = new FormData();
    fd.append("file", file);
    const res = await api.post(`/uploads/avatar`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },
  async setMainImage(carId: string, imageId: string): Promise<void> {
    await api.post(`/uploads/cars/${carId}/images/${imageId}/main`);
  },
};

// ---- Admin / Super-Admin services ----
export const adminService = {
  async stats(): Promise<DashboardStats> {
    const res = await api.get("/admin/stats");
    return res.data;
  },
  async listings(params: { status?: string; q?: string; page?: number; limit?: number } = {}): Promise<PaginatedResponse<any>> {
    const res = await api.get("/admin/listings", { params });
    return res.data;
  },
  async approve(id: string): Promise<any> {
    const res = await api.patch(`/admin/listings/${id}/approve`);
    return res.data;
  },
  async reject(id: string, reason?: string): Promise<any> {
    const res = await api.patch(`/admin/listings/${id}/reject`, { reason });
    return res.data;
  },
  async feature(id: string, is_featured = true): Promise<any> {
    const res = await api.patch(`/admin/listings/${id}/feature`, { is_featured });
    return res.data;
  },
  async bulkAction(ids: string[], action: string): Promise<{ affected: number }> {
    const res = await api.post("/admin/listings/bulk-action", { ids, action });
    return res.data;
  },
  async reports(params: { status?: string; page?: number; limit?: number } = {}): Promise<PaginatedResponse<Report>> {
    const res = await api.get("/admin/reports", { params });
    return res.data;
  },
  async resolveReport(id: string, payload: { status: string; resolution_notes?: string; action?: string }): Promise<void> {
    await api.post(`/admin/reports/${id}/resolve`, payload);
  },
  async users(params: { q?: string; status?: string; page?: number; limit?: number } = {}): Promise<PaginatedResponse<AdminUser>> {
    const res = await api.get("/admin/users", { params });
    return res.data;
  },
  async updateUser(id: string, payload: Record<string, any>): Promise<AdminUser> {
    const res = await api.patch(`/admin/users/${id}`, payload);
    return res.data;
  },
};

export const superAdminService = {
  async admins(params: { page?: number; limit?: number } = {}): Promise<PaginatedResponse<AdminUser>> {
    const res = await api.get("/super-admin/admins", { params });
    return res.data;
  },
  async createAdmin(payload: { email: string; password: string; full_name: string; role_id: string; phone?: string }): Promise<AdminUser> {
    const res = await api.post("/super-admin/admins", payload);
    return res.data;
  },
  async updateAdmin(id: string, payload: Record<string, any>): Promise<AdminUser> {
    const res = await api.patch(`/super-admin/admins/${id}`, payload);
    return res.data;
  },
  async deleteAdmin(id: string): Promise<void> {
    await api.delete(`/super-admin/admins/${id}`);
  },
  async permissions(): Promise<Permission[]> {
    const res = await api.get("/super-admin/permissions");
    return res.data;
  },
  async roles(params: { page?: number; limit?: number } = {}): Promise<PaginatedResponse<Role>> {
    const res = await api.get("/super-admin/roles", { params });
    return res.data;
  },
  async createRole(payload: { name: string; slug: string; description?: string; permission_ids: string[] }): Promise<Role> {
    const res = await api.post("/super-admin/roles", payload);
    return res.data;
  },
  async updateRole(id: string, payload: Record<string, any>): Promise<Role> {
    const res = await api.patch(`/super-admin/roles/${id}`, payload);
    return res.data;
  },
  async deleteRole(id: string): Promise<void> {
    await api.delete(`/super-admin/roles/${id}`);
  },
  async settings(): Promise<SiteSetting[]> {
    const res = await api.get("/super-admin/settings");
    return res.data;
  },
  async updateSetting(key: string, payload: { value?: string; description?: string }): Promise<SiteSetting> {
    const res = await api.put(`/super-admin/settings/${key}`, payload);
    return res.data;
  },
  async auditLogs(params: { user_id?: string; action?: string; page?: number; limit?: number } = {}): Promise<PaginatedResponse<AuditLog>> {
    const res = await api.get("/super-admin/audit-logs", { params });
    return res.data;
  },
  async categories(): Promise<Category[]> {
    const res = await api.get("/super-admin/categories");
    return res.data;
  },
  async createCategory(payload: Record<string, any>): Promise<Category> {
    const res = await api.post("/super-admin/categories", payload);
    return res.data;
  },
  async makes(): Promise<Make[]> {
    const res = await api.get("/super-admin/makes");
    return res.data;
  },
  async createMake(payload: Record<string, any>): Promise<Make> {
    const res = await api.post("/super-admin/makes", payload);
    return res.data;
  },
  async locations(): Promise<Location[]> {
    const res = await api.get("/super-admin/locations");
    return res.data;
  },
  async createLocation(payload: Record<string, any>): Promise<Location> {
    const res = await api.post("/super-admin/locations", payload);
    return res.data;
  },
  async promotionPackages(): Promise<PromotionPackage[]> {
    const res = await api.get("/super-admin/promotion-packages");
    return res.data;
  },
  async createPromotionPackage(payload: Record<string, any>): Promise<PromotionPackage> {
    const res = await api.post("/super-admin/promotion-packages", payload);
    return res.data;
  },
  async updatePromotionPackage(id: string, payload: Record<string, any>): Promise<PromotionPackage> {
    const res = await api.patch(`/super-admin/promotion-packages/${id}`, payload);
    return res.data;
  },
  async deletePromotionPackage(id: string): Promise<void> {
    await api.delete(`/super-admin/promotion-packages/${id}`);
  },
};
