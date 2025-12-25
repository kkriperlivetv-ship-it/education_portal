from waitress import serve  # Для Windows
# from gunicorn import ...  # Для Linux
from app import app

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 EDUCATION PORTAL - ПРОДАКШЕН РЕЖИМ")
    print("=" * 50)
    print("📊 Debug: ОТКЛЮЧЕН")
    print("🔒 Режим: ПРОДАКШЕН")
    print("🌐 Доступ: http://0.0.0.0:5000")
    print("=" * 50)
    
    # Для Windows
    serve(app, host='0.0.0.0', port=5000)
    
    # Для Linux (альтернатива):
    # app.run(host='0.0.0.0', port=5000)