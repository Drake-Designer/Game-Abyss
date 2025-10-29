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

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features in Plain English](#features)
3. [How I Split the Project into Apps](#how-i-split-the-project-into-apps)
4. [Crafted With Care](#crafted-with-care)
5. [Tested With Real Players](#tested-with-real-players)
6. [Installed Apps](#installed-apps)
7. [User Experience Design](#user-experience-design)
    - [User Stories](#user-stories)
    - [Structure](#structure)
    - [Design](#design)
        - [Wireframes](#wireframes)
        - [Colour Palette](#colour-palette)
        - [Typography](#typography)
8. [Features](#features)
    - [Existing Features](#existing-features)
9. [Database Design](#database-design)
10. [Technologies Used](#technologies-used)
11. [Testing and Bug Fixes](#testing-and-bug-fixes)
12. [Deployment](#deployment)
    - [Local Development](#local-development)
    - [Heroku Deployment](#heroku-deployment)
13. [Credits](#credits)

---

<a id="project-overview"></a>

## Project Overview

Welcome to **Game Abyss!**

A modern blog platform designed for the gaming community. Whether you're a casual player or a hardcore gamer, Game Abyss is your space to:

> Share your thoughts, read reviews, and connect with fellow gamers from around the world!

### The Story Behind Game Abyss

Here's the truth: **I've wanted to create a gaming blog for ages!**

For years, I've been thinking: _"Wouldn't it be cool to have my own gaming community where people can share reviews, discuss their favorite games, and just... talk about gaming?"_ But I never knew where to start or how to build it.

Then came my journey with **Python and Django** through the Code Institute course, and suddenly everything clicked! 🎯

I realized: _"Wait a minute... I'm literally learning exactly what I need to build that blog I've always wanted!"_

So instead of creating just another practice project to tick off the assessment requirements, I thought: **"Why not make this count? Why not build something I actually care about and can continue developing after graduation?"**

And that's how Game Abyss was born! 🚀

This project is my way of combining:

- ✅ My passion for gaming (I've been a gamer since I was a kid!)
- ✅ My newly acquired Python and Django skills
- ✅ My long-term dream of running a gaming community
- ✅ A real-world portfolio project I'm genuinely proud of

The best part? This isn't just a one-and-done academic project. I'm already planning features to add after I submit this (comments system, user profiles, game reviews database, maybe even an API!). Game Abyss is just getting started! 💪

### Key Features

- **User Authentication**: Secure registration, login, and password reset functionality powered by Django-allauth
- **Professional Email System**: Real password reset emails via SendGrid (not just console output!)
- **Responsive Design**: Fully responsive interface that works beautifully on all devices
- **Admin Dashboard**: Comprehensive Django admin panel for content management
- **Modern Dark Theme**: Gaming-inspired design with custom CSS variables
- **Production-Ready**: Deployed on Heroku with PostgreSQL database

### What's Coming Next (Future Features)

Because I plan to keep working on this after graduation:

- **Blog System**: Full CRUD functionality for creating and managing blog posts
- **Comment System**: Let users discuss and engage with each other's posts
- **User Profiles**: Personalized profile pages showing user activity and posts
- **Like/Favorite System**: Save your favorite posts and show appreciation
- **Search & Filter**: Find posts by game title, genre, or keywords
- **Game Database Integration**: Pull game info from APIs like RAWG or IGDB

### Target Audience

Game Abyss is built for:

- **Gamers** who want to share their gaming experiences and opinions
- **Players** looking for honest reviews and recommendations from real people
- **Gaming enthusiasts** who enjoy community discussions and debates
- **Content creators** who want a platform for their gaming content
- **Anyone** who loves games and wants to be part of a friendly community

---

<a id="features"></a>

## Features

When I started drawing the first wireframes, I imagined how a fellow gamer would move through the site on a quiet Sunday afternoon. Every feature grew out of that story:

- **Warm landing page** – The hero banner greets visitors with the latest highlights so nobody feels lost when they arrive.
- **Simple registration and login** – Powered by Django Allauth, signing up feels familiar and safe, and password reset emails actually arrive in real inboxes.
- **Blog publishing tools** – Authors can create, edit, and tidy up posts with Summernote’s friendly text editor, while draft and publish states keep work-in-progress pieces private.
- **Gallery corner** – Screenshots, fan art, and cover artwork live in their own gallery so visual stories stand next to written ones.
- **Content moderation dashboard** – Staff users can review submissions, approve comments, and tune the home page through Django’s admin (styled with Jazzmin so it feels modern).
- **Responsive layout** – I tested the layout on desktop, tablet, and mobile so buttons stay tappable and text remains readable everywhere.
- **Performance touches** – Cloudinary handles media files, Whitenoise serves static assets quickly, and PostgreSQL keeps everything stable on Heroku.

---

<a id="how-i-split-the-project-into-apps"></a>

## How I Split the Project into Apps

- **`core`**: global settings, error pages, shared templates
- **`accounts`**: authentication, Django Allauth integration
- **`pages`**: static pages like About and Contact
- **`blog`**: posts, categories, featured content
- **`gallery`**: images, fan art, media embeds

---

<a id="crafted-with-care"></a>

## Crafted With Care

Designing Game Abyss felt a lot like polishing a favourite controller: I obsessed over micro-interactions, made sure focus states are visible for keyboard users, kept headings consistent, and tweaked colour contrasts until they looked right on both dark and bright screens.

---

<a id="tested-with-real-players"></a>

## Tested With Real Players

Real testers (staff and normal users) tried to break forms, upload content, and gave feedback. Their input shaped polish decisions and made the site sturdier.

---

<a id="installed-apps"></a>

## Installed Apps I Chose

- **Django**
- **django-allauth**
- **django-crispy-forms** + **crispy-bootstrap5**
- **django-summernote**
- **django-cloudinary-storage** + **cloudinary**
- **whitenoise**
- **gunicorn**
- **psycopg2-binary** + **dj-database-url**
- **django-debug-toolbar**
- **django-jazzmin**
- **django-widget-tweaks**
- **sendgrid** + **python-http-client**
- **pillow**
- **djlint** and **prettier**

---

<a id="user-experience-design"></a>

## User Experience Design

<a id="user-stories"></a>

### User Stories

#### As a Visitor

- Browse posts without account
- Read reviews and articles
- Navigate easily
- Register to join community

#### As a Registered User

- Register, login, reset password
- Create, edit, delete posts
- Comment on posts
- Customize profile
- Delete account

#### As an Admin

- Manage all content
- Moderate posts/comments
- Manage users
- Configure site settings

<a id="structure"></a>

### Structure

Site layout, navigation, blog system, authentication.

<a id="design"></a>

### Design

<a id="wireframes"></a>

#### Wireframes

Created with Balsamiq.

<a id="colour-palette"></a>

#### Colour Palette

Dark theme with primary `#ff6b35` and secondary `#4ecdc4`.

<a id="typography"></a>

#### Typography

Google Fonts: Inter + Roboto Mono.

---

<a id="features"></a>

## Features

<a id="existing-features"></a>

### Existing Features

- Homepage hero + latest posts
- Blog CRUD
- User auth
- Email system
- Dark theme
- Security

<a id="database-design"></a>

## Database Design

PostgreSQL in production, SQLite in development.

---

<a id="technologies-used"></a>

## Technologies Used

Backend: Django, PostgreSQL
Frontend: HTML, CSS, JS, Bootstrap
Packages: django-allauth, crispy-forms, summernote, pillow, whitenoise, etc.
Tools: Git, GitHub, Heroku, Balsamiq

---

<a id="testing-and-bug-fixes"></a>

## Testing and Bug Fixes

Validation (HTML, CSS, JS, Python), Lighthouse, user testing.
Key bugs: static files fix with WhiteNoise, DB connection with dj-database-url.
Browser autoplay limitation explained.

---

<a id="deployment"></a>

## Deployment

<a id="local-development"></a>

### Local Development

Clone, venv, install, migrate, createsuperuser, runserver.

<a id="heroku-deployment"></a>

### Heroku Deployment

Create app, add Postgres, config vars, push, migrate, collectstatic.

---

<a id="credits"></a>

## Credits

Resources: Django docs, tutorials, Stack Overflow, Code Institute, peers.
Design inspiration: Dribbble, Behance.
Media: Unsplash, Font Awesome, Google Fonts.
Testers: friends, family, CI peers.

---

<div align="center">
  <p><strong>Game Abyss</strong> • Built with ❤️ by <a href="https://github.com/Drake-Designer">Drake-Designer</a></p>
  <p><em>Milestone Project 3 - Code Institute</em></p>
</div>
