![Code Institute Project](documentation/code-institute-img.png)

<h1 align="center">
  <img src="documentation/game-abyss-favicon.webp" width="25" height="23" alt="Game Abyss Favicon"/>
  Milestone Project 3: Game Abyss
</h1>

<p align="center">
  <em><strong>
    A community-driven gaming blog built with Django and PostgreSQL.<br>
    Share reviews, discover new games, and join the conversation!
  </strong></em>
</p>

---

## 👉 [Visit Game Abyss](https://game-abyss-d0a64d3f2cf0.herokuapp.com/)

![Game Abyss Screenshot](documentation/am-i-responsive.png)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [User Experience Design](#user-experience-design)
    - [User Stories](#user-stories)
    - [Structure](#structure)
    - [Design](#design)
        - [Wireframes](#wireframes)
        - [Colour Palette](#colour-palette)
        - [Typography](#typography)
3. [Features](#features)
    - [Existing Features](#existing-features)
    - [Future Features](#future-features)
4. [Database Design](#database-design)
5. [Technologies Used](#technologies-used)
6. [Testing & Bug Fixes](#testing--bug-fixes)
7. [Deployment](#deployment)
    - [Local Development](#local-development)
    - [Heroku Deployment](#heroku-deployment)
8. [Credits](#credits)

---

## Project Overview

Welcome to **Game Abyss!**

A modern blog platform designed for the gaming community. Whether you're a casual player or a hardcore gamer, Game Abyss is your space to:

> Share your thoughts, read reviews, and connect with fellow gamers from around the world!

### Key Features

- **User Authentication**: Secure registration, login, and password reset functionality
- **Blog System**: Create, read, update, and delete blog posts
- **User Profiles**: Personalized profiles for each member of the community
- **Responsive Design**: Fully responsive interface that works on all devices
- **Admin Dashboard**: Comprehensive admin panel for content management
- **Comment System**: Engage with posts through comments and discussions

### Target Audience

Game Abyss is built for:

- Gamers who want to share their gaming experiences
- Players looking for honest reviews and recommendations
- Gaming enthusiasts who enjoy community discussions
- Content creators who want a platform for their gaming content

---

## User Experience Design

### User Stories

#### As a Visitor (Not Logged In)

- I want to browse blog posts without creating an account
- I want to read reviews and articles about games
- I want to easily navigate the site and find content
- I want to see a clean, modern interface that works on my device
- I want to register for an account to join the community

#### As a Registered User

- I want to log in securely to access my account
- I want to create and publish my own blog posts
- I want to edit or delete my posts if I change my mind
- I want to comment on other users' posts
- I want to reset my password if I forget it
- I want to customize my profile information

#### As an Admin

- I want to manage all content through an admin dashboard
- I want to moderate posts and comments
- I want to manage user accounts
- I want to configure site settings

### Structure

The website follows a clear, intuitive structure:

```
Homepage
├── Navigation (Navbar)
│   ├── Home
│   ├── About
│   ├── Contact
│   ├── Login/Register (if not authenticated)
│   └── Profile/Logout (if authenticated)
├── Hero Section (Welcome message + CTA)
├── Latest Posts Section
└── Footer (Copyright + Social Links)

Blog System
├── Blog List (All posts)
├── Blog Detail (Single post view)
├── Create Post (Authenticated users)
├── Edit Post (Post author only)
└── Delete Post (Post author only)

Authentication System
├── Login
├── Register
├── Logout
├── Password Reset
└── Email Verification
```

### Design

#### Wireframes

The layout for Game Abyss was carefully planned using [Balsamiq](https://balsamiq.com/), creating wireframes for different devices to ensure a consistent user experience across all platforms.

Wireframes were created for:

- **Desktop PC**
- **Tablet (iPad Pro)**
- **Mobile (iPhone SE / Samsung Galaxy)**

Each wireframe includes:

- **Navigation bar** with logo and menu items
- **Hero section** with welcoming message and call-to-action buttons
- **Content area** for blog posts and main content
- **Footer** with copyright and social links

The wireframes helped establish the visual hierarchy and ensure the layout works seamlessly on all screen sizes.

![Wireframes](documentation/wireframes.png)

#### Colour Palette

Game Abyss uses a dark, modern colour scheme inspired by gaming aesthetics:

| Name           | Hex Code  | Use                             |
| -------------- | --------- | ------------------------------- |
| Deep Black     | `#0a0e27` | Primary background              |
| Dark Navy      | `#1a1f3a` | Secondary background / Cards    |
| Slate Grey     | `#2d3250` | Borders / Dividers              |
| Light Text     | `#e4e4e7` | Primary text                    |
| Muted Text     | `#9ca3af` | Secondary text / Labels         |
| Primary Accent | `#7c3aed` | Buttons / Links / Active states |
| Hover Accent   | `#9333ea` | Hover states                    |
| Success Green  | `#10b981` | Success messages                |
| Warning Yellow | `#f59e0b` | Warnings                        |
| Error Red      | `#ef4444` | Errors                          |

This dark palette creates an immersive gaming atmosphere while maintaining excellent readability and accessibility.

![Color Palette](documentation/color-palette.png)

#### Typography

Game Abyss uses carefully selected fonts from [Google Fonts](https://fonts.google.com/) to create a modern, readable interface:

| Where Used         | Font Family | Purpose                           |
| ------------------ | ----------- | --------------------------------- |
| Headings / Display | Inter       | Main titles and headings          |
| Body Text          | Inter       | Paragraphs, content, general text |
| Monospace / Code   | Roboto Mono | Code snippets, technical content  |

```css
/* Font families in CSS */

--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'Roboto Mono', 'Courier New', monospace;
```

**Font Weights:**

- Light (300): Secondary text, captions
- Regular (400): Body text
- Medium (500): Subheadings, emphasis
- Semi-Bold (600): Navigation, buttons
- Bold (700): Main headings

---

## Features

### Existing Features

#### 🏠 Homepage

- **Hero Section**: Eye-catching welcome message with call-to-action buttons
- **Latest Posts**: Display of recent blog posts from the community
- **Responsive Grid**: Adaptive layout for all screen sizes

#### 📝 Blog System

- **Post Creation**: Rich text editor for creating detailed blog posts
- **Post Management**: Edit and delete your own posts
- **Post Categories**: Organize content by game genres or topics
- **Post Views**: Track how many people read your posts

#### 👤 User Authentication

- **Registration**: Secure sign-up with email verification
- **Login/Logout**: Secure authentication system
- **Password Reset**: Email-based password recovery
- **Profile Management**: Update your profile information

#### 🎨 Design Features

- **Dark Theme**: Modern gaming-inspired dark interface
- **Responsive Navigation**: Mobile-friendly hamburger menu
- **Custom Cards**: Elegant post cards with hover effects
- **Loading States**: Visual feedback for user actions

#### 🔒 Security Features

- **CSRF Protection**: Built-in Django security
- **Password Hashing**: Secure password storage
- **Environment Variables**: Sensitive data protection
- **HTTPS**: Secure connection in production

### Future Features

Features planned for future releases:

- 💬 **Comment System**: Allow users to comment on blog posts
- ⭐ **Like System**: Let users like and favorite posts
- 🔍 **Search Functionality**: Search posts by title, content, or tags
- 🏷️ **Tag System**: Better content organization with tags
- 👥 **User Profiles**: Public profile pages with user's posts
- 📧 **Email Notifications**: Notify users of new comments or likes
- 🖼️ **Image Upload**: Allow users to add images to posts
- 📱 **Social Sharing**: Share posts on social media platforms
- 🎮 **Game Database**: Integration with game APIs for metadata
- 🏆 **User Reputation**: Gamification with points and badges

---

## Database Design

Game Abyss uses PostgreSQL in production and SQLite for local development. The database schema is managed through Django's ORM.

### Entity Relationship Diagram

```
┌─────────────────┐
│      User       │
│  (Django Auth)  │
├─────────────────┤
│ id (PK)         │
│ username        │
│ email           │
│ password        │
│ date_joined     │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────┐
│    BlogPost     │
├─────────────────┤
│ id (PK)         │
│ title           │
│ slug            │
│ author (FK)     │
│ content         │
│ excerpt         │
│ created_at      │
│ updated_at      │
│ published       │
│ views           │
└─────────────────┘
```

### Models Overview

#### User Model (Django Built-in)

Django's built-in User model provides authentication functionality.

#### BlogPost Model (Future)

```python
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    excerpt = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
```

---

## Technologies Used

### Core Technologies

#### Backend

- **[Python 3.12](https://www.python.org/)** – Programming language
- **[Django 5.2](https://www.djangoproject.com/)** – Web framework
- **[PostgreSQL](https://www.postgresql.org/)** – Production database
- **[SQLite](https://www.sqlite.org/)** – Development database

#### Frontend

- **HTML5** – Page structure
- **CSS3** – Styling and animations
- **JavaScript** – Interactivity
- **[Bootstrap 5](https://getbootstrap.com/)** – CSS framework

### Python Packages

```python
# Core Framework
Django==5.2.7
psycopg2-binary==2.9.10  # PostgreSQL adapter
dj-database-url==2.3.0   # Database URL parsing

# Authentication
django-allauth==65.4.0   # User authentication

# Static Files
whitenoise==6.8.2        # Static file serving

# Environment Variables
python-dotenv==1.0.0     # Load .env files
```

### Development Tools

- **[VS Code](https://code.visualstudio.com/)** – Code editor
- **[Git](https://git-scm.com/)** – Version control
- **[GitHub](https://github.com/)** – Code repository
- **[Heroku](https://www.heroku.com/)** – Deployment platform
- **[Balsamiq](https://balsamiq.com/)** – Wireframe creation

### Design & Media

- **[Google Fonts](https://fonts.google.com/)** – Typography
- **[Font Awesome](https://fontawesome.com/)** – Icons
- **[RealFaviconGenerator](https://realfavicongenerator.net/)** – Favicon generation
- **[Coolors](https://coolors.co/)** – Colour palette

### Testing & Validation

- **[W3C HTML Validator](https://validator.w3.org/)** – HTML validation
- **[W3C CSS Validator](https://jigsaw.w3.org/css-validator/)** – CSS validation
- **[JSHint](https://jshint.com/)** – JavaScript validation
- **[PEP8](https://pep8ci.herokuapp.com/)** – Python code validation
- **[Lighthouse](https://developers.google.com/web/tools/lighthouse)** – Performance testing
- **[Am I Responsive](https://ui.dev/amiresponsive)** – Responsiveness testing

---

## Testing & Bug Fixes

Full details on all testing carried out—including:

- Code validation (HTML, CSS, JavaScript, Python)
- Performance testing with Lighthouse
- Device and browser compatibility
- User story testing
- Manual feature testing
- Automated testing

> can be found in the **[TESTING.md](/TESTING.md)** file.

### Key Bug Fixes

#### 🐞 BUG 1: Static Files Not Loading in Production

**Problem:**
After deploying to Heroku, CSS and static files were not loading correctly. The site appeared unstyled in production.

**Cause:**
Django's default static file handling doesn't work in production without additional configuration.

**Solution:**
Implemented WhiteNoise for static file serving:

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Added this
    # ... other middleware
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

Ran `python manage.py collectstatic` before deployment to gather all static files.

#### 🐞 BUG 2: Database Connection Issues

**Problem:**
The application couldn't connect to PostgreSQL on Heroku, showing database connection errors.

**Cause:**
Missing `DATABASE_URL` configuration and incorrect SSL settings.

**Solution:**
Updated database configuration to use `dj-database-url`:

```python
# settings.py
db_url = os.environ.get("DATABASE_URL")
if db_url:
    DATABASES["default"] = dj_database_url.parse(
        db_url, conn_max_age=600, ssl_require=True
    )
```

Added `DATABASE_URL` to Heroku config vars with proper PostgreSQL connection string.

---

## Deployment

Game Abyss is deployed on **Heroku** with PostgreSQL database and uses **WhiteNoise** for static file serving.

### Local Development

#### Prerequisites

- Python 3.12 or higher
- Git
- A code editor (VS Code recommended)

#### Setup Steps

1. **Clone the Repository**

    ```bash
    git clone https://github.com/Drake-Designer/Game-Abyss.git
    cd Game-Abyss
    ```

2. **Create Virtual Environment**

    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up Environment Variables**

    Create an `env.py` file in the root directory:

    ```python
    import os

    os.environ.setdefault("SECRET_KEY", "your-secret-key-here")
    os.environ.setdefault("DEBUG", "True")
    os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
    ```

5. **Run Migrations**

    ```bash
    python manage.py migrate
    ```

6. **Create Superuser**

    ```bash
    python manage.py createsuperuser
    ```

7. **Collect Static Files**

    ```bash
    python manage.py collectstatic --noinput
    ```

8. **Run Development Server**

    ```bash
    python manage.py runserver
    ```

9. **Access the Site**
    - Main site: `http://localhost:8000`
    - Admin panel: `http://localhost:8000/admin`

### Heroku Deployment

#### Prerequisites

- Heroku account
- Heroku CLI installed
- PostgreSQL database (Heroku add-on)

#### Deployment Steps

1. **Create Heroku App**

    ```bash
    heroku create your-app-name
    ```

2. **Add PostgreSQL Database**

    ```bash
    heroku addons:create heroku-postgresql:essential-0
    ```

3. **Set Environment Variables**

    ```bash
    heroku config:set SECRET_KEY="your-secret-key"
    heroku config:set DEBUG="False"
    heroku config:set ALLOWED_HOSTS="your-app-name.herokuapp.com"
    heroku config:set CSRF_TRUSTED_ORIGINS="https://your-app-name.herokuapp.com"
    ```

4. **Deploy to Heroku**

    ```bash
    git push heroku main
    ```

5. **Run Migrations on Heroku**

    ```bash
    heroku run python manage.py migrate
    ```

6. **Create Superuser on Heroku**

    ```bash
    heroku run python manage.py createsuperuser
    ```

7. **Collect Static Files**

    ```bash
    heroku run python manage.py collectstatic --noinput
    ```

8. **Open Your App**
    ```bash
    heroku open
    ```

#### Important Files for Deployment

**Procfile** (tells Heroku how to run the app):

```
web: gunicorn core.wsgi:application
```

**requirements.txt** (Python dependencies):

```
Django==5.2.7
psycopg2-binary==2.9.10
dj-database-url==2.3.0
django-allauth==65.4.0
whitenoise==6.8.2
gunicorn==23.0.0
```

**runtime.txt** (Python version):

```
python-3.12.8
```

### Useful Links

- **Live Site:**
  [https://game-abyss-d0a64d3f2cf0.herokuapp.com/](https://game-abyss-d0a64d3f2cf0.herokuapp.com/)

- **GitHub Repository:**
  [https://github.com/Drake-Designer/Game-Abyss](https://github.com/Drake-Designer/Game-Abyss)

---

## Credits

I want to thank all the resources, tutorials, and people that helped me build **Game Abyss**.

This project represents my journey learning Django and building a full-stack web application.

### Learning Resources

#### Django Documentation & Tutorials

- **[Django Official Documentation](https://docs.djangoproject.com/)**
  _The main resource for learning Django fundamentals_

- **[Django for Beginners by William S. Vincent](https://djangoforbeginners.com/)**
  _Excellent book that helped me understand Django structure_

- **[Django Girls Tutorial](https://tutorial.djangogirls.org/)**
  _Great introduction to Django basics_

- **[Real Python Django Tutorials](https://realpython.com/tutorials/django/)**
  _In-depth tutorials on various Django topics_

#### Django Allauth (Authentication)

- **[Django-allauth Documentation](https://docs.allauth.org/)**
  _Official documentation for the authentication system_

- **[Django Allauth Tutorial by LearnDjango](https://learndjango.com/tutorials/django-allauth-tutorial)**
  _Helpful tutorial for implementing user authentication_

#### Deployment Resources

- **[Heroku Django Deployment Guide](https://devcenter.heroku.com/articles/django-app-configuration)**
  _Official Heroku guide for deploying Django apps_

- **[WhiteNoise Documentation](https://whitenoise.readthedocs.io/)**
  _Documentation for serving static files in production_

### Code Institute

- **Code Institute Course Materials**
  _The foundation of my learning journey_

- **Code Institute Student Support**
  _Always available when I needed help_

### Community Support

- **Stack Overflow**
  _For countless solutions to coding problems_

- **Django Forum**
  _Helpful community discussions_

- **Reddit r/django**
  _Community advice and best practices_

### Design Inspiration

- **[Dribbble](https://dribbble.com/)**
  _Design inspiration for UI/UX_

- **[Behance](https://www.behance.net/)**
  _More design references_

### Media & Assets

- **[Unsplash](https://unsplash.com/)**
  _Free high-quality images_

- **[Font Awesome](https://fontawesome.com/)**
  _Icons used throughout the site_

- **[Google Fonts](https://fonts.google.com/)**
  _Typography_

### Testing & Feedback

Thank you to everyone who tested Game Abyss and provided valuable feedback:

- **Friends and Family** – For testing on different devices
- **Code Institute Peers** – For peer review and suggestions
- **Fellow Students** – For constructive criticism and ideas

### Special Thanks

A huge thank you to:

- **[Code Institute](https://codeinstitute.net/)** – For the amazing course and support
- **My Mentor** – For guidance and code reviews throughout the project
- **Student Care Team** – For always being supportive and helpful
- **Slack Community** – For answering questions and sharing knowledge

### Personal Note

Building Game Abyss has been an incredible learning experience. Coming from my previous Phaser game project ([Dungeon Escape!](https://github.com/Drake-Designer/Dungeon-Escape)), this Django application represents my growth as a developer.

While Dungeon Escape! taught me JavaScript and game development, Game Abyss introduced me to backend development, databases, user authentication, and deployment — skills that have opened up a whole new world of possibilities!

I'm excited to continue learning and building more projects in the future! 🚀

---

<div align="center">
  <p><strong>Game Abyss</strong> • Built with ❤️ by <a href="https://github.com/Drake-Designer">Drake-Designer</a></p>
  <p><em>Milestone Project 4 - Code Institute</em></p>
</div>
