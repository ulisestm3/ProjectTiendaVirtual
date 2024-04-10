1. Para usar entorno virtual en Windows:
    Para solucionar este problema, puedes cambiar temporalmente la política de ejecución de scripts para permitir la activación de entornos virtuales. Sigue estos pasos:

    Abre PowerShell como administrador o la terminal de VSCODE.

    Ejecuta el siguiente comando para cambiar la política de ejecución:

    powershell
    
    Set-ExecutionPolicy RemoteSigned -Scope Process

    Este comando establece la política de ejecución actual para permitir la ejecución de scripts firmados localmente, lo que debería permitir la activación del entorno virtual.

    Ahora, intenta activar el entorno virtual nuevamente utilizando el comando:
    bash
    
    myenv\Scripts\activate
    Con esto, deberías poder activar tu entorno virtual y continuar con la configuración de tu proyecto Flask en Windows. Una vez que hayas terminado, recuerda restaurar la política de ejecución de scripts a su valor original si así lo deseas ejecutando el comando:

    powershell
    Set-ExecutionPolicy Default -Scope Process

    Es importante tener en cuenta que cambiar la política de ejecución de scripts puede tener implicaciones en la seguridad de tu sistema, así que asegúrate de entender los riesgos asociados antes de hacerlo.

