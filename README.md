![Django CI](https://github.com/nico-fst/checkmathe/actions/workflows/django.yml/badge.svg)
![Gitguardian Scan](https://github.com/nico-fst/checkmathe/actions/workflows/gitguardian.yml/badge.svg)
![Docker Image CI](https://github.com/nico-fst/checkmathe/actions/workflows/docker-image.yml/badge.svg)

![django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![drf](https://img.shields.io/badge/django%20rest-ff1709?style=for-the-badge&logo=django&logoColor=white)

![sqlite](https://img.shields.io/badge/Sqlite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

# checkmathe
conceptual website for students to book and manage tutorings

# Docker Configuration
1. Build Image via  `docker build -t django-docker:0.0.1 .`
2. Create, start (and rebuild) Container via `docker compose up --build`

Start without rebuilding via `docker-compose up`

# Installation

1. Create venv: ```python3 -m venv venv```
2. Activate venv: ```source venv/bin/activate```
3. Install dependencies: ```pip3 install -r requirements.txt```
4. Create an .env in the project's root folder and fill it using the exact following structure:

```
PERSONAL_TEACHER_CODE="code_when_registering_as_teacher"
DB_NAME="name_of_your_db"
DB_USER="name_of_db_user"
DB_PASSWORD="password_of_db_user"
```

# Run

Start server via ```python manage.py runserver```


# Debugging and Tesing

- Locally execute the tests via ```python manage.py test```
<!--TODO - Locally test the Github Workflows via *act*  -->