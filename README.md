# Laboratorio 1 - Matriz 100.000 x 100.000 en disco

**Estudiante:** Jenifer Alejandra Davila Popayan  

## Objetivo

Crear y almacenar en disco una matriz de **100.000 x 100.000** elementos sin cargarla completa en memoria RAM, priorizando:

- bajo consumo de RAM;
- escritura secuencial rápida a disco;
- almacenamiento compacto;
- lectura parcial eficiente;
- verificación del contenido generado.

## Archivos del repositorio

- `laboratorio1.py`: programa principal. Crea, muestra y verifica la matriz.
- `README.md`: explica el enfoque y cómo ejecutar el laboratorio.
- `requirements.txt`: dependencia necesaria (`numpy`).
- `.gitignore`: evita subir a GitHub el archivo binario de aproximadamente 10 GB.


La matriz contiene:

```text
100.000 x 100.000 = 10.000.000.000 elementos
```

Si se creara en RAM con `float64`, necesitaría aproximadamente **80 GB** (74,5 GiB), lo que excede la RAM de la mayoría de equipos.

En esta solución se usa `uint8`, porque el laboratorio no exige un rango numérico específico. Cada elemento ocupa 1 byte, por lo que el archivo final ocupa exactamente:

```text
10.000.000.000 bytes = 10 GB decimales ≈ 9,31 GiB
```

Los valores siguen una regla determinista:

```text
valor[fila, columna] = (fila + columna) % 256
```

Esto permite verificar cualquier posición sin guardar una segunda matriz.

## Estrategia de optimización

### 1. RAM controlada

La matriz nunca se crea completa. Se generan bloques de hasta 256 filas:

```text
256 x 100.000 x 1 byte ≈ 25,6 MB
```

### 2. Escritura rápida

Cada bloque se escribe en formato binario y de forma secuencial. Se evita convertir miles de millones de números a texto, lo que sería mucho más lento y ocuparía más espacio.

### 3. Lectura eficiente

Para consultar el archivo se usa `numpy.memmap`, que permite tratar el archivo como una matriz sin cargar los 10 GB completos en RAM.

### 4. Verificación

Se realizan tres controles:

1. tamaño exacto del archivo;
2. verificación de 1.000 posiciones aleatorias y puntos fijos;
3. opcionalmente, lectura completa y comparación del hash SHA-256.

Se eligió `uint8` porque el enunciado no especifica que los elementos deban tener un rango mayor a 0-255. Si el docente exige enteros de 32 bits, el archivo aumentaría a aproximadamente **40 GB**. Si exige `float64`, aumentaría a aproximadamente **80 GB**.
