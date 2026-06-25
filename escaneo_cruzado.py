import os
import subprocess
import sys

def verificar_e_instalar_herramientas():
    print("[*] Verificando herramientas básicas...")
    # Asegurar pip y dependencias de compilación para holehe
    subprocess.run(["pkg", "install", "python", "git", "clang", "make", "libjpeg-turbo", "-y"], stdout=subprocess.DEVNULL)
    
    # Instalar Holehe si no existe
    try:
        import holehe
        print("[✓] Holehe ya está instalado.")
    except ImportError:
        print("[*] Instalanado Holehe mediante pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "holehe"])

    # Instalar Sherlock si no existe la carpeta
    if not os.path.exists("sherlock"):
        print("[*] Clonando e instalando Sherlock...")
        subprocess.run(["git", "clone", "https://github.com/sherlock-project/sherlock.git"])
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "sherlock/requirements.txt"])
    else:
        print("[✓] Sherlock ya está listo en su directorio.")

def ejecutar_herramientas(target_user, target_email):
    print("\n" + "="*40)
    print(f" Lanzando Sherlock para el usuario: {target_user}")
    print("="*40)
    
    # Ejecutar Sherlock
    if target_user:
        cmd_sherlock = f"python3 sherlock/sherlock {target_user} --timeout 2 | tee reporte_sherlock_{target_user}.txt"
        os.system(cmd_sherlock)
    
    print("\n" + "="*40)
    print(f" Lanzando Holehe para el correo: {target_email}")
    print("="*40)
    
    # Ejecutar Holehe
    if target_email:
        cmd_holehe = f"holehe {target_email} --only-used | tee reporte_holehe_{target_email}.txt"
        os.system(cmd_holehe)

if __name__ == "__main__":
    # 1. Asegurar entorno
    verificar_e_instalar_herramientas()
    
    # 2. Análisis rápido del txt anterior para guiar al usuario
    print("\n[i] Extrayendo dorks clave de tu resultado.txt previo:")
    if os.path.exists("resultado.txt"):
        with open("resultado.txt", "r") as f:
            lineas = f.readlines()
            # Mostrar solo los dorks principales de redes sociales para abrirlos rápido
            for linea in lineas:
                if "site%3Afacebook.com" in linea or "site%3Alinkedin.com" in linea:
                    print(f" -> Link de búsqueda: {linea.strip().replace('URL: ', '')}")
    else:
        print(" [!] No se encontró el archivo resultado.txt en esta carpeta.")

    print("\n" + "-"*50)
    print("Introduce los datos que hayas descubierto al abrir los links de PhoneInfoga:")
    user = input("=> Nombre de usuario / Alias para Sherlock (ej: juanito98): ").strip()
    email = input("=> Correo electrónico completo para Holehe (ej: juan@gmail.com): ").strip()
    
    if user or email:
        ejecutar_herramientas(user, email)
        print("\n[✓] Escaneos finalizados. Reportes guardados como 'reporte_sherlock_*.txt' y 'reporte_holehe_*.txt'")
    else:
        print("[!] No ingresaste ningún objetivo para escanear.")

