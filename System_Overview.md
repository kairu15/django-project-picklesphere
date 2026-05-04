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
    %% Start/End Symbols
    Start([Start]) --> UserAction
    
    %% User Action Decision
    UserAction{User Type} --> Admin[Administrator]
    UserAction --> Player[Player]
    UserAction --> Organizer[Tournament Organizer]
    
    %% Administrator Flow
    Admin --> AdminLogin[Login to Admin Panel]
    AdminLogin --> AdminDashboard[Access Dashboard]
    AdminDashboard --> AdminTasks{Select Task}
    
    AdminTasks --> ManageCourts[Manage Courts]
    AdminTasks --> ManageUsers[Manage Users]
    AdminTasks --> ManageEquipment[Manage Equipment]
    AdminTasks --> ViewReports[View Reports]
    AdminTasks --> ManageTournaments[Manage Tournaments]
    
    ManageCourts --> CourtActions{Action}
    CourtActions --> AddCourt[Add New Court]
    CourtActions --> UpdateCourt[Update Court Info]
    CourtActions --> DeleteCourt[Delete Court]
    
    AddCourt --> SaveCourt[Save to Database]
    UpdateCourt --> SaveCourt
    SaveCourt --> AdminDashboard
    
    ManageUsers --> UserActions{Action}
    UserActions --> ViewUsers[View All Users]
    UserActions --> EditUser[Edit User Profile]
    UserActions --> SuspendUser[Suspend User]
    
    ViewUsers --> AdminDashboard
    EditUser --> SaveUser[Save Changes]
    SuspendUser --> SaveUser
    SaveUser --> AdminDashboard
    
    ManageEquipment --> EquipActions{Action}
    EquipActions --> AddEquip[Add Equipment]
    EquipActions --> UpdateEquip[Update Equipment]
    EquipActions --> ViewRentals[View Rentals]
    
    AddEquip --> SaveEquip[Save to Database]
    UpdateEquip --> SaveEquip
    ViewRentals --> AdminDashboard
    SaveEquip --> AdminDashboard
    
    ViewReports --> GenerateReport[Generate Report]
    GenerateReport --> AdminDashboard
    
    ManageTournaments --> TourneyActions{Action}
    TourneyActions --> CreateTourney[Create Tournament]
    TourneyActions --> UpdateTourney[Update Tournament]
    TourneyActions --> ViewResults[View Results]
    
    CreateTourney --> SaveTourney[Save to Database]
    UpdateTourney --> SaveTourney
    ViewResults --> AdminDashboard
    SaveTourney --> AdminDashboard
    
    %% Player Flow
    Player --> PlayerLogin[Login to Account]
    PlayerLogin --> PlayerDashboard[Access User Dashboard]
    PlayerDashboard --> PlayerTasks{Select Task}
    
    PlayerTasks --> BookCourt[Book Court]
    PlayerTasks --> RentEquipment[Rent Equipment]
    PlayerTasks --> JoinTournament[Join Tournament]
    PlayerTasks --> ViewProfile[View Profile]
    PlayerTasks --> ViewHistory[View History]
    
    BookCourt --> CheckAvailability[Check Court Availability]
    CheckAvailability --> Available{Available?}
    Available --> Yes[Select Time Slot]
    Available --> No[Select Different Date]
    No --> CheckAvailability
    
    Yes --> ProcessPayment[Process Payment]
    ProcessPayment --> PaymentSuccess{Payment Successful?}
    PaymentSuccess --> YesConfirm[Confirm Booking]
    PaymentSuccess --> NoRetry[Retry Payment]
    NoRetry --> ProcessPayment
    
    YesConfirm --> SaveBooking[Save Booking to Database]
    SaveBooking --> SendNotification[Send Confirmation Notification]
    SendNotification --> PlayerDashboard
    
    RentEquipment --> ViewEquipment[View Available Equipment]
    ViewEquipment --> SelectEquip[Select Equipment]
    SelectEquip --> EquipPayment[Process Equipment Payment]
    EquipPayment --> EquipSuccess{Payment Successful?}
    EquipSuccess --> YesEquip[Confirm Rental]
    EquipSuccess --> NoEquip[Retry Payment]
    NoEquip --> EquipPayment
    
    YesEquip --> SaveRental[Save Rental to Database]
    SaveRental --> EquipNotify[Send Rental Notification]
    EquipNotify --> PlayerDashboard
    
    JoinTournament --> ViewTournaments[View Available Tournaments]
    ViewTournaments --> SelectTourney[Select Tournament]
    SelectTourney --> RegisterTourney[Register for Tournament]
    RegisterTourney --> TourneyPayment[Process Registration Fee]
    TourneyPayment --> TourneySuccess{Payment Successful?}
    TourneySuccess --> YesTourney[Confirm Registration]
    TourneySuccess --> NoTourney[Retry Payment]
    NoTourney --> TourneyPayment
    
    YesTourney --> SaveRegistration[Save Registration]
    SaveRegistration --> TourneyNotify[Send Registration Notification]
    TourneyNotify --> PlayerDashboard
    
    ViewProfile --> ProfileActions{Action}
    ProfileActions --> UpdateProfile[Update Profile]
    ProfileActions --> ChangePassword[Change Password]
    
    UpdateProfile --> SaveProfile[Save Changes]
    ChangePassword --> SavePassword[Save New Password]
    SaveProfile --> PlayerDashboard
    SavePassword --> PlayerDashboard
    
    ViewHistory --> DisplayHistory[Display Booking History]
    DisplayHistory --> PlayerDashboard
    
    %% Tournament Organizer Flow
    Organizer --> OrganizerLogin[Login as Organizer]
    OrganizerLogin --> OrganizerDashboard[Access Organizer Dashboard]
    OrganizerDashboard --> OrganizerTasks{Select Task}
    
    OrganizerTasks --> CreateEvent[Create Tournament Event]
    OrganizerTasks --> ManageParticipants[Manage Participants]
    OrganizerTasks --> TrackScores[Track Scores]
    OrganizerTasks --> PublishResults[Publish Results]
    
    CreateEvent --> EventDetails[Enter Event Details]
    EventDetails --> SaveEvent[Save Event to Database]
    SaveEvent --> OrganizerDashboard
    
    ManageParticipants --> ViewParticipants[View Registered Participants]
    ViewParticipants --> ParticipantActions{Action}
    ParticipantActions --> Approve[Approve Participant]
    ParticipantActions --> Reject[Reject Participant]
    
    Approve --> UpdateStatus[Update Participant Status]
    Reject --> UpdateStatus
    UpdateStatus --> OrganizerDashboard
    
    TrackScores --> SelectMatch[Select Match]
    SelectMatch --> EnterScores[Enter Match Scores]
    EnterScores --> SaveScores[Save Scores to Database]
    SaveScores --> OrganizerDashboard
    
    PublishResults --> GenerateResults[Generate Final Results]
    GenerateResults --> Publish[Publish to Public]
    Publish --> OrganizerDashboard
    
    %% Common Flow - Logout
    AdminDashboard --> Logout{Logout?}
    PlayerDashboard --> Logout
    OrganizerDashboard --> Logout
    
    Logout --> YesLogout[Logout User]
    YesLogout --> End([End])
    
    Logout --> NoReturn[Return to Dashboard]
    NoReturn --> AdminDashboard
    NoReturn --> PlayerDashboard
    NoReturn --> OrganizerDashboard
    
    %% Styling
    classDef startEnd fill:#2ecc71,stroke:#27ae60,stroke-width:3px,color:#fff
    classDef process fill:#3498db,stroke:#2980b9,stroke-width:2px,color:#fff
    classDef decision fill:#f39c12,stroke:#e67e22,stroke-width:2px,color:#fff
    classDef database fill:#9b59b6,stroke:#8e44ad,stroke-width:2px,color:#fff
    classDef user fill:#e74c3c,stroke:#c0392b,stroke-width:2px,color:#fff
    
    class Start,End startEnd
    class AdminLogin,AdminDashboard,PlayerLogin,PlayerDashboard,OrganizerLogin,OrganizerDashboard,Logout,YesLogout process
    class UserAction,AdminTasks,CourtActions,UserActions,EquipActions,Available,PaymentSuccess,EquipSuccess,TourneySuccess,ParticipantActions,Logout decision
    class SaveCourt,SaveUser,SaveEquip,SaveBooking,SaveRental,SaveRegistration,SaveEvent,UpdateStatus,SaveScores database
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
