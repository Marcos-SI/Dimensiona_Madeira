pip install -r requirements.txt
python manage.py migrate
python manage.py collecstatic --noiput
python seed.py