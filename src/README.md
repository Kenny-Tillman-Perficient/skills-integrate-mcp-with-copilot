# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teacher login with protected sign-up and unregister workflows

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Configure teacher credentials and a session-signing secret in the server environment. Do not commit these values or put them in a checked-in file:

   ```
   export TEACHER_CREDENTIALS='{"teacher":"replace-with-a-strong-password"}'
   export SESSION_SECRET='replace-with-a-long-random-secret'
   ```

   `TEACHER_CREDENTIALS` is a JSON object mapping teacher usernames to passwords. Use your deployment platform's secret manager for production. Set `COOKIE_SECURE=true` when serving the site over HTTPS; leave it unset for local HTTP development.

3. Run the application:

   ```
   python app.py
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| GET    | `/auth/status`                                                    | Check whether the current browser has a teacher session              |
| POST   | `/auth/login`                                                     | Log in using a configured teacher username and password              |
| POST   | `/auth/logout`                                                    | End the current browser's teacher session                            |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Teacher-only activity registration                                   |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher-only activity unregister                                    |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.

Teacher credentials are configured through `TEACHER_CREDENTIALS` and are not stored in the repository. Teacher sessions use an HTTP-only, same-site cookie signed with `SESSION_SECRET`.
