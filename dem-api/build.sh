pip install -r requirements.txt
python manager.py migrate
python manage.py collecstatic --noiput
python seed.py