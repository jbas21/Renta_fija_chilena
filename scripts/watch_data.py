import os
import sys
import time
import shutil
import subprocess
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class DataFolderEventHandler(FileSystemEventHandler):
    """Handle file system events for the data folder."""

    def __init__(self, data_dir):
        super().__init__()
        self.data_dir = data_dir
        self.processed_dir = os.path.join(os.path.dirname(data_dir), 'processed_data')
        os.makedirs(self.processed_dir, exist_ok=True)

    def on_created(self, event): # maneja archivos nuevos creados en la carpeta data
        if event.is_directory:
            return

        file_path = os.path.abspath(event.src_path)
        relative_path = os.path.relpath(file_path, self.data_dir)
        print(f"Nuevo archivo agregado a data: {relative_path}")

        if file_path.lower().endswith('.xlsx'):
            print("Se detectó un archivo Excel. Ejecutando crear_db.py para actualizar la base de datos...")
            self._process_file(file_path)

    def on_moved(self, event):  # maneja archivos movidos a la carpeta data, lo que es útil si se mueven archivos desde otra ubicación en lugar de copiarlos directamente
        if event.is_directory:
            return

        dest_path = os.path.abspath(event.dest_path)
        if os.path.commonpath([dest_path, self.data_dir]) == self.data_dir:
            relative_path = os.path.relpath(dest_path, self.data_dir)
            print(f"Archivo movido a data: {relative_path}")

            if dest_path.lower().endswith('.xlsx'):
                print("Se detectó un archivo Excel movido a data. Ejecutando crear_db.py para actualizar la base de datos...")
                self._process_file(dest_path)

    def _process_file(self, file_path): # procesa el archivo
        if self._run_crear_db():
            self._move_file_to_processed(file_path)

    def _run_crear_db(self): #ejecuta crear_db.py para actualizar la base de datos
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        crear_db_path = os.path.join(base_dir, 'scripts', 'crear_db.py')

        try:
            subprocess.run([sys.executable, crear_db_path], check=True)
            print("crear_db.py se ejecutó correctamente.")
            return True
        except subprocess.CalledProcessError as error:
            print(f"Error al ejecutar crear_db.py: {error}")
            return False

    def _move_file_to_processed(self, file_path): # mueve el archivo a processed_data después de procesarlo
        filename = os.path.basename(file_path)
        destination = os.path.join(self.processed_dir, filename)
        destination = self._unique_destination(destination)

        try:
            shutil.move(file_path, destination)
            relative_dest = os.path.relpath(destination, self.processed_dir)
            print(f"Archivo movido a carpeta de procesados: {relative_dest}")
        except OSError as error:
            print(f"Error al mover el archivo a procesados: {error}")

    def _unique_destination(self, destination): # evita que se sobrescriban archivos en processed_data
        if not os.path.exists(destination):
            return destination

        base, ext = os.path.splitext(destination)
        counter = 1
        while True:
            candidate = f"{base}_{counter}{ext}"
            if not os.path.exists(candidate):
                return candidate
            counter += 1


def main():# función principal para iniciar el watcher
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(base_dir, 'data')

    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"No se encontró la carpeta de datos: {data_dir}")

    event_handler = DataFolderEventHandler(data_dir)
    observer = Observer()
    observer.schedule(event_handler, path=data_dir, recursive=False)
    observer.start()

    print(f"Observando la carpeta: {data_dir}")
    print("Presiona Ctrl+C para detener.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Deteniendo el watcher...")

    observer.join()


if __name__ == '__main__':# ejecuta la función principal para iniciar el watcher
    main()
