// Shared types for the BlackSharkCars frontend.

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface UserPublic {
  id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  avatar_url?: string | null;
  city?: string | null;
  country?: string | null;
  status: string;
  is_email_verified: boolean;
  created_at: string;
}

export interface UserPrivate extends UserPublic {
  roles: string[];
  permissions: string[];
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  icon?: string | null;
  description?: string | null;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Make {
  id: string;
  name: string;
  slug: string;
  logo_url?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Model {
  id: string;
  make_id: string;
  name: string;
  slug: string;
  body_type?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Location {
  id: string;
  country: string;
  region?: string | null;
  city: string;
  district?: string | null;
  display_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CarImage {
  id: string;
  url: string;
  thumbnail_url?: string | null;
  display_order: number;
  is_main: boolean;
  width?: number | null;
  height?: number | null;
}

export interface CarVideo {
  id: string;
  url: string;
  thumbnail_url?: string | null;
  duration_seconds?: number | null;
}

export interface CarFeature {
  id: string;
  name: string;
  value?: string | null;
  category?: string | null;
}

export interface SellerSummary {
  id: string;
  full_name: string;
  avatar_url?: string | null;
  city?: string | null;
  country?: string | null;
  seller_type: "USER" | "DEALER";
}

export interface CarCard {
  id: string;
  make: string;
  model: string;
  year: number;
  price: number;
  currency: string;
  mileage: number;
  fuel_type?: string | null;
  transmission?: string | null;
  body_type?: string | null;
  city?: string | null;
  country?: string | null;
  status: string;
  is_featured: boolean;
  is_promoted: boolean;
  views_count: number;
  favorites_count: number;
  main_image?: string | null;
  published_at?: string | null;
  seller_type: "USER" | "DEALER";
}

export interface CarDetail extends Omit<CarCard, "make" | "model" | "main_image"> {
  make_id: string;
  model_id: string;
  make_name: string;
  model_name: string;
  category_id?: string | null;
  category_name?: string | null;
  vin?: string | null;
  drive_type?: string | null;
  engine?: string | null;
  engine_size?: number | null;
  horsepower?: number | null;
  exterior_color?: string | null;
  interior_color?: string | null;
  doors?: number | null;
  seats?: number | null;
  description?: string | null;
  condition: string;
  is_negotiable: boolean;
  published_at?: string | null;
  expires_at?: string | null;
  sold_at?: string | null;
  created_at: string;
  updated_at: string;
  images: CarImage[];
  videos: CarVideo[];
  features: CarFeature[];
  seller: SellerSummary;
  location_display?: string | null;
  // Contact preferences
  phone_country_code?: string | null;
  phone_number?: string | null;
  contact_methods: string[];
}

// Allowed values for CarDetail.contact_methods (and the create form)
export const CONTACT_METHODS = [
  "PHONE",
  "WHATSAPP",
  "VIBER",
  "TELEGRAM",
  "CHAT",
] as const;
export type ContactMethod = typeof CONTACT_METHODS[number];

export interface Dealer {
  id: string;
  owner_id: string;
  business_name: string;
  slug: string;
  description?: string | null;
  logo_url?: string | null;
  cover_url?: string | null;
  phone?: string | null;
  email?: string | null;
  website?: string | null;
  address?: string | null;
  city?: string | null;
  country?: string | null;
  working_hours?: string | null;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  body?: string | null;
  data?: Record<string, any> | null;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  body: string;
  is_read: boolean;
  is_system: boolean;
  created_at: string;
}

export interface Conversation {
  id: string;
  car_id?: string | null;
  subject?: string | null;
  last_message_at?: string | null;
  is_active: boolean;
  participants: Array<{
    user_id: string;
    full_name: string;
    avatar_url?: string | null;
    unread_count: number;
    last_read_at?: string | null;
  }>;
  last_message?: Message | null;
  unread_count: number;
  created_at: string;
}

export interface Report {
  id: string;
  reporter_id: string;
  car_id?: string | null;
  reported_user_id?: string | null;
  reason: string;
  description?: string | null;
  status: string;
  resolved_by_id?: string | null;
  resolution_notes?: string | null;
  resolved_at?: string | null;
  created_at: string;
}

export interface PromotionPackage {
  id: string;
  name: string;
  slug: string;
  promotion_type: string;
  description?: string | null;
  price: number;
  currency: string;
  duration_days: number;
  max_active_per_user: number;
  is_active: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface Permission {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  category: string;
}

export interface Role {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  is_system: boolean;
  is_default: boolean;
  permissions: Permission[];
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  user_id?: string | null;
  action: string;
  resource_type?: string | null;
  resource_id?: string | null;
  ip_address?: string | null;
  user_agent?: string | null;
  metadata_json?: Record<string, any> | null;
  created_at: string;
}

export interface DashboardStats {
  total_users: number;
  active_users: number;
  total_listings: number;
  active_listings: number;
  pending_listings: number;
  sold_listings: number;
  total_dealers: number;
  total_reports: number;
  pending_reports: number;
  total_messages: number;
  total_revenue: number;
  new_users_last_30d: number;
  new_listings_last_30d: number;
}

export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  status: string;
  is_email_verified: boolean;
  last_login_at?: string | null;
  last_login_ip?: string | null;
  roles: string[];
  created_at: string;
  cars_count?: number;
  is_super_admin?: boolean;
}

export interface SiteSetting {
  key: string;
  value?: string | null;
  description?: string | null;
  updated_at: string;
}

export interface SearchFilters {
  make?: string;
  make_id?: string;
  model?: string;
  model_id?: string;
  category_id?: string;
  body_type?: string;
  fuel_type?: string;
  transmission?: string;
  drive_type?: string;
  condition?: string;
  location_id?: string;
  city?: string;
  country?: string;
  seller_type?: string;
  min_price?: number;
  max_price?: number;
  min_year?: number;
  max_year?: number;
  min_mileage?: number;
  max_mileage?: number;
  color?: string;
  q?: string;
  is_featured?: boolean;
  sort?: string;
  page?: number;
  limit?: number;
}