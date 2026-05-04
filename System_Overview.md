# PickleSphere - System Overview

## Table of Contents
- [System Overview](#system-overview)
- [Purpose of the System](#purpose-of-the-system)
- [Target Users](#target-users)
- [System Flowchart](#system-flowchart)
- [System Architecture](#system-architecture)
- [Key Features](#key-features)

---

## System Overview

PickleSphere is a comprehensive **Pickleball Facility & Game Management System** built with Django framework. The system provides an integrated platform for managing pickleball court reservations, equipment rentals, game scoring, tournament organization, and user management. It serves as a centralized solution for pickleball facility operators and players to streamline operations and enhance the overall playing experience.

### Technology Stack
- **Backend Framework**: Django 4.2+
- **Database**: MySQL
- **Real-time Communication**: Django Channels with Redis
- **Frontend**: Django Templates with Crispy Forms
- **Authentication**: Custom User Model with Django Auth
- **Media Management**: Pillow for image handling

### System Modules
The system consists of the following integrated modules:
- **Accounts**: User registration, authentication, and profile management
- **Courts**: Court information, images, and availability management
- **Reservations**: Court booking system with scheduling
- **Payments**: Payment processing and transaction logging
- **Scoring**: Game scoring system with customizable formats
- **Notifications**: Real-time notification system
- **Dashboard**: Centralized admin and user dashboard
- **Equipment**: Equipment rental management
- **Tournaments**: Tournament organization and management

---

## Purpose of the System

The primary purpose of PickleSphere is to digitize and streamline the operations of pickleball facilities while providing an enhanced experience for players. The system addresses the following key objectives:

### Operational Efficiency
- Automate court reservation processes
- Reduce manual administrative tasks
- Streamline equipment rental management
- Centralize facility operations

### User Experience Enhancement
- Provide easy online booking capabilities
- Enable real-time availability checking
- Offer comprehensive game tracking and scoring
- Facilitate tournament participation

### Data Management
- Maintain comprehensive user profiles
- Track reservation history and patterns
- Monitor equipment inventory and usage
- Generate reports for facility analytics

### Communication
- Send automated notifications for bookings
- Provide updates on tournament schedules
- Enable real-time communication between users and administrators

---

## Target Users

### Primary Users

#### 1. Facility Administrators/Staff
- **Role**: Manage day-to-day facility operations
- **Key Needs**: 
  - Court management and scheduling
  - User account oversight
  - Payment processing
  - Equipment inventory tracking
  - Tournament organization
  - System configuration and settings

#### 2. Players (Regular Users)
- **Role**: End users who utilize the facility
- **Key Needs**:
  - Court reservation and booking
  - Profile and skill level management
  - Game scoring and tracking
  - Equipment rental
  - Tournament registration
  - Payment processing

#### 3. Tournament Organizers
- **Role**: Coordinate and manage pickleball tournaments
- **Key Needs**:
  - Tournament creation and scheduling
  - Participant registration
  - Bracket management
  - Score tracking
  - Results publication

### Secondary Users

#### 4. Equipment Managers
- **Role**: Oversee equipment inventory and maintenance
- **Key Needs**:
  - Equipment catalog management
  - Rental tracking
  - Maintenance scheduling
  - Availability monitoring

#### 5. Finance/Accounting Staff
- **Role**: Handle financial transactions
- **Key Needs**:
  - Payment verification
  - Transaction logging
  - Revenue reporting
  - Refund processing

---

## System Flowchart

```mermaid
flowchart TD
    Start([Start]) --> Login{Login?}
    Login --> NoLogin[Register / Login]
    NoLogin --> UserType{User Type}

    UserType --> Admin[Administrator]
    UserType --> Player[Player]
    UserType --> Organizer[Organizer]

    %% Administrator Flow
    Admin --> AdminDash[Admin Dashboard]
    AdminDash --> AdminTask{Select Task}

    AdminTask --> Courts[Manage Courts]
    AdminTask --> Users[Manage Users]
    AdminTask --> Equip[Manage Equipment]
    AdminTask --> Reports[View Reports]
    AdminTask --> Tourneys[Manage Tournaments]

    Courts --> CourtDB[Update Database]
    Users --> UserDB[Update Database]
    Equip --> EquipDB[Update Database]
    Reports --> AdminDash
    Tourneys --> TourneyDB[Update Database]

    CourtDB --> AdminDash
    UserDB --> AdminDash
    EquipDB --> AdminDash
    TourneyDB --> AdminDash

    %% Player Flow
    Player --> PlayerDash[Player Dashboard]
    PlayerDash --> PlayerTask{Select Task}

    PlayerTask --> Book[Book Court]
    PlayerTask --> Rent[Rent Equipment]
    PlayerTask --> Join[Join Tournament]
    PlayerTask --> Profile[Manage Profile]
    PlayerTask --> History[View History]

    Book --> CheckAvail[Check Availability]
    CheckAvail --> SelectTime[Select Time Slot]
    SelectTime --> Pay1[Process Payment]
    Pay1 --> BookingDB[Save Booking]
    BookingDB --> Notify1[Send Notification]
    Notify1 --> PlayerDash

    Rent --> ViewEquip[View Equipment]
    ViewEquip --> SelectEquip[Select Equipment]
    SelectEquip --> Pay2[Process Payment]
    Pay2 --> RentalDB[Save Rental]
    RentalDB --> Notify2[Send Notification]
    Notify2 --> PlayerDash

    Join --> ViewTourneys[View Tournaments]
    ViewTourneys --> SelectTourney[Select Tournament]
    SelectTourney --> Register[Register]
    Register --> Pay3[Process Payment]
    Pay3 --> RegDB[Save Registration]
    RegDB --> Notify3[Send Notification]
    Notify3 --> PlayerDash

    Profile --> ProfileDB[Update Profile]
    ProfileDB --> PlayerDash
    History --> PlayerDash

    %% Organizer Flow
    Organizer --> OrgDash[Organizer Dashboard]
    OrgDash --> OrgTask{Select Task}

    OrgTask --> CreateEvent[Create Event]
    OrgTask --> ManagePart[Manage Participants]
    OrgTask --> TrackScore[Track Scores]
    OrgTask --> Publish[Publish Results]

    CreateEvent --> EventDB[Save Event]
    EventDB --> OrgDash

    ManagePart --> PartDB[Update Status]
    PartDB --> OrgDash

    TrackScore --> ScoreDB[Save Scores]
    ScoreDB --> OrgDash

    Publish --> ResultsDB[Save Results]
    ResultsDB --> OrgDash

    %% Common Logout Flow
    AdminDash --> Logout{Logout?}
    PlayerDash --> Logout
    OrgDash --> Logout

    Logout --> Yes[Logout]
    Yes --> End([End])

    Logout --> No[Continue]
    No --> AdminDash
    No --> PlayerDash
    No --> OrgDash

    %% Styling
    classDef startEnd fill:#2ecc71,stroke:#27ae60,stroke-width:3px,color:#fff
    classDef process fill:#3498db,stroke:#2980b9,stroke-width:2px,color:#fff
    classDef decision fill:#f39c12,stroke:#e67e22,stroke-width:2px,color:#fff
    classDef database fill:#9b59b6,stroke:#8e44ad,stroke-width:2px,color:#fff
    classDef user fill:#e74c3c,stroke:#c0392b,stroke-width:2px,color:#fff

    class Start,End startEnd
    class NoLogin,AdminDash,PlayerDash,OrgDash,Courts,Users,Equip,Reports,Tourneys,Book,Rent,Join,Profile,History,CheckAvail,SelectTime,ViewEquip,SelectEquip,ViewTourneys,SelectTourney,Register,CreateEvent,ManagePart,TrackScore,Publish,Yes,No process
    class Login,UserType,AdminTask,PlayerTask,OrgTask,Logout decision
    class CourtDB,UserDB,EquipDB,TourneyDB,BookingDB,RentalDB,RegDB,ProfileDB,EventDB,PartDB,ScoreDB,ResultsDB database
    class Admin,Player,Organizer user
```

### Flowchart Legend

| Symbol | Description |
|--------|-------------|
| **Oval** | Start/End points |
| **Rectangle** | Process/Action |
| **Diamond** | Decision point |
| **Cylinder** | Database operation |
| **Parallelogram** | Input/Output (implied in process) |
| **Rounded Rectangle** | User roles |

---

## System Architecture

### Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Web UI     │  │  Admin Panel │  │  Mobile View │  │
│  │  (Templates) │  │   (Django    │  │  (Responsive)│  │
│  │              │  │    Admin)    │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                     Application Layer                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Accounts │  │ Reserva- │  │ Payments │  │ Scoring │ │
│  │   App    │  │  tions   │  │   App    │  │   App   │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Courts  │  │Equipment │  │Tournament│  │Notifica-│ │
│  │   App    │  │   App    │  │   App    │  │  tions  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                      Data Layer                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              MySQL Database                      │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │   │
│  │  │ Users   │ │ Courts  │ │ Booking │ │Payment │ │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └────────┘ │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │   │
│  │  │Equipment│ │Tourney  │ │Scores   │ │Notif.  │ │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Redis (Caching/Sessions)            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. User Management
- Custom user model with extended profiles
- Role-based access control (Admin, Player, Organizer)
- Profile customization with skill levels
- Authentication and authorization

### 2. Court Reservation System
- Real-time court availability checking
- Flexible booking schedules
- Automated confirmation notifications
- Booking history and management

### 3. Equipment Rental
- Equipment catalog with images
- Availability tracking
- Rental period management
- Payment integration

### 4. Payment Processing
- Secure payment handling
- Transaction logging
- Refund processing
- Payment history

### 5. Game Scoring
- Customizable scoring formats
- Real-time score updates
- Match history tracking
- Statistics generation

### 6. Tournament Management
- Tournament creation and scheduling
- Participant registration
- Bracket management
- Results tracking and publication

### 7. Notification System
- Real-time notifications via Django Channels
- Email notifications
- In-app notification center
- Notification preferences

### 8. Dashboard
- Centralized admin dashboard
- User-specific dashboards
- Analytics and reporting
- Activity logging

---

## Database Schema Overview

### Core Tables
- **users**: User accounts and profiles
- **courts**: Court information and images
- **reservations**: Booking records
- **payments**: Payment transactions
- **equipment**: Equipment inventory
- **rentals**: Equipment rental records
- **tournaments**: Tournament events
- **participants**: Tournament participants
- **matches**: Match records and scores
- **notifications**: Notification records

---

## Security Features

- CSRF protection
- SQL injection prevention (Django ORM)
- XSS protection
- Secure password hashing
- Session management
- Authentication middleware
- File upload validation

---

## Future Enhancements

- Mobile application (iOS/Android)
- Advanced analytics and reporting
- AI-powered court recommendations
- Social features (friend system, chat)
- Integration with payment gateways (Stripe, PayPal)
- Multi-facility support
- API for third-party integrations

---

*Document Version: 1.0*  
*Last Updated: May 2026*  
*System: PickleSphere v1.0*
