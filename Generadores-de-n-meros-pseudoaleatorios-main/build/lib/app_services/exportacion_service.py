import csv
from tkinter import filedialog, messagebox


class ExportacionService:
    @staticmethod
    def exportar_treeview_csv(treeview, columnas, sugerido):
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
