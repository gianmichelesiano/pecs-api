cd backend


python app/backend_pre_start.py    
alembic upgrade head 

fastapi run --reload --port 5000 app/main.py

cd backend

python -m alembic revision --autogenerate -m "Add_pictogram_table"

python -m alembic upgrade head

docker-compose -f docker-compose-backend.yml up