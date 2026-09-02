
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np

DEFAULT_N = 100_000
DEFAULT_BLOCK_ROWS = 256
DTYPE = np.dtype(np.uint8)
OUTPUT_DIR = Path("salida")


def human_bytes(num_bytes: int) -> str:
    gib = num_bytes / (1024**3)
    gb = num_bytes / 1_000_000_000
    return f"{num_bytes:,} bytes = {gb:.2f} GB = {gib:.2f} GiB"


def file_paths(n: int) -> tuple[Path, Path]:
    suffix = "100000x100000" if n == DEFAULT_N else f"{n}x{n}"
    data_path = OUTPUT_DIR / f"matriz_{suffix}_uint8.dat"
    meta_path = OUTPUT_DIR / f"matriz_{suffix}_metadata.json"
    return data_path, meta_path


def expected_file_size(n: int) -> int:
    return n * n * DTYPE.itemsize


def check_free_space(path: Path, required_bytes: int) -> None:
    probe = path if path.exists() else path.parent
    probe.mkdir(parents=True, exist_ok=True)
    usage = os.statvfs(probe) if hasattr(os, "statvfs") else None

    if usage is not None:
        free_bytes = usage.f_bavail * usage.f_frsize
    else:
        import shutil
        free_bytes = shutil.disk_usage(probe).free

    
    recommended = int(required_bytes * 1.05)
    if free_bytes < recommended:
        raise RuntimeError(
            "Espacio insuficiente.\n"
            f"Necesario aprox.: {human_bytes(recommended)}\n"
            f"Disponible:        {human_bytes(free_bytes)}"
        )


def print_progress(done_rows: int, n: int, start_time: float) -> None:
    """Muestra progreso sin imprimir una línea por cada bloque."""
    elapsed = max(perf_counter() - start_time, 1e-9)
    percent = (done_rows / n) * 100
    written = done_rows * n * DTYPE.itemsize
    speed_mib = (written / (1024**2)) / elapsed
    print(
        f"\rProgreso: {percent:6.2f}% | "
        f"Filas: {done_rows:,}/{n:,} | "
        f"Escrito: {written / 1_000_000_000:6.2f} GB | "
        f"Velocidad media: {speed_mib:7.1f} MiB/s",
        end="",
        flush=True,
    )


def create_matrix(n: int, block_rows: int) -> None:
    """Crea la matriz en disco usando bloques pequeños de memoria.

    No se crea nunca un arreglo de n x n en RAM. Solo existe un bloque de
    `block_rows x n` elementos. Con n=100.000 y block_rows=256, el bloque
    principal ocupa aproximadamente 25,6 MB.
    """
    if n <= 0:
        raise ValueError("n debe ser mayor que 0")
    if block_rows <= 0:
        raise ValueError("block_rows debe ser mayor que 0")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data_path, meta_path = file_paths(n)
    total_bytes = expected_file_size(n)

    print("\n=== CREACIÓN DE MATRIZ ===")
    print(f"Dimensiones: {n:,} x {n:,}")
    print(f"Tipo:       {DTYPE.name} ({DTYPE.itemsize} byte por elemento)")
    print(f"Archivo:    {data_path}")
    print(f"Tamaño:     {human_bytes(total_bytes)}")
    print(f"Bloque:     hasta {block_rows:,} filas (~{block_rows * n / 1_000_000:.1f} MB de datos)\n")

    check_free_space(data_path, total_bytes)


    columns_mod = (np.arange(n, dtype=np.uint64) & 0xFF).astype(np.uint8)[None, :]
    sha256 = hashlib.sha256()
    start_time = perf_counter()
    last_progress = -1

    
    with open(data_path, "wb") as fh:
        for start_row in range(0, n, block_rows):
            end_row = min(start_row + block_rows, n)
            rows_in_block = end_row - start_row

            rows_mod = (
                np.arange(start_row, end_row, dtype=np.uint64) & 0xFF
            ).astype(np.uint8)[:, None]

            block = np.empty((rows_in_block, n), dtype=np.uint8)

           
            np.add(rows_mod, columns_mod, out=block)

            sha256.update(memoryview(block))

           
            block.tofile(fh)

            done = end_row
            progress_int = int(done * 100 / n)
            if progress_int != last_progress or done == n:
                print_progress(done, n, start_time)
                last_progress = progress_int

    elapsed = perf_counter() - start_time
    print("\n")

    actual_size = data_path.stat().st_size
    if actual_size != total_bytes:
        raise RuntimeError(
            f"El archivo quedó con {actual_size:,} bytes y se esperaban {total_bytes:,}."
        )

    metadata = {
        "rows": n,
        "columns": n,
        "dtype": DTYPE.name,
        "bytes_per_element": DTYPE.itemsize,
        "expected_file_size_bytes": total_bytes,
        "pattern": "value[row, column] = (row + column) % 256",
        "block_rows": block_rows,
        "sha256": sha256.hexdigest(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "data_file": data_path.name,
    }
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("Matriz creada correctamente.")
    print(f"Archivo de datos: {data_path}")
    print(f"Metadatos:        {meta_path}")
    print(f"SHA-256:          {metadata['sha256']}")
    print(f"Tiempo total:     {elapsed:.2f} s")


def load_memmap(n: int) -> np.memmap:
    data_path, _ = file_paths(n)
    if not data_path.exists():
        raise FileNotFoundError(
            f"No existe {data_path}. Primero ejecuta: python laboratorio1.py crear"
            + ("" if n == DEFAULT_N else f" --n {n}")
        )
    expected = expected_file_size(n)
    actual = data_path.stat().st_size
    if actual != expected:
        raise RuntimeError(
            f"Tamaño incorrecto: {actual:,} bytes; esperado: {expected:,} bytes."
        )
    return np.memmap(data_path, dtype=DTYPE, mode="r", shape=(n, n), order="C")


def show_matrix(n: int) -> None:
    matrix = load_memmap(n)
    r = min(5, n)
    c = min(8, n)
    middle = max(0, n // 2 - r // 2)
    last = max(0, n - r)

    print("\n=== MUESTRA DE LA MATRIZ ===")
    print(f"Forma lógica: {matrix.shape}")
    print(f"dtype:        {matrix.dtype}")
    print("\nPrimer bloque:")
    print(np.asarray(matrix[0:r, 0:c]))

    print("\nBloque del centro:")
    print(np.asarray(matrix[middle : middle + r, middle : middle + c]))

    print("\nÚltimo bloque:")
    print(np.asarray(matrix[last:n, max(0, n - c) : n]))

    print(
        "\nNota: no se imprimen los 10.000 millones de elementos, porque eso sería "
        "impráctico y no demuestra una lectura eficiente. Se consultan únicamente "
        "las zonas necesarias del archivo."
    )


def calculate_full_sha256(path: Path, chunk_size: int = 64 * 1024 * 1024) -> str:
    """Lee el archivo secuencialmente en bloques y calcula SHA-256 sin saturar RAM."""
    digest = hashlib.sha256()
    total = path.stat().st_size
    read_bytes = 0
    start = perf_counter()

    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
            read_bytes += len(chunk)
            percent = read_bytes * 100 / total
            print(f"\rHash completo: {percent:6.2f}%", end="", flush=True)
    print(f"  ({perf_counter() - start:.2f} s)")
    return digest.hexdigest()


def verify_matrix(n: int, full_hash: bool, samples: int) -> None:
    if samples <= 0:
        raise ValueError("samples debe ser mayor que 0")

    data_path, meta_path = file_paths(n)
    matrix = load_memmap(n)

    print("\n=== VERIFICACIÓN ===")
    print("1. Tamaño del archivo: OK")
    print(f"   {human_bytes(data_path.stat().st_size)}")

    rng = np.random.default_rng(seed=20260902)
    sample_count = min(samples, max(1, n * n))
    rows = rng.integers(0, n, size=sample_count, dtype=np.int64)
    cols = rng.integers(0, n, size=sample_count, dtype=np.int64)
    actual = np.asarray(matrix[rows, cols], dtype=np.uint8)
    expected = ((rows + cols) & 0xFF).astype(np.uint8)

    mismatches = np.flatnonzero(actual != expected)
    if mismatches.size:
        idx = int(mismatches[0])
        raise RuntimeError(
            "Contenido incorrecto. Primera diferencia: "
            f"fila={rows[idx]}, columna={cols[idx]}, "
            f"leído={actual[idx]}, esperado={expected[idx]}"
        )

    print(f"2. {sample_count:,} posiciones aleatorias: OK")
    print("   Regla validada: valor = (fila + columna) % 256")

    # Validaciones adicionales en esquinas y centro.
    fixed_points = [
        (0, 0),
        (0, n - 1),
        (n - 1, 0),
        (n - 1, n - 1),
        (n // 2, n // 2),
    ]
    for row, col in fixed_points:
        value = int(matrix[row, col])
        expected_value = (row + col) % 256
        if value != expected_value:
            raise RuntimeError(
                f"Fallo en ({row}, {col}): leído={value}, esperado={expected_value}"
            )
    print("3. Esquinas y centro: OK")

    if full_hash:
        if not meta_path.exists():
            raise FileNotFoundError(
                f"No existe {meta_path}; se necesita para comparar el SHA-256."
            )
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        expected_hash = metadata.get("sha256")
        print("4. Verificación completa SHA-256 (lee todo el archivo):")
        actual_hash = calculate_full_sha256(data_path)
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"SHA-256 diferente.\nEsperado: {expected_hash}\nActual:   {actual_hash}"
            )
        print("   SHA-256: OK")
    else:
        print("4. SHA-256 completo: omitido (opcional).")
        print("   Para ejecutarlo: python laboratorio1.py verificar --hash-completo")

    print("\nResultado: archivo verificado correctamente.")


def show_info(n: int, block_rows: int) -> None:
    total = expected_file_size(n)
    naive_float64 = n * n * np.dtype(np.float64).itemsize
    block_bytes = min(block_rows, n) * n * DTYPE.itemsize

    print("\n=== INFORMACIÓN DEL LABORATORIO ===")
    print(f"Matriz: {n:,} x {n:,} = {n*n:,} elementos")
    print(f"Con float64, una matriz completa requeriría: {human_bytes(naive_float64)}")
    print(f"Con uint8, el archivo final requiere:       {human_bytes(total)}")
    print(f"Bloque principal en RAM:                    {human_bytes(block_bytes)}")
    print("\nLa solución NO crea la matriz completa en RAM.")
    print("La crea por bloques, la escribe secuencialmente y luego la lee con memmap.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Laboratorio 1: matriz grande escrita y leída eficientemente desde disco."
    )
    parser.add_argument(
        "accion",
        choices=["info", "crear", "mostrar", "verificar"],
        help="Operación que se desea realizar.",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=DEFAULT_N,
        help=f"Dimensión NxN. Predeterminado: {DEFAULT_N}.",
    )
    parser.add_argument(
        "--block-rows",
        type=int,
        default=DEFAULT_BLOCK_ROWS,
        help=f"Filas por bloque durante la escritura. Predeterminado: {DEFAULT_BLOCK_ROWS}.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=1000,
        help="Cantidad de posiciones aleatorias en la verificación rápida.",
    )
    parser.add_argument(
        "--hash-completo",
        action="store_true",
        help="Además de las muestras, lee todo el archivo y compara SHA-256.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.accion == "info":
            show_info(args.n, args.block_rows)
        elif args.accion == "crear":
            create_matrix(args.n, args.block_rows)
        elif args.accion == "mostrar":
            show_matrix(args.n)
        elif args.accion == "verificar":
            verify_matrix(args.n, args.hash_completo, args.samples)
        return 0
    except (OSError, RuntimeError, ValueError, FileNotFoundError) as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
