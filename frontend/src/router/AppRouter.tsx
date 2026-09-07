import React from "react";
import { Route, Routes } from "react-router-dom";
import { PublicLayout } from "@/layouts/PublicLayout";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { AdminLayout } from "@/layouts/AdminLayout";
import { SuperAdminLayout } from "@/layouts/SuperAdminLayout";
import { ProtectedRoute, AdminRoute, SuperAdminRoute } from "./ProtectedRoute";

import { HomePage } from "@/pages/HomePage";
import { SearchPage } from "@/pages/SearchPage";
import { CarDetailPage } from "@/pages/CarDetailPage";
import { DealersPage } from "@/pages/DealersPage";
import { DealerDetailPage } from "@/pages/DealerDetailPage";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage";
import { CreateListingPage } from "@/pages/CreateListingPage";
import { EditListingPage } from "@/pages/EditListingPage";

import { DashboardOverviewPage } from "@/pages/DashboardOverviewPage";
import { DashboardListingsPage } from "@/pages/DashboardListingsPage";
import { DashboardFavoritesPage } from "@/pages/DashboardFavoritesPage";
import { DashboardMessagesPage } from "@/pages/DashboardMessagesPage";
import { DashboardNotificationsPage } from "@/pages/DashboardNotificationsPage";
import { DashboardProfilePage } from "@/pages/DashboardProfilePage";
import { DashboardSettingsPage } from "@/pages/DashboardSettingsPage";

import { AdminDashboardPage } from "@/pages/admin/AdminDashboardPage";
import { AdminListingsPage } from "@/pages/admin/AdminListingsPage";
import { AdminUsersPage } from "@/pages/admin/AdminUsersPage";
import { AdminReportsPage } from "@/pages/admin/AdminReportsPage";

import { SuperAdminDashboardPage } from "@/pages/superadmin/SuperAdminDashboardPage";
import { SuperAdminAdminsPage } from "@/pages/superadmin/SuperAdminAdminsPage";
import { SuperAdminRolesPage } from "@/pages/superadmin/SuperAdminRolesPage";
import { SuperAdminAuditLogsPage } from "@/pages/superadmin/SuperAdminAuditLogsPage";
import { SuperAdminCategoriesPage } from "@/pages/superadmin/SuperAdminCategoriesPage";
import { SuperAdminMakesPage } from "@/pages/superadmin/SuperAdminMakesPage";
import { SuperAdminLocationsPage } from "@/pages/superadmin/SuperAdminLocationsPage";
import { SuperAdminPromotionsPage } from "@/pages/superadmin/SuperAdminPromotionsPage";
import { SuperAdminSettingsPage } from "@/pages/superadmin/SuperAdminSettingsPage";

export const AppRouter: React.FC = () => {
  return (
    <Routes>
      {/* Public */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/cars" element={<SearchPage />} />
        <Route path="/cars/:id" element={<CarDetailPage />} />
        <Route path="/dealers" element={<DealersPage />} />
        <Route path="/dealers/:id" element={<DealerDetailPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />

        <Route path="/sell" element={<ProtectedRoute><CreateListingPage /></ProtectedRoute>} />
      </Route>

      {/* Dashboard */}
      <Route path="/dashboard" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
        <Route index element={<DashboardOverviewPage />} />
        <Route path="listings" element={<DashboardListingsPage />} />
        <Route path="listings/new" element={<CreateListingPage />} />
        <Route path="listings/:id/edit" element={<EditListingPage />} />
        <Route path="favorites" element={<DashboardFavoritesPage />} />
        <Route path="messages" element={<DashboardMessagesPage />} />
        <Route path="notifications" element={<DashboardNotificationsPage />} />
        <Route path="profile" element={<DashboardProfilePage />} />
        <Route path="settings" element={<DashboardSettingsPage />} />
      </Route>

      {/* Admin */}
      <Route path="/admin" element={<AdminRoute><AdminLayout /></AdminRoute>}>
        <Route index element={<AdminDashboardPage />} />
        <Route path="listings" element={<AdminListingsPage />} />
        <Route path="users" element={<AdminUsersPage />} />
        <Route path="reports" element={<AdminReportsPage />} />
      </Route>

      {/* Super Admin */}
      <Route path="/super-admin" element={<SuperAdminRoute><SuperAdminLayout /></SuperAdminRoute>}>
        <Route index element={<SuperAdminDashboardPage />} />
        <Route path="admins" element={<SuperAdminAdminsPage />} />
        <Route path="roles" element={<SuperAdminRolesPage />} />
        <Route path="audit-logs" element={<SuperAdminAuditLogsPage />} />
        <Route path="categories" element={<SuperAdminCategoriesPage />} />
        <Route path="makes" element={<SuperAdminMakesPage />} />
        <Route path="locations" element={<SuperAdminLocationsPage />} />
        <Route path="promotions" element={<SuperAdminPromotionsPage />} />
        <Route path="settings" element={<SuperAdminSettingsPage />} />
        <Route path="users" element={<AdminUsersPage />} />
      </Route>

      <Route path="*" element={<div style={{ padding: 80, textAlign: "center" }}><h1>404</h1><p>Page not found</p></div>} />
    </Routes>
  );
};