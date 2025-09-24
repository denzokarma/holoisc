# Overview

This is a Flask-based hologram stock management system designed to track hologram inventory and issuance. The application manages holograms that arrive in cartons of 100,000 units, automatically divided into 5 boxes of 20,000 units each. The system provides functionality for stock management, sequential hologram issuance with permit tracking, and PDF report generation.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Template Engine**: Jinja2 templates with Flask
- **UI Framework**: Bootstrap 5.3.0 for responsive design
- **Icons**: Font Awesome 6.0.0 for consistent iconography
- **JavaScript**: Vanilla JavaScript for form interactions and client-side calculations
- **CSS**: Custom stylesheet for brand-specific styling

## Backend Architecture
- **Framework**: Flask with modular route organization
- **Forms**: Flask-WTF with WTForms for form handling and validation
- **Database ORM**: SQLAlchemy for database operations
- **PDF Generation**: ReportLab for generating formatted reports
- **Session Management**: Flask sessions with configurable secret key

## Data Storage Solutions
- **Primary Database**: SQLite for development/small-scale deployment
- **Schema Design**: 
  - Hierarchical structure: Cartons → Boxes → Individual holograms
  - Issue tracking with permit associations
  - Automatic series number allocation and tracking
- **Relationships**: 
  - One-to-many: Carton to Boxes
  - One-to-many: Issues to Permits
  - Cascade deletion for data consistency

## Authentication and Authorization
- **Current State**: No authentication system implemented
- **Session Security**: Configurable secret key via environment variables
- **Data Protection**: Basic form CSRF protection via Flask-WTF

## Business Logic Architecture
- **Stock Management**: Automatic box subdivision and series calculation
- **Sequential Allocation**: First-in-first-out hologram dispensing across boxes
- **Inventory Tracking**: Real-time stock balance calculation
- **Validation**: Unique constraint enforcement for issue numbers and carton numbers

# External Dependencies

## Frontend Libraries
- **Bootstrap 5.3.0**: UI framework from CDN
- **Font Awesome 6.0.0**: Icon library from CDN
- **No build process**: Direct CDN integration for simplicity

## Python Packages
- **Flask**: Web framework
- **Flask-SQLAlchemy**: Database ORM integration
- **Flask-WTF**: Form handling and CSRF protection
- **WTForms**: Form validation and rendering
- **ReportLab**: PDF generation for reports

## Database
- **SQLite**: File-based database (hologram_management.db)
- **No external database server required**
- **Automatic schema creation on first run**

## Environment Configuration
- **SESSION_SECRET**: Environment variable for session security
- **No external API integrations**
- **No third-party authentication services**

## Deployment Dependencies
- **Static file serving**: Flask development server
- **No external CDN**: Local static assets with CDN fallbacks
- **No caching layer**: Direct database queries