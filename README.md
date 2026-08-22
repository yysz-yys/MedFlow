后端：
cd MedFlow-backend
python -m venv venv
pip install -r requirements.txt
cd MedFlow-backend && venv\Scripts\activate 
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001


前端：
cd E:\MedFlow\MedFlow-frontend
pnpm approve-builds     
pnpm --filter admin dev
pnpm --filter doctor dev
pnpm --filter patient dev