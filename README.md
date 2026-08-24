# 🛒 FoodBasket – Responsive Grocery E-Commerce & Local Delivery Store

A production-ready, highly styled Django + Bootstrap grocery store application featuring role-based access control (RBAC), multi-portal management, real-time location-based product filtering, mock payment gateway processing, and containerized Docker environments.

---

## 🚀 Live Application Link
Explore the live deployed store here:  
👉 **[https://foodgrocery-store.onrender.com/](https://foodgrocery-store.onrender.com/)**

---

## ✨ Features

### 🔒 1. Authentication & Security
- Role-based profiles: **Customer**, **Approved Vendor**, and **Super Admin**.
- Passwordless OTP/Email verification for customers.
- Custom route guards (`@vendor_required`, `@superadmin_required`) preventing unauthorized portal navigation.
- Lightweight, zero-dependency signed JWT APIs under `/api/`.

### 🏢 2. Multi-Portal Access
- **Customer UI**: Public storefront to browse, search, toggle wishlists, add items to cart, checkout, view order tracking, and print receipts.
- **Vendor Portal (`/vendor/`)**: Approved shops can manage their inventory catalogs (CRUD products), track sales metrics, and update delivery statuses.
- **Admin Dashboard (`/superadmin/`)**: Superadmins approve/reject shop applications, assign active delivery zones/pincodes to vendors, and monitor total transaction volumes.

### 📍 3. Location-Based Area Shop Filtering
- Redirection immediately after customer login to select active delivery zones.
- Optional HTML5 Geolocation detection or manual pincode input mapping to serviced areas.
- Automated homepage/listing filters showing only fresh foods and items provided by vendors operating within the customer's active delivery pincode.

### 🛒 4. Checkout & Order Management
- Simulation of secure contact endpoints with Stripe/Razorpay payment servers for online payments.
- Printable, custom styled customer invoice layouts (`window.print()`).
- Automated low-stock email warning triggers notifying vendors and superadmins when item inventories drop below configured thresholds.

---

## 🛠️ Local Development Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Apply Migrations & Seed Demo Data
```bash
python manage.py migrate --noinput
python manage.py seed_data
```
*Note: Seeding creates an admin account (`admin` / `adminpass`) and three local Madurai-based vendor accounts (`vendorpass`).*

### 3. Run Development Server
```bash
python manage.py runserver
```
Visit the store at: `http://127.0.0.1:8000/`

### 4. Run Automated Unit Tests
```bash
python manage.py test
```

---

## 🐳 Containerization & Deployment

- **Docker Compose**: Orchestrates Django web containers and a PostgreSQL database locally.
  ```bash
  docker-compose up --build
  ```
- **WhiteNoise Integration**: Handles compression and static asset delivery automatically during production builds.
- **Production Logging**: Equipped with rotating file logging (5MB capacity limit, 5 backups history) and Sentry hooks.
