"""Seed script: creates demo users, dealers, makes, models, categories, locations, and sample cars."""
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# allow running as `python -m scripts.seed`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models import (
    User, UserRole, Role, Permission, RolePermission,
    Category, Make, Model, Location,
    Car, CarImage, CarFeature, Dealer, DealerEmployee,
    SiteSetting, PromotionPackage,
)
from app.core.config import settings


CATEGORIES = [
    {"name": "Sedan", "slug": "sedan", "icon": "car-sedan", "display_order": 1},
    {"name": "SUV", "slug": "suv", "icon": "car-suv", "display_order": 2},
    {"name": "Coupe", "slug": "coupe", "icon": "car-coupe", "display_order": 3},
    {"name": "Hatchback", "slug": "hatchback", "icon": "car-hatch", "display_order": 4},
    {"name": "Wagon", "slug": "wagon", "icon": "car-wagon", "display_order": 5},
    {"name": "Pickup", "slug": "pickup", "icon": "car-pickup", "display_order": 6},
    {"name": "Van", "slug": "van", "icon": "car-van", "display_order": 7},
    {"name": "Motorcycle", "slug": "motorcycle", "icon": "moto", "display_order": 8},
    {"name": "Truck", "slug": "truck", "icon": "truck", "display_order": 9},
    {"name": "Electric", "slug": "electric", "icon": "car-electric", "display_order": 10},
    {"name": "Convertible", "slug": "convertible", "icon": "car-convertible", "display_order": 11},
    {"name": "Crossover", "slug": "crossover", "icon": "car-crossover", "display_order": 12},
]

MAKES_MODELS = {
    "BMW": ["3 Series", "5 Series", "7 Series", "X3", "X5", "X7", "M3", "M5", "i4", "iX"],
    "Mercedes-Benz": ["C-Class", "E-Class", "S-Class", "GLA", "GLC", "GLE", "GLS", "AMG GT", "EQS", "EQC"],
    "Toyota": ["Corolla", "Camry", "RAV4", "Land Cruiser", "Hilux", "Yaris", "Supra", "Prius", "Highlander"],
    "Lexus": ["ES", "RX", "NX", "LX", "IS", "UX", "GX"],
    "Audi": ["A3", "A4", "A6", "A8", "Q3", "Q5", "Q7", "Q8", "RS6", "e-tron"],
    "Porsche": ["911", "Cayenne", "Macan", "Panamera", "Taycan", "718 Cayman", "718 Boxster"],
    "Tesla": ["Model 3", "Model S", "Model X", "Model Y", "Cybertruck"],
    "Ford": ["F-150", "Mustang", "Explorer", "Escape", "Bronco", "Focus", "Ranger"],
    "Hyundai": ["Elantra", "Sonata", "Tucson", "Santa Fe", "Palisade", "Kona", "Ioniq 5"],
    "Volkswagen": ["Golf", "Passat", "Tiguan", "Touareg", "ID.4", "Polo", "Arteon"],
    "Honda": ["Civic", "Accord", "CR-V", "Pilot", "HR-V", "Odyssey"],
    "Nissan": ["Altima", "Maxima", "Pathfinder", "Rogue", "GT-R", "Leaf", "370Z"],
    "Kia": ["Forte", "K5", "Sportage", "Sorento", "Telluride", "EV6", "Stinger"],
    "Subaru": ["Impreza", "Legacy", "Outback", "Forester", "Crosstrek", "WRX", "Ascent"],
    "Mazda": ["Mazda3", "Mazda6", "CX-3", "CX-5", "CX-9", "MX-5 Miata", "CX-50"],
}

LOCATIONS = [
    {"country": "United States", "city": "New York", "display_name": "New York, USA"},
    {"country": "United States", "city": "Los Angeles", "display_name": "Los Angeles, USA"},
    {"country": "United States", "city": "Chicago", "display_name": "Chicago, USA"},
    {"country": "United States", "city": "Houston", "display_name": "Houston, USA"},
    {"country": "United States", "city": "Miami", "display_name": "Miami, USA"},
    {"country": "Armenia", "city": "Yerevan", "display_name": "Yerevan, Armenia"},
    {"country": "Armenia", "city": "Gyumri", "display_name": "Gyumri, Armenia"},
    {"country": "Russia", "city": "Moscow", "display_name": "Moscow, Russia"},
    {"country": "Russia", "city": "Saint Petersburg", "display_name": "Saint Petersburg, Russia"},
    {"country": "Germany", "city": "Berlin", "display_name": "Berlin, Germany"},
    {"country": "Germany", "city": "Munich", "display_name": "Munich, Germany"},
    {"country": "United Kingdom", "city": "London", "display_name": "London, UK"},
    {"country": "France", "city": "Paris", "display_name": "Paris, France"},
    {"country": "Italy", "city": "Milan", "display_name": "Milan, Italy"},
    {"country": "UAE", "city": "Dubai", "display_name": "Dubai, UAE"},
]


SAMPLE_CARS = [
    {
        "make": "BMW", "model": "5 Series", "year": 2022, "price": 38500, "mileage": 42000,
        "fuel": "PETROL", "transmission": "AUTOMATIC", "body": "SEDAN", "drive": "AWD",
        "engine": "2.0L Turbo", "horsepower": 248, "color": "Black",
        "location": "Yerevan, Armenia", "currency": "USD",
    },
    {
        "make": "Mercedes-Benz", "model": "C-Class", "year": 2023, "price": 45000, "mileage": 18000,
        "fuel": "PETROL", "transmission": "AUTOMATIC", "body": "SEDAN", "drive": "RWD",
        "engine": "2.0L Turbo", "horsepower": 255, "color": "White",
        "location": "Moscow, Russia", "currency": "USD",
    },
    {
        "make": "Toyota", "model": "Camry", "year": 2021, "price": 22000, "mileage": 55000,
        "fuel": "HYBRID", "transmission": "AUTOMATIC", "body": "SEDAN", "drive": "FWD",
        "engine": "2.5L Hybrid", "horsepower": 208, "color": "Silver",
        "location": "Los Angeles, USA", "currency": "USD",
    },
    {
        "make": "Tesla", "model": "Model 3", "year": 2023, "price": 39900, "mileage": 12000,
        "fuel": "ELECTRIC", "transmission": "AUTOMATIC", "body": "SEDAN", "drive": "AWD",
        "engine": "Dual Motor", "horsepower": 434, "color": "Blue",
        "location": "San Francisco, USA", "currency": "USD",
    },
    {
        "make": "Porsche", "model": "911", "year": 2021, "price": 125000, "mileage": 15000,
        "fuel": "PETROL", "transmission": "AUTOMATIC", "body": "COUPE", "drive": "RWD",
        "engine": "3.0L Twin-Turbo", "horsepower": 379, "color": "Red",
        "location": "Dubai, UAE", "currency": "USD",
    },
    {
        "make": "Audi", "model": "Q5", "year": 2022, "price": 48000, "mileage": 32000,
        "fuel": "PETROL", "transmission": "AUTOMATIC", "body": "SUV", "drive": "AWD",
        "engine": "2.0L Turbo", "horsepower": 261, "color": "Gray",
        "location": "Berlin, Germany", "currency": "USD",
    },
    {
        "make": "Lexus", "model": "RX", "year": 2023, "price": 59000, "mileage": 8000,
        "fuel": "HYBRID", "transmission": "AUTOMATIC", "body": "SUV", "drive": "AWD",
        "engine": "2.5L Hybrid", "horsepower": 308, "color": "White",
        "location": "New York, USA", "currency": "USD",
    },
    {
        "make": "Ford", "model": "Mustang", "year": 2020, "price": 32000, "mileage": 48000,
        "fuel": "PETROL", "transmission": "MANUAL", "body": "COUPE", "drive": "RWD",
        "engine": "5.0L V8", "horsepower": 460, "color": "Yellow",
        "location": "Miami, USA", "currency": "USD",
    },
    {
        "make": "Volkswagen", "model": "Golf", "year": 2021, "price": 21000, "mileage": 60000,
        "fuel": "PETROL", "transmission": "MANUAL", "body": "HATCHBACK", "drive": "FWD",
        "engine": "1.4L Turbo", "horsepower": 147, "color": "Red",
        "location": "Munich, Germany", "currency": "USD",
    },
    {
        "make": "Hyundai", "model": "Tucson", "year": 2022, "price": 26500, "mileage": 38000,
        "fuel": "PETROL", "transmission": "AUTOMATIC", "body": "SUV", "drive": "FWD",
        "engine": "2.5L", "horsepower": 187, "color": "Green",
        "location": "Chicago, USA", "currency": "USD",
    },
    {
        "make": "Honda", "model": "Civic", "year": 2023, "price": 24500, "mileage": 14000,
        "fuel": "PETROL", "transmission": "AUTOMATIC", "body": "SEDAN", "drive": "FWD",
        "engine": "1.5L Turbo", "horsepower": 180, "color": "Black",
        "location": "Houston, USA", "currency": "USD",
    },
    {
        "make": "Kia", "model": "EV6", "year": 2023, "price": 48000, "mileage": 7000,
        "fuel": "ELECTRIC", "transmission": "AUTOMATIC", "body": "CROSSOVER", "drive": "AWD",
        "engine": "Dual Motor", "horsepower": 320, "color": "White",
        "location": "London, UK", "currency": "USD",
    },
    {
        "make": "Mazda", "model": "MX-5 Miata", "year": 2021, "price": 28000, "mileage": 22000,
        "fuel": "PETROL", "transmission": "MANUAL", "body": "CONVERTIBLE", "drive": "RWD",
        "engine": "2.0L", "horsepower": 181, "color": "Red",
        "location": "Milan, Italy", "currency": "USD",
    },
    {
        "make": "Nissan", "model": "GT-R", "year": 2020, "price": 95000, "mileage": 26000,
        "fuel": "PETROL", "transmission": "AUTOMATIC", "body": "COUPE", "drive": "AWD",
        "engine": "3.8L Twin-Turbo V6", "horsepower": 565, "color": "Gray",
        "location": "Dubai, UAE", "currency": "USD",
    },
    {
        "make": "Subaru", "model": "Outback", "year": 2022, "price": 32000, "mileage": 35000,
        "fuel": "PETROL", "transmission": "AUTOMATIC", "body": "WAGON", "drive": "AWD",
        "engine": "2.5L", "horsepower": 182, "color": "Blue",
        "location": "Saint Petersburg, Russia", "currency": "USD",
    },
    {
        "make": "Tesla", "model": "Model Y", "year": 2023, "price": 52000, "mileage": 9000,
        "fuel": "ELECTRIC", "transmission": "AUTOMATIC", "body": "SUV", "drive": "AWD",
        "engine": "Dual Motor", "horsepower": 384, "color": "Black",
        "location": "Paris, France", "currency": "USD",
    },
]


def seed():
    # Tables are created by Alembic migrations. We only seed data here.
    with SessionLocal() as db:
        # ---- categories ----
        for c in CATEGORIES:
            existing = db.execute(select(Category).where(Category.slug == c["slug"])).scalar_one_or_none()
            if not existing:
                db.add(Category(**c))
        db.flush()

        # ---- makes & models ----
        for make_name, models in MAKES_MODELS.items():
            make_slug = make_name.lower().replace(" ", "-").replace(".", "")
            make = db.execute(select(Make).where(Make.slug == make_slug)).scalar_one_or_none()
            if not make:
                make = Make(name=make_name, slug=make_slug, logo_url=None)
                db.add(make)
                db.flush()
            for m in models:
                m_slug = m.lower().replace(" ", "-").replace(".", "")
                existing = db.execute(
                    select(Model).where(Model.make_id == make.id, Model.slug == m_slug)
                ).scalar_one_or_none()
                if not existing:
                    db.add(Model(make_id=make.id, name=m, slug=m_slug, is_active=True))
        db.flush()

        # ---- locations ----
        for l in LOCATIONS:
            existing = db.execute(
                select(Location).where(Location.country == l["country"], Location.city == l["city"])
            ).scalar_one_or_none()
            if not existing:
                db.add(Location(**l))
        db.flush()

        # ---- roles (ensure default USER role) ----
        user_role = db.execute(select(Role).where(Role.slug == "USER")).scalar_one_or_none()
        dealer_role = db.execute(select(Role).where(Role.slug == "DEALER")).scalar_one_or_none()
        admin_role = db.execute(select(Role).where(Role.slug == "ADMIN")).scalar_one_or_none()

        # ---- demo users ----
        demo_users = [
            {"email": "user@blacksharkcars.local", "name": "Demo User", "password": "Demo!2025"},
            {"email": "seller@blacksharkcars.local", "name": "Demo Seller", "password": "Demo!2025"},
            {"email": "dealer@blacksharkcars.local", "name": "Premium Auto Group", "password": "Demo!2025"},
        ]
        user_records = {}
        for d in demo_users:
            u = db.execute(select(User).where(User.email == d["email"])).scalar_one_or_none()
            if not u:
                u = User(
                    email=d["email"], password_hash=hash_password(d["password"]),
                    full_name=d["name"], status="ACTIVE", is_email_verified=True,
                    city="Yerevan", country="Armenia",
                )
                db.add(u)
                db.flush()
                if user_role:
                    u.roles.append(UserRole(role=user_role))
            user_records[d["email"]] = u
        db.flush()

        # make seller the DEALER role
        seller = user_records["seller@blacksharkcars.local"]
        if dealer_role and not any(r.role.slug == "DEALER" for r in seller.roles):
            seller.roles.append(UserRole(role=dealer_role))

        # ---- dealer profile ----
        dealer_profile = db.execute(select(Dealer).where(Dealer.slug == "premium-auto-group")).scalar_one_or_none()
        if not dealer_profile:
            dealer_profile = Dealer(
                owner_id=seller.id,
                business_name="Premium Auto Group",
                slug="premium-auto-group",
                description="Authorized dealer specializing in luxury and performance vehicles.",
                city="Yerevan", country="Armenia",
                phone="+37411111111", email="contact@premiumauto.local",
                website="https://premiumauto.local",
                is_verified=True, is_active=True,
            )
            db.add(dealer_profile)
        db.flush()

        # ---- site settings ----
        for k, v in {
            "site_name": "BlackSharkCars",
            "site_tagline": "Find Your Next Car",
            "default_currency": "USD",
            "listings_auto_approve": "true",
            "contact_email": "hello@blacksharkcars.local",
            "footer_text": "© 2025 BlackSharkCars. All rights reserved.",
        }.items():
            s = db.get(SiteSetting, k)
            if not s:
                db.add(SiteSetting(key=k, value=v))
        db.flush()

        # ---- promotion packages ----
        for p in [
            {"name": "Featured", "slug": "featured", "promotion_type": "FEATURED", "price": 19.99, "duration_days": 14, "display_order": 1},
            {"name": "Top Listing", "slug": "top-listing", "promotion_type": "TOP_LISTING", "price": 29.99, "duration_days": 14, "display_order": 2},
            {"name": "Homepage Highlight", "slug": "homepage", "promotion_type": "HOMEPAGE", "price": 49.99, "duration_days": 7, "display_order": 3},
            {"name": "Highlighted", "slug": "highlighted", "promotion_type": "HIGHLIGHTED", "price": 9.99, "duration_days": 7, "display_order": 4},
            {"name": "Dealer Promotion", "slug": "dealer-promotion", "promotion_type": "DEALER_PROMOTION", "price": 99.99, "duration_days": 30, "display_order": 5},
        ]:
            existing = db.execute(select(PromotionPackage).where(PromotionPackage.slug == p["slug"])).scalar_one_or_none()
            if not existing:
                db.add(PromotionPackage(**p, currency="USD", max_active_per_user=10, is_active=True))
        db.flush()

        # ---- sample cars ----
        if db.execute(select(Car).limit(1)).scalar_one_or_none() is None:
            cat_by_slug = {c.slug: c for c in db.execute(select(Category)).scalars().all()}
            make_by_name = {m.name: m for m in db.execute(select(Make)).scalars().all()}
            loc_by_display = {l.display_name: l for l in db.execute(select(Location)).scalars().all()}

            for i, s in enumerate(SAMPLE_CARS):
                mk = make_by_name[s["make"]]
                mdl = db.execute(select(Model).where(Model.make_id == mk.id, Model.name == s["model"])).scalar_one()
                cat = cat_by_slug.get(s["body"].lower())
                loc = loc_by_display.get(s["location"])
                if not loc:
                    country, city = s["location"].split(", ", 1)
                    loc = Location(country=country, city=city, display_name=s["location"])
                    db.add(loc)
                    db.flush()
                    loc_by_display[s["location"]] = loc

                car = Car(
                    seller_id=seller.id if i % 2 == 0 else user_records["user@blacksharkcars.local"].id,
                    dealer_id=dealer_profile.id if i % 2 == 0 else None,
                    make_id=mk.id, model_id=mdl.id, category_id=cat.id if cat else None,
                    location_id=loc.id if loc else None,
                    year=s["year"], price=s["price"], currency=s["currency"],
                    mileage=s["mileage"], body_type=s["body"], fuel_type=s["fuel"],
                    transmission=s["transmission"], drive_type=s["drive"],
                    engine=s["engine"], horsepower=s["horsepower"],
                    exterior_color=s["color"], interior_color="Black",
                    description=f"Beautiful {s['year']} {s['make']} {s['model']} in excellent condition. "
                                f"Well maintained, full service history, clean title.",
                    condition="USED",
                    status="ACTIVE", is_featured=(i < 4), is_promoted=(i % 3 == 0),
                    views_count=150 + i * 37, favorites_count=i * 2,
                    published_at=datetime.now(timezone.utc) - timedelta(days=i),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60),
                    doors=4, seats=5,
                )
                db.add(car)
                db.flush()

                # Synthetic placeholder image (no real binary in repo)
                db.add(CarImage(
                    car_id=car.id,
                    storage_key=f"sample/{car.id}/1.jpg",
                    url=f"https://placehold.co/1200x800/050505/FFFFFF?text={s['make']}+{s['model']}",
                    thumbnail_url=f"https://placehold.co/400x300/050505/FFFFFF?text={s['make']}+{s['model']}",
                    display_order=0, is_main=True,
                    content_type="image/jpeg",
                ))

                for f_name in ["Bluetooth", "Backup Camera", "Cruise Control"]:
                    db.add(CarFeature(car_id=car.id, name=f_name))

        db.commit()
        print("Seed complete.")
        print(f"  Super Admin: {settings.SUPER_ADMIN_EMAIL} / {settings.SUPER_ADMIN_PASSWORD}")
        print(f"  Demo user:   user@blacksharkcars.local / Demo!2025")
        print(f"  Demo dealer: dealer@blacksharkcars.local / Demo!2025")


if __name__ == "__main__":
    seed()