# ReqManager: Requirements Management System

## Overview

ReqManager is a comprehensive Django-based web application designed to help teams manage software requirements effectively. It provides robust features for tracking, organizing, and collaborating on project requirements.

## Features

- 📋 Project and Organization Management
- 🔍 Detailed Requirement Tracking
- 📊 Requirement Status and Priority Tracking
- 🔗 Requirement Traceability Matrix
- 📈 Requirement History and Versioning
- 🎯 Project Objectives Alignment

## Tech Stack

- Django 5.1.7
- Python 3.9+
- SQLite (development)
- Bootstrap 5
- Chart.js
- Django Filters

## Prerequisites

- Python 3.9 or higher
- pip
- virtual environment (recommended)

## Installation

1. Clone the repository
```bash
git clone https://github.com/avishekpaul1310/reqmanager.git
cd reqmanager
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run migrations
```bash
python manage.py migrate
```

5. Create a superuser
```bash
python manage.py createsuperuser
```

6. Run the development server
```bash
python manage.py runserver
```

## Running Tests

```bash
python manage.py test
```

## Configuration

Key settings are in `reqmanager/settings.py`. For production, remember to:
- Set `DEBUG = False`
- Update `SECRET_KEY`
- Configure database settings
- Set up static and media file hosting

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Avishek Paul - avishek-paul@outlook.com

Project Link: [https://github.com/avishekpaul1310/reqmanager](https://github.com/yourusername/reqmanager)

## Acknowledgements

- Django
- Bootstrap
- Chart.js
