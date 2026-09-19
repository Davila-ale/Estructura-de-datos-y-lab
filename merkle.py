import hashlib

# Función para calcular SHA-256
def calcular_hash(dato):
    return hashlib.sha256(dato.encode()).hexdigest()


# Construir un nivel del árbol de Merkle
def construir_nivel(hashes):
    nuevo_nivel = []

    for i in range(0, len(hashes), 2):

        izquierda = hashes[i]

        # Si existe un hermano, lo usamos.
        # Si no existe, duplicamos el último hash.
        if i + 1 < len(hashes):
            derecha = hashes[i + 1]
        else:
            derecha = izquierda

        combinado = izquierda + derecha

        nuevo_hash = calcular_hash(combinado)

        nuevo_nivel.append(nuevo_hash)

    return nuevo_nivel


# Construir el árbol completo y obtener la raíz
def obtener_merkle_root(hashes):
    nivel_actual = hashes

    while len(nivel_actual) > 1:
        nivel_actual = construir_nivel(nivel_actual)

    return nivel_actual[0]

def mostrar_niveles(hashes):
    nivel_actual = hashes
    numero_nivel = 0

    while len(nivel_actual) > 1:

        print(f"\nNivel {numero_nivel}:")

        for i, hash_actual in enumerate(nivel_actual):
            print(f"  Nodo {i + 1}: {hash_actual}")

        nivel_actual = construir_nivel(nivel_actual)
        numero_nivel += 1

    print(f"\nNivel {numero_nivel}:")
    print(f"  MERKLE ROOT: {nivel_actual[0]}")

# Generar prueba de inclusión
def generar_prueba_inclusion(hashes, indice):
    prueba = []

    nivel_actual = hashes
    indice_actual = indice

    while len(nivel_actual) > 1:

        # Si el nivel tiene cantidad impar,
        # duplicamos el último hash.
        if len(nivel_actual) % 2 != 0:
            nivel_actual = nivel_actual + [nivel_actual[-1]]

        # Determinar cuál es el hermano
        if indice_actual % 2 == 0:
            indice_hermano = indice_actual + 1
            direccion = "derecha"
        else:
            indice_hermano = indice_actual - 1
            direccion = "izquierda"

        hash_hermano = nivel_actual[indice_hermano]

        prueba.append((hash_hermano, direccion))

        # Subimos al siguiente nivel
        nivel_actual = construir_nivel(nivel_actual)

        indice_actual = indice_actual // 2

    return prueba


# Verificar prueba de inclusión
def verificar_prueba(data, prueba, merkle_root):
    hash_actual = calcular_hash(data)

    for hash_hermano, direccion in prueba:

        if direccion == "derecha":
            combinado = hash_actual + hash_hermano
        else:
            combinado = hash_hermano + hash_actual

        hash_actual = calcular_hash(combinado)

    return hash_actual == merkle_root


# 1. Crear las transacciones
transacciones = [
    "Alice paga 10 a Bob",
    "Carlos paga 20 a Diana",
    "Elena paga 15 a Juan",
    "Pedro paga 8 a Ana",
    "Luis paga 12 a Maria"
]


# 2. Calcular el hash de cada transacción
hashes = []

for transaccion in transacciones:
    hashes.append(calcular_hash(transaccion))


print("HASHES DE LAS TRANSACCIONES")
print("-" * 60)

for i, hash_transaccion in enumerate(hashes):
    print(f"Transacción {i + 1}: {hash_transaccion}")


# 3. Mostrar el primer nivel
primer_nivel = construir_nivel(hashes)

print("\nPRIMER NIVEL DEL ÁRBOL")
print("-" * 60)

for i, hash_nuevo in enumerate(primer_nivel):
    print(f"Nodo {i + 1}: {hash_nuevo}")


# 4. Calcular la Merkle Root original
merkle_root_original = obtener_merkle_root(hashes)

print("\nMERKLE ROOT ORIGINAL")
print("-" * 60)
print(merkle_root_original)


# 5. Modificar la transacción 3
transacciones[2] = "Elena paga 150 a Juan"


# 6. Calcular nuevamente los hashes
hashes_modificados = []

for transaccion in transacciones:
    hashes_modificados.append(calcular_hash(transaccion))


# 7. Calcular la nueva Merkle Root
merkle_root_nueva = obtener_merkle_root(hashes_modificados)

print("\nMERKLE ROOT DESPUÉS DE MODIFICAR T3")
print("-" * 60)
print(merkle_root_nueva)

# 8. Comparar las raíces
print("\n¿LA RAÍZ CAMBIÓ?")

if merkle_root_original != merkle_root_nueva:
    print("Sí, la raíz cambió.")
else:
    print("No, la raíz no cambió.")


# 9. Generar prueba de inclusión para T3
prueba_t3 = generar_prueba_inclusion(hashes, 2)

print("\nPRUEBA DE INCLUSIÓN PARA LA TRANSACCIÓN 3")
print("-" * 60)

for hash_hermano, direccion in prueba_t3:
    print(f"{direccion}: {hash_hermano}")


# 10. Verificación válida
resultado_valido = verificar_prueba(
    "Elena paga 15 a Juan",
    prueba_t3,
    merkle_root_original
)

print("\nVERIFICACIÓN DE LA TRANSACCIÓN 3")
print("-" * 60)
print(f"Resultado: {resultado_valido}")


# 11. Verificación con dato incorrecto

resultado_invalido = verificar_prueba(
    "Elena paga 150 a Juan",
    prueba_t3,
    merkle_root_original
)

print("\nVERIFICACIÓN CON DATO INCORRECTO")
print("-" * 60)
print(f"Resultado: {resultado_invalido}")

def mostrar_arbol(hashes):
    print("\nÁRBOL DE MERKLE")
    print("=" * 70)

    nivel_actual = hashes
    niveles = [nivel_actual]

    while len(nivel_actual) > 1:

        if len(nivel_actual) % 2 != 0:
            nivel_actual = nivel_actual + [nivel_actual[-1]]

        nivel_actual = construir_nivel(nivel_actual)
        niveles.append(nivel_actual)

    for i, nivel in enumerate(niveles):
        print(f"\nNivel {i}:")
        for j, hash_actual in enumerate(nivel):
            print(f"  [{j}] {hash_actual}")

mostrar_arbol(hashes)