import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener la URI de conexión a PostgreSQL
# Si no existe, se define una conexión por defecto para evitar fallas catastróficas durante las pruebas de integración.
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "sia_t_db")

# Construir la URL de conexión
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Para ambientes de desarrollo o pruebas sin PostgreSQL real levantado,
# podemos soportar opcionalmente SQLite en memoria como fallback automático.
# Así, el código ETL y el backend pueden ser probados y compilados de forma segura.
if os.getenv("USE_SQLITE_FALLBACK", "true").lower() == "true":
    DATABASE_URL = "sqlite:///./sia_t_local.db"
    # SQLite requiere parámetros adicionales para el manejo de hilos concurrentes
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)

# Crear fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base declarativa para mapear modelos ORM (si se desea usar SQLAlchemy)
Base = declarative_base()

def get_db():
    """
    Dependency helper para obtener una sesión de base de datos limpia.
    Se encarga de cerrar la sesión automáticamente tras completar la transacción/request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """
    Prueba rápida de ping para comprobar la salud de la conexión a la base de datos.
    """
    try:
        with engine.connect() as conn:
            print("=== CONEXIÓN EXITOSA A LA BASE DE DATOS SIA-T ===")
            print(f"Engine binded to: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
            return True
    except Exception as e:
        print("=== ERROR DE CONEXIÓN A LA BASE DE DATOS ===")
        print(f"Detalle del error: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
