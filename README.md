# Household-Services-app

## How to Run

- Clone the repository.
  
  ```shell
  https://github.com/saket-kumar14/Music_streaming_app
  ```
- Run
  ```shell
  python3 app.py
  ```

## Description

This is a music streaming platform designed for seamless audio content delivery. The app supports role-based authentication, distinguishing between admins, creators (artists), and customers (listeners).

- User Roles:

Admin: Manages platform operations, user accounts, and content moderation.
Creators (Artists): Upload, manage, and modify their own music content.
Customers (Listeners): Browse, stream, and create playlists from available music.

- Core Functionalities:

CRUD Operations: Users can create, read, update, and delete content based on their roles.
Music Library Management: Creators can upload and organize tracks.
Streaming Support: Customers can play music with a user-friendly interface.
Personalized Playlists: Users can curate and manage their own playlists.
Search & Discover: Advanced search and recommendation features.

## Frameworks Used

Backend – Python-Flask , flask_sqlalchemy, matplotlib
Database - SQLite
Frontend - HTML, CSS, JS
Jinja2 Render_template – for rendering HTML pages,
Redirect - redirecting, url_for - for HTML templates,
Request - to fetch data from forms/input fields,

## API Design

CRUD: Implementation of all tables 
With Role Based Authentication 
Services – Create, Edit, Delete (Exclusive for Admin).
GET - Read, POST - Create, UPDATE, DELETE
