![Django CI](https://github.com/nico-fst/checkmathe/actions/workflows/django.yml/badge.svg)
![Gitguardian Scan](https://github.com/nico-fst/checkmathe/actions/workflows/gitguardian.yml/badge.svg)
![Docker Image CI](https://github.com/nico-fst/checkmathe/actions/workflows/docker-image.yml/badge.svg)

![django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![drf](https://img.shields.io/badge/django%20rest-ff1709?style=for-the-badge&logo=django&logoColor=white)

![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

# CheckMathe.de
A website for students and teachers of tutorings to come together and start learning with overhead converging to 0.

View the API docs at /swagger/.


# Structure

The Django application requires
- optonally: a AWS S3 server for uploaded attachments (like PDFs)
View the [documentation](TODO lol).

It can be set up as a container pair (django - db) or using a lightweight sqlite3.


# Setting up

Create the following .env file:

```js
SECRET_KEY="django_secret_key"

PERSONAL_TEACHER_CODE="code_that_marks_new_user_as_teacher"

DB_NAME="name_of_postgres_db"
DB_USER="user_having_access_to_db"
DB_PASSWORD="ens_password"
DB_HOST="OPTIONAL-host_if_remote"
DB_PORT="OPTIONAL-port_if_different"

ALLOWED_HOSTS="where_to_deploy_website"
DEBUG="OPTIONAL-true_if_in_dev"
LOCAL="OPTIONAL-true_if_working_locally_with_attachments_instead_of_on_s3"
```

## A: As Docker Container

Set up an AWS S3 Bucket and remember its connection data ([Tutorial](https://www.youtube.com/watch?v=Ko52pn1KXS0)).

Add the following to the .env:

```js
AWS_STORAGE_BUCKET_NAME="bucket_name_of_s3"
AWS_S3_REGION_NAME="region"
AWS_ACCESS_KEY_ID="access_key"
AWS_SECRET_ACCESS_KEY="secret_access_key"
```

Start Container via `docker-compose up --build -d`.
When shutting system for debugging, remember to reset volumes via `docker-compose down -v`.

## B: Locally

1. Create venv: ```python3 -m venv venv```
2. Activate venv: ```source venv/bin/activate```
3. Install dependencies: ```pip3 install -r requirements.txt```
4. Create an .env in the project's root folder and fill it using the exact following structure:

- Start server via ```python manage.py runserver```
- Locally execute the tests via ```python manage.py test```

---

# References

A collection of tutorials that I found to be quite precise:
- [YT: GitHub Pipeline (Postgres)](https://youtu.be/AU-mYipmtnc?feature=shared)
- [YT: Setting up S3 with Django](https://www.youtube.com/watch?v=Ko52pn1KXS0)
- [YT: Setting up PostgreSQL with Django](https://www.youtube.com/watch?v=4VGzRYF3q-o)
- [YT: Using Github Environments](https://www.youtube.com/watch?v=5XfgT9A9PHw)
