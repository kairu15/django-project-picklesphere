# PickleSphere - System Overview

---

## 1. Purpose of the System

**PickleSphere** is a comprehensive web-based Court Reservation and Tournament Management System specifically designed for pickleball facilities. The system aims to:

- **Automate Court Bookings** - Enable users to view court availability and make reservations online, reducing manual coordination and eliminating double-bookings.

- **Streamline Tournament Operations** - Provide end-to-end tournament management including player registration, bracket generation, match scheduling, and leaderboard tracking.

- **Manage Equipment Rentals** - Track inventory and facilitate equipment rentals (paddles, balls, nets, shoes) with integrated payment processing.

- **Process Payments Securely** - Support multiple payment methods (GCash, Cash, Credit/Debit Card) with verification workflows for cashless transactions.

- **Enhance User Experience** - Offer role-based dashboards (Admin, Staff, Player) with real-time notifications, activity logging, and content management for marketing pages.

- **Enable Data-Driven Decisions** - Generate reports on revenue, court utilization, tournament statistics, and user activity for facility management.

---

## 2. Target Users

| User Role | Description | Key Functions |
|-----------|-------------|---------------|
| **Administrator** | System owners/managers with full access | User management, content editing, financial reports, system configuration, refund approvals |
| **Staff** | Facility employees with operational access | Reservation approvals, payment verification, equipment check-in/out, tournament match management |
| **Player/User** | Registered members and guests | Court reservations, tournament registration, equipment rental, payment processing, viewing match schedules |
| **Guest Visitor** | Non-registered public users | View court information, browse tournaments, read about/pricing content, contact facility |

---

## 3. System Flowchart

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    PICKLESPHERE SYSTEM                                      │
│                         Court Reservation & Tournament Management                          │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

                                        ╔═══════════╗
                                        ║   START   ║
                                        ║  (Oval)   ║
                                        ╚═════╤═════╝
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     ENTRY POINT                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │  Landing Page   │    │     Login       │    │   Register      │    │  Public Pages   │  │
│  │   (Process)     │───▶│   (Process)     │───▶│   (Process)     │    │  (About/Contact)│  │
│  └─────────────────┘    └────────┬────────┘    └─────────────────┘    └─────────────────┘  │
└───────────────────────────────────┼───────────────────────────────────────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   AUTHENTICATION    │
                         │     (Diamond)       │
                         │  Valid Credentials? │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │ No            │ Yes           │
                    ▼               ▼               │
            ┌──────────────┐  ┌──────────────┐      │
            │ Return to    │  │  Role Check  │◀─────┘
            │ Login        │  │  (Diamond)   │
            │ (Process)    │  └──────┬───────┘
            └──────────────┘         │
                                     ▼
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   ADMIN ROLE    │    │   STAFF ROLE    │    │   PLAYER ROLE   │
    │   (Cylinder)    │    │   (Cylinder)    │    │   (Cylinder)    │
    └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
             │                      │                      │
             ▼                      ▼                      ▼
┌────────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐
│   ADMIN DASHBOARD      │ │   STAFF DASHBOARD      │ │   PLAYER DASHBOARD     │
│   (Document)           │ │   (Document)           │ │   (Document)           │
├────────────────────────┤ ├────────────────────────┤ ├────────────────────────┤
│ ┌──────────────────┐ │ │ ┌──────────────────┐ │ │ ┌──────────────────┐ │
│ │ User Management  │ │ │ │ Reservation Mgmt │ │ │ │ Browse Courts    │ │
│ │ (Process)        │ │ │ │ (Process)        │ │ │ │ (Process)        │ │
│ └────────┬─────────┘ │ │ └────────┬─────────┘ │ │ └────────┬─────────┘ │
│          │          │ │          │          │ │          │             │
│ ┌────────▼─────────┐ │ │ ┌────────▼─────────┐ │ │ ┌────────▼─────────┐   │
│ │ Database Storage │ │ │ │ Payment Verify   │ │ │ │ Make Reservation │   │
│ │   (Cylinder)     │ │ │ │ (Process)        │ │ │ │ (Parallelogram)  │   │
│ └──────────────────┘ │ │ └────────┬─────────┘ │ │ └────────┬─────────┘   │
│                      │ │          │          │ │          │             │
│ ┌──────────────────┐ │ │ ┌────────▼─────────┐ │ │ ┌────────▼─────────┐   │
│ │ Content Mgmt     │ │ │ │ Equipment Check  │ │ │ │ Payment Process  │   │
│ │ (Process)        │ │ │ │ In/Out           │ │ │ │ (Diamond)        │   │
│ └────────┬─────────┘ │ │ │ (Parallelogram)  │ │ │ └────────┬─────────┘   │
│          │          │ │ └────────┬─────────┘ │ │          │             │
│ ┌────────▼─────────┐ │ │          │          │ │    ┌─────┴─────┐        │
│ │ Tournament Admin │ │ │ ┌────────▼─────────┐ │ │    │           │        │
│ │ (Process)        │ │ │ │ Tournament Match │ │ │    ▼           ▼        │
│ └────────┬─────────┘ │ │ │ Management       │ │ │  Paid        Pending    │
│          │          │ │ └────────┬─────────┘ │ │    │            │        │
│ ┌────────▼─────────┐ │ │          │          │ │    ▼            ▼        │
│ │ Financial Report │ │ │ ┌────────▼─────────┐ │ │ ┌──────────┐ ┌────────┐ │
│ │ (Document)       │ │ │ │ Database Storage │ │ │ │Confirmed │ │Notify  │ │
│ └────────┬─────────┘ │ │ │   (Cylinder)     │ │ │ │(Process) │ │Staff   │ │
│          │          │ │ └──────────────────┘ │ │ └────┬─────┘ └────────┘ │
│ ┌────────▼─────────┐ │ └──────────────────────┘ │      │               │
│ │ Database Storage │ │                          │ ┌────▼────┐            │
│ │   (Cylinder)     │ │                          │ │Equipment│            │
│ └──────────────────┘ │                          │ │  Rent   │            │
│                      │                          │ │(Process)│            │
└──────────────────────┘                          │ └────┬────┘            │
                                                  │      │               │
                                                  │ ┌────▼────┐            │
                                                  │ │Tournament│           │
                                                  │ │Register │            │
                                                  │ │(Process) │           │
                                                  │ └────┬────┘            │
                                                  │      │                │
                                                  │ ┌────▼────────┐        │
                                                  │ │ Database    │        │
                                                  │ │ Storage     │        │
                                                  │ │ (Cylinder)  │        │
                                                  │ └─────────────┘        │
                                                  └────────────────────────┘

                                    │
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   TOURNAMENT MODULE │
                         │   (Sub-Flowchart)   │
                         └──────────┬──────────┘
                                    │
                                    ▼
              ┌───────────────────────────────────────────┐
              │                                           │
              ▼                                           ▼
    ┌─────────────────────┐                     ┌─────────────────────┐
    │  Tournament Creation│                     │  Player Registration│
    │     (Process)       │                     │   (Parallelogram)   │
    │  (Admin/Staff)        │                     │                     │
    └──────────┬──────────┘                     └──────────┬──────────┘
               │                                           │
               ▼                                           ▼
    ┌─────────────────────┐                     ┌─────────────────────┐
    │ Registration Open?  │                     │  Registration Review│
    │    (Diamond)        │◀──────────────────│    (Diamond)        │
    │  Open / Closed      │                     │ Approve / Reject    │
    └──────────┬──────────┘                     └──────────┬──────────┘
               │                                           │
        ┌──────┴──────┐                             ┌──────┴──────┐
        ▼             ▼                             ▼             ▼
      Open         Closed                       Approved      Rejected
        │             │                             │             │
        ▼             ▼                             ▼             ▼
   ┌────────┐    ┌────────┐                  ┌────────┐    ┌────────┐
   │ Accept │    │ Wait   │                  │Bracket │    │ Notify │
   │Players │    │ Period │                  │Generate│    │ Player │
   │        │    │ (Loop) │                  │        │    │        │
   └───┬────┘    └────────┘                  └───┬────┘    └────────┘
       │                                         │
       ▼                                         ▼
┌─────────────────────────┐           ┌─────────────────────────┐
│   Minimum Players?      │           │   Match Scheduling      │
│      (Diamond)          │           │     (Process)           │
│  Yes / No               │           │  Assign Courts & Time   │
└──────────┬──────────────┘           └──────────┬──────────────┘
           │                                    │
    ┌──────┴──────┐                      ┌──────┴──────┐
    ▼             ▼                      ▼             ▼
  Yes            No                   Continue      End of
    │             │                      │          Tournament
    ▼             ▼                      ▼             │
┌────────┐    ┌────────┐          ┌────────┐       │
│Generate│    │Extend  │          │  Match │       │
│Matches │    │Reg.    │          │ Score  │       │
│        │    │Period  │          │Entry    │       │
└────────┘    └────────┘          │(Staff) │       │
                                   └───┬────┘       │
                                       │            │
                                       ▼            │
                              ┌────────────────┐    │
                              │  Winner?       │    │
                              │  (Diamond)     │────┘
                              │  Yes / No      │
                              └───────┬────────┘
                                      │
                               ┌──────┴──────┐
                               ▼             ▼
                             Yes            No
                               │             │
                               ▼             ▼
                          ┌────────┐    ┌────────┐
                          │Update  │    │Next    │
                          │Leaderbd│    │Round   │
                          └────────┘    └────────┘

                                    │
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  RESERVATION MODULE │
                         │   (Sub-Flowchart)   │
                         └──────────┬──────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                                                                     │
    ▼                                                                     │
┌─────────────────────┐                                         ┌─────────────────────┐
│  Select Court       │                                         │  Staff Approval     │
│  (Parallelogram)    │                                         │     (Diamond)       │
│  Indoor / Outdoor   │                                         │  Approve / Reject │
└──────────┬──────────┘                                         └──────────┬──────────┘
           │                                                               │
           ▼                                                               ▼
┌─────────────────────┐                                         ┌─────────────────────┐
│  Select Date/Time   │                                         │  Payment Processing │
│     (Process)       │                                         │     (Diamond)       │
│  Check Availability │                                         │  GCash/Cash/Card    │
└──────────┬──────────┘                                         └──────────┬──────────┘
           │                                                               │
           ▼                                                               ▼
┌─────────────────────┐                                         ┌─────────────────────┐
│  Available?         │                                         │  Payment Verified?  │
│    (Diamond)        │                                         │     (Diamond)       │
│  Yes / No           │                                         │   Yes / No          │
└──────────┬──────────┘                                         └──────────┬──────────┘
           │                                                               │
    ┌──────┴──────┐                                                 ┌──────┴──────┐
    ▼             ▼                                                 ▼             ▼
  Yes            No                                              Yes            No
    │             │                                                 │             │
    ▼             ▼                                                 ▼             ▼
┌────────┐    ┌────────┐                                     ┌────────┐    ┌────────┐
│ Add    │    │Suggest │                                     │Confirm │    │Retry/  │
│Equipment│   │Alternative│                                    │Reservation│   │Cancel  │
│(Optional)│   │Slots    │                                    │        │   │        │
└───┬────┘    └────────┘                                     └────┬───┘   └────────┘
    │                                                             │
    ▼                                                             ▼
┌─────────────────────┐                                         ┌─────────────────────┐
│  Calculate Total    │                                         │  Database Storage   │
│     (Process)       │                                         │    (Cylinder)       │
│  Court + Equipment  │                                         │  Reservation Record │
└──────────┬──────────┘                                         └─────────────────────┘
           │
           ▼
┌─────────────────────┐
│  Create Payment     │
│     (Process)       │
│  Generate Record    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Database Storage   │
│    (Cylinder)       │
│  Payment Record     │
└─────────────────────┘

                                    │
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  EQUIPMENT MODULE   │
                         │   (Sub-Flowchart)   │
                         └──────────┬──────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                                                                     │
    ▼                                                                     ▼
┌─────────────────────┐                                         ┌─────────────────────┐
│  Browse Equipment   │                                         │  Check-In Process   │
│     (Process)       │                                         │     (Process)       │
│  View Availability  │                                         │  Staff Verification │
└──────────┬──────────┘                                         └──────────┬──────────┘
           │                                                               │
           ▼                                                               ▼
┌─────────────────────┐                                         ┌─────────────────────┐
│  Select Item        │                                         │  Check-Out Process  │
│  (Parallelogram)    │                                         │     (Process)       │
│  Paddle/Ball/Net    │                                         │  Record Condition   │
└──────────┬──────────┘                                         └──────────┬──────────┘
           │                                                               │
           ▼                                                               ▼
┌─────────────────────┐                                         ┌─────────────────────┐
│  In Stock?          │                                         │  Return Process     │
│    (Diamond)        │                                         │     (Process)       │
│  Yes / No           │                                         │  Update Inventory   │
└──────────┬──────────┘                                         └──────────┬──────────┘
           │                                                               │
    ┌──────┴──────┐                                                 ┌──────┴──────┐
    ▼             ▼                                                 ▼             ▼
  Yes            No                                              On Time        Late
    │             │                                                 │             │
    ▼             ▼                                                 ▼             ▼
┌────────┐    ┌────────┐                                     ┌────────┐    ┌────────┐
│Reserve │    │ Notify │                                     │Complete│    │Add Fee │
│Item    │    │Out of  │                                     │Rental  │    │        │
│        │    │Stock   │                                     │        │    │        │
└───┬────┘    └────────┘                                     └───┬────┘    └───┬────┘
    │                                                             │             │
    ▼                                                             ▼             ▼
┌─────────────────────┐                                         ┌─────────────────────┐
│  Link to Reservation│                                         │  Database Storage   │
│     (Process)       │                                         │    (Cylinder)       │
│  Or Standalone      │                                         │  Update Status      │
└──────────┬──────────┘                                         └─────────────────────┘
           │
           ▼
┌─────────────────────┐
│  Database Storage   │
│    (Cylinder)       │
│  Rental Record      │
└─────────────────────┘

                                    │
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  PAYMENT MODULE     │
                         │   (Sub-Flowchart)   │
                         └──────────┬──────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                                                                     │
    ▼                                                                     ▼
┌─────────────────────┐                                         ┌─────────────────────┐
│  Select Method      │                                         │  Cash Payment       │
│     (Diamond)       │                                         │     (Process)       │
│  GCash/Cash/Card    │                                         │  Counter Payment    │
└──────────┬──────────┘                                         └──────────┬──────────┘
           │                                                               │
    ┌──────┼──────┐                                                 ┌──────┴──────┐
    │      │      │                                                 ▼             ▼
    ▼      ▼      ▼                                            Received      Pending
┌────────┐┌────────┐┌────────┐                                    │             │
│ GCash  ││  Cash  ││  Card  │                                    ▼             ▼
│        ││        ││        │                              ┌────────┐    ┌────────┐
└───┬────┘└────┬───┘└───┬────┘                              │Confirm │    │Wait for│
    │          │        │                                    │Payment │    │Payment │
    ▼          │        ▼                                    └────────┘    └────────┘
┌────────┐     │   ┌────────┐                                        │
│Upload  │     │   │Instant │                                        │
│Receipt │     │   │Process │                                        ▼
└───┬────┘     │   └───┬────┘                               ┌─────────────────────┐
    │          │       │                                    │  Database Storage   │
    ▼          │       ▼                                    │    (Cylinder)       │
┌────────┐     │  ┌────────┐                                 │  Payment Record     │
│Verify  │     │  │Confirm │                                 └─────────────────────┘
│(Staff) │     │  │Payment │
└───┬────┘     │  └────────┘
    │          │       │
    ▼          ▼       ▼
┌─────────────────────────────┐
│    Database Storage         │
│      (Cylinder)             │
│   Payment Transaction Log   │
└─────────────────────────────┘

                                    │
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   NOTIFICATION      │
                         │     MODULE          │
                         └──────────┬──────────┘
                                    │
                                    ▼
              ┌───────────────────────────────────────────┐
              │                                           │
              ▼                                           ▼
    ┌─────────────────────┐                     ┌─────────────────────┐
    │  Trigger Events     │                     │  Delivery Method      │
│     (Process)       │                     │     (Process)       │
├─────────────────────┤                     ├─────────────────────┤
│ • Reservation Status│                     │ • In-App Notification │
│ • Payment Received  │                     │ • Email Alert         │
│ • Tournament Update │                     │ • SMS (Optional)      │
│ • Equipment Due     │                     │                       │
└──────────┬──────────┘                     └──────────┬──────────┘
           │                                           │
           ▼                                           ▼
┌─────────────────────┐                     ┌─────────────────────┐
│  Database Storage     │                     │  Mark as Read?      │
│    (Cylinder)         │                     │    (Diamond)        │
│  Notification Queue   │                     │  Yes / No           │
└─────────────────────┘                     └─────────────────────┘

                                    │
                                    │
                                    ▼
                              ╔═══════════╗
                              ║    END    ║
                              ║   (Oval)  ║
                              ╚═══════════╝
```

---

## Flowchart Symbol Legend

| Symbol | Name | Description |
|--------|------|-------------|
| ⬭ **Oval** | Terminal | Start/End of a process |
| ⬜ **Rectangle** | Process | Action or operation performed |
| ◇ **Diamond** | Decision | Yes/No or multiple choice decision point |
| ▱ **Parallelogram** | Input/Output | Data entry or retrieval |
| 🗄️ **Cylinder** | Database | Data storage and retrieval operations |
| 📄 **Document** | Document/Report | Output report or screen display |
| → **Arrow** | Flow Line | Direction of process flow |

---

## System Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  Public Pages  │  User Dashboard  │  Staff Panel  │  Admin Panel │
│  (About/Contact│  (Reservations,  │  (Approvals,  │  (Reports,   │
│   Pricing)     │   Tournaments)   │   Equipment)  │   Settings)  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  Accounts  │  Courts  │  Reservations │  Payments │  Tournaments │
│  (Users)   │  (Sites) │  (Bookings)   │  (GCash,  │  (Matches) │
│            │          │               │   Cash)   │            │
├─────────────────────────────────────────────────────────────────┤
│  Equipment │  Dashboard│ Notifications │  Scoring  │   (CMS)   │
│  (Rentals) │  (Content)│  (Alerts)     │  (Points) │           │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                     PostgreSQL Database                          │
│         (Users, Courts, Reservations, Payments, etc.)            │
└─────────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  Django Framework  │  Django ORM  │  Media Storage  │  Cache  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key System Modules

1. **Accounts Module** - User authentication, registration, role-based access control (Admin/Staff/Player)
2. **Courts Module** - Court management with sites, availability checking, and pricing
3. **Reservations Module** - Booking workflow with time slots, approval process, and calendar view
4. **Equipment Module** - Inventory tracking, rental management, and condition monitoring
5. **Payments Module** - Multi-method payment processing (GCash, Cash, Card) with verification
6. **Tournaments Module** - Registration, bracket generation, match scheduling, and scoring
7. **Dashboard/Content Module** - CMS for public pages, testimonials, gallery, and site content
8. **Notifications Module** - Real-time alerts for users and staff
9. **Scoring Module** - Match score tracking and leaderboard management

---

*Document Version: 1.0*  
*System: PickleSphere v1.0*  
*Framework: Django 5.x*
