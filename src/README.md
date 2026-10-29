# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Display active school announcements
- Create, edit, and delete announcements when signed in as a teacher

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/activities` | Get activities with their details and current participant count |
| POST | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity |
| GET | `/announcements` | Get announcements that are currently active |
| POST | `/auth/login?username=…&password=…` | Sign in and receive a bearer token |
| GET | `/auth/check-session` | Validate the bearer-token session |
| POST | `/auth/logout` | Revoke the bearer-token session |
| GET | `/announcements/manage` | List all announcements (requires `Authorization: Bearer <token>`) |
| POST | `/announcements/manage` | Create an announcement (requires bearer token) |
| PUT | `/announcements/manage/{announcement_id}` | Update an announcement (requires bearer token) |
| DELETE | `/announcements/manage/{announcement_id}` | Delete an announcement (requires bearer token) |

## Data Model

Announcements are stored in the MongoDB `announcements` collection. Each record contains:

- `title` and `message`
- Optional `start_date` in `YYYY-MM-DD` format
- Required `expiration_date` in `YYYY-MM-DD` format

The application inserts an example announcement when the collection is empty. Public visitors only see announcements whose start date has arrived and expiration date has not passed. Any signed-in teacher can manage announcements; sessions expire after seven days.
