# Admin Flowchart - PickleSphere

```mermaid
flowchart TD
    A((Start)) --> B[Admin Login]
    B --> C{Admin Role?}
    C -->|No| D[Access Denied]
    C -->|Yes| E[Admin Dashboard]

    E --> F{Choose Module}

    F -->|Users| G[User Management]
    G --> H{CRUD}
    H -->|Create| I[Create User/Staff/Admin]
    H -->|Edit| J[Edit Role/Profile]
    H -->|Delete| K[Deactivate User]
    I --> E
    J --> E
    K --> E

    F -->|Reservations| L[All Reservations]
    L --> M{Action}
    M -->|Create| N[Book for Any User]
    M -->|Edit| O[Modify Any Field]
    M -->|Delete| P[Force Delete]
    N --> E
    O --> E
    P --> E

    F -->|Payments| Q[All Payments]
    Q --> R{Action}
    R -->|Refund| S[Process Refund]
    R -->|Reports| T[Export CSV/PDF/Excel]
    S --> E
    T --> E

    F -->|Equipment| U[Equipment CRUD]
    U --> E

    F -->|Tournaments| V[Tournament Management]
    V --> W[Create/Edit/Delete]
    V --> X[Manage Bracket]
    V --> Y[Bulk Approve]
    W --> E
    X --> E
    Y --> E

    F -->|Content| Z[Content Management]
    Z --> AA[Homepage/Pricing/About/Contact]
    AA --> E

    F -->|Courts| AB[Court & Site CRUD]
    AB --> E

    F -->|System| AC[Activity Logs & Settings]
    AC --> E

    F -->|Logout| AD((End))
```

## Admin vs Staff vs User

| Feature | User | Staff | Admin |
|---------|------|-------|-------|
| **Reservations** | Own only | View/Approve all | Full CRUD |
| **Payments** | Own only | Verify only | + Refunds/Reports |
| **Users** | Self only | View only | Full CRUD |
| **Equipment** | Rent | Checkout/Checkin | Full CRUD |
| **Tournaments** | Register/Play | Approve players | Full management |
| **Content** | View | ❌ | Full CRUD |
| **Reports** | ❌ | Basic | Full + Export |
| **System** | ❌ | ❌ | Logs & Settings |
