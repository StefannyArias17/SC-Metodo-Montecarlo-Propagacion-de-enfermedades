import re


class SemillasService:
    @staticmethod
    def parsear_texto(texto):
        tokens = re.split(r"[,\s;]+", texto.strip())
        semillas = []
        for token in tokens:
            if token == "":
                continue
            semillas.append(int(token))
        return semillas

    @classmethod
    def leer_archivo(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            contenido = f.read()
        return cls.parsear_texto(contenido)
