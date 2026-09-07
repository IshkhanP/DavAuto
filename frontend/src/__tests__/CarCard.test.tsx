import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { CarCard } from "@/components/CarCard";

vi.mock("@/context/AuthContext", () => ({
  useAuth: () => ({ user: null }),
}));

describe("CarCard", () => {
  const mockCar: any = {
    id: "abc",
    make: "BMW",
    model: "5 Series",
    year: 2022,
    price: 38000,
    currency: "USD",
    mileage: 42000,
    fuel_type: "PETROL",
    transmission: "AUTOMATIC",
    city: "Yerevan",
    country: "Armenia",
    is_featured: true,
    is_promoted: false,
    main_image: "https://example.com/x.jpg",
    published_at: new Date().toISOString(),
    views_count: 0,
    favorites_count: 0,
    status: "ACTIVE",
    seller_type: "USER",
  };

  it("renders make, model and price", () => {
    render(
      <MemoryRouter>
        <CarCard car={mockCar} />
      </MemoryRouter>
    );
    expect(screen.getByText(/BMW/i)).toBeTruthy();
    expect(screen.getByText(/5 Series/i)).toBeTruthy();
    expect(screen.getByText(/38,000/)).toBeTruthy();
  });

  it("shows featured badge when is_featured is true", () => {
    render(
      <MemoryRouter>
        <CarCard car={mockCar} />
      </MemoryRouter>
    );
    expect(screen.getByText(/Featured/i)).toBeTruthy();
  });
});