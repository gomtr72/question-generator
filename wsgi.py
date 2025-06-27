# wsgi.py

from app import create_app

application = create_app()
app = application  # gunicorn에서 사용할 app 변수 명시적 선언

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8000)
