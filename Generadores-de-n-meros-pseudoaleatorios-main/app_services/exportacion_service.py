import csv
from tkinter import filedialog, messagebox


class ExportacionService:
    """
    Servicio para exportar datos de widgets Treeview a archivos CSV.

    Proporciona funcionalidad estática para exportar datos tabulares desde
    componentes Treeview de Tkinter a archivos CSV con formato estándar.

    Notes
    -----
    - Todos los métodos son estáticos, no requiere instanciación.
    - Abre un diálogo de guardado que el usuario puede cancelar.
    - Usa codificación UTF-8 para que soportar caracteres especiales.
    """

    @staticmethod
    def exportar_treeview_csv(treeview, columnas, sugerido):
        """
        Exporta los datos de un Treeview a un archivo CSV.

        Abre un diálogo de guardado para que el usuario seleccione la ubicación
        del archivo. Los datos se escriben con encabezados de columna basados
        en la lista de columnas proporcionada.

        Parameters
        ----------
        treeview : tkinter.ttk.Treeview
            Widget Treeview que contiene los datos a exportar.
        columnas : list[str]
            Lista con los nombres de las columnas para la fila de encabezados.
        sugerido : str
            Nombre de archivo sugerido en el diálogo de guardado.

        Returns
        -------
        None
            Si el usuario cancela el diálogo, no se exporta nada.
            Si la exportación es exitosa, muestra un mensaje de confirmación.

        Notes
        -----
        - El archivo se crea con encoding UTF-8.
        - Sobrescribe el archivo si ya existe.
        - Las filas se extraen llamando a `treeview.item(item)["values"]`.
        """
        path = filedialog.asksaveasfilename(
            title="Guardar CSV",
            defaultextension=".csv",
            initialfile=sugerido,
            filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columnas)
            for item in treeview.get_children():
                writer.writerow(treeview.item(item)["values"])

        messagebox.showinfo("Exportacion", f"Archivo generado: {path}")
