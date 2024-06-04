# Social Media API

API service for social media platform management built using Django Rest Framework (DRF).

## Installation

To run this project locally, follow these steps:

1. Clone the repository:

```shell
git clone https://github.com/your-username/social-media-api.git
cd social-media-api
python -m venv venv
source venv/bin/activate   # On Windows, use 'venv\Scripts\activate'
pip install -r requirements.txt

createdb social_media_db

export DB_HOST=localhost
export DB_NAME=social_media_db
export DB_USER=your_db_username
export DB_PASSWORD=your_db_password
export SECRET_KEY=your_secret_key

python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## Usage

Once the server is running, you can access the API endpoints using tools like Postman or curl. 
* The API documentation is available at /api/doc/swagger/.

## Features

 * JWT authentication
 * User authentication, registration, and profile management
 * Post creation, retrieval, update, and deletion
 * Like and comment functionalities for posts
 * Follow and unfollow users
 * Search users and posts
 * Retrieve own posts and following posts
