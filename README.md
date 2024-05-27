![Django CI](https://github.com/nico-fst/checkmathe/actions/workflows/django.yml/badge.svg)
![Gitguardian Scan](https://github.com/nico-fst/checkmathe/actions/workflows/gitguardian.yml/badge.svg)
![Docker Image CI](https://github.com/nico-fst/checkmathe/actions/workflows/docker-image.yml/badge.svg)

![django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![drf](https://img.shields.io/badge/django%20rest-ff1709?style=for-the-badge&logo=django&logoColor=white)

![sqlite](https://img.shields.io/badge/Sqlite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

# CheckMathe.de
A website for students and teachers of tutorings to come together and start learning with overhead converging to 0.


# Usage

## Set up

### 1 Databases

1. Set up an empty PostgreSQL DB and remember its connection data ([Starting Tutorial](https://www.youtube.com/watch?v=4VGzRYF3q-o), but with a few tweaks: TODO link Obsidian Tutorial).
2. Set up an AWS S3 Bucket and remember its connection data ([Tutorial](https://www.youtube.com/watch?v=Ko52pn1KXS0)).

### 2 Locally

1. Create venv: ```python3 -m venv venv```
2. Activate venv: ```source venv/bin/activate```
3. Install dependencies: ```pip3 install -r requirements.txt```
4. Create an .env in the project's root folder and fill it using the exact following structure:

```js
SECRET_KEY="django_secret_key"

PERSONAL_TEACHER_CODE="code_that_marks_new_user_as_teacher"

DB_NAME="name_of_postgres_db"
DB_USER="user_having_access_to_db"
DB_PASSWORD="ens_password"
DB_HOST="host_if_remote"

AWS_STORAGE_BUCKET_NAME="bucket_name_of_s3"
AWS_S3_REGION_NAME="region"
AWS_ACCESS_KEY_ID="access_key"
AWS_SECRET_ACCESS_KEY="secret_access_key"

ALLOWED_HOSTS="where_to_deploy_website"
DEBUG="true_if_in_dev"
```


### 3 Docker Configuration

1. Build Image via  `docker build -t django-docker:0.0.1 .`
2. Create, start (and rebuild) Container via `docker compose up --build`

Start without rebuilding via `docker-compose up`


## Execution

### Run in Development

Start server via ```python manage.py runserver```


### Debugging and Testing

- Locally execute the tests via ```python manage.py test```

# References

A collection of tutorials that I found to be quite precise:
- [YT: GitHub Pipeline (Postgres)](https://youtu.be/AU-mYipmtnc?feature=shared)
- [YT: Setting up S3 with Django](https://www.youtube.com/watch?v=Ko52pn1KXS0)
- [YT: Setting up PostgreSQL with Django](https://www.youtube.com/watch?v=4VGzRYF3q-o)