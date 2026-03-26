import re


class SemillasService:
    """
    Servicio para parsear y leer semillas iniciales desde texto o archivos.

    Proporciona métodos para extraer valores numéricos enteros desde
    cadenas de texto con diversos separadores (comas, espacios, puntos y comas).

    Notes
    -----
    - Todos los métodos son estáticos, no requiere instanciación.
    - Compatible con múltiples formatos de entrada y separadores.
    - Utiliza expresiones regulares para una tokenización robusta.
    """

    @staticmethod
    def parsear_texto(texto):
        """
        Extrae valores enteros de una cadena de texto con separadores múltiples.

        Tokeniza la entrada usando expresiones regulares que reconocen comas,
        espacios y puntos y comas como separadores, y convierte cada token
        válido a entero.

        Parameters
        ----------
        texto : str
            Cadena de entrada con valores numéricos separados.
            Ejemplo: '123, 456; 789 1000'.

        Returns
        -------
        list[int]
            Lista con los valores enteros extraídos en orden.
            Ignora espacios en blanco y tokens vacíos.

        Raises
        ------
        ValueError
            Si algún token no puede convertirse a entero.
        """
        tokens = re.split(r"[,\s;]+", texto.strip())
        semillas = []
        for token in tokens:
            if token == "":
                continue
            semillas.append(int(token))
        return semillas

    @classmethod
    def leer_archivo(cls, path):
        """
        Lee y parsea semillas desde un archivo de texto.

        Abre un archivo, lee su contenido completo y lo procesa
        usando parsear_texto() para extraer los valores enteros.

        Parameters
        ----------
        path : str
            Ruta al archivo a leer (debe existir).
            Encoding: UTF-8.

        Returns
        -------
        list[int]
            Lista de valores enteros extraídos del archivo.

        Raises
        ------
        FileNotFoundError
            Si el archivo no existe.
        ValueError
            Si los valores no pueden convertirse a enteros.
        """
        with open(path, "r", encoding="utf-8") as f:
            contenido = f.read()
        return cls.parsear_texto(contenido)
