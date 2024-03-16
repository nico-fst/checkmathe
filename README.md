![Django CI](https://github.com/nico-fst/checkmathe/actions/workflows/django.yml/badge.svg)
![Gitguardian Scan](https://github.com/nico-fst/checkmathe/actions/workflows/gitguardian.yml/badge.svg)

![django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![drf](https://img.shields.io/badge/django%20rest-ff1709?style=for-the-badge&logo=django&logoColor=white)

![sqlite](https://img.shields.io/badge/Sqlite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

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

Deactivate venv: ```deactivate```

# Run

1. In your local .env, define your Django ```SECRET_KEY```
2. Start server: ```python manage.py runserver```

Manually test the project: ```python manage.py test```
