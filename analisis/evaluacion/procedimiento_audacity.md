# Medición manual de f0 en Audacity

Es el «segundo método» que pide el enunciado: estimar la frecuencia fundamental leyendo el espectro en Audacity. El valor se anota en la columna `audacity_hz` de `datos/grabaciones/lecturas.csv`, una vez por archivo.

> **Borrador.** Hay que validarlo en Audacity con las primeras grabaciones y corregir los nombres de menús o las opciones que no coincidan con la versión instalada. Anotar aquí la versión usada: `Audacity ____`.

## Pasos

1. Abrir el WAV y seleccionar el tramo estable de la nota: de **0,2 s a 2,2 s**. Es la misma ventana que usa la evaluación automática (`evaluacion.ignorar_inicio_s` y `duracion_max_s` en `compartido/parametros.json`).
   - Para fijar la selección con exactitud, usar los campos de inicio y fin de la barra de selección, abajo.
2. Abrir **Analizar → Trazar espectro**.
3. Configurar la ventana del espectro:
   - **Algoritmo:** Espectro.
   - **Función:** ventana de Hann.
   - **Tamaño:** 65536. Es el mayor que cabe en 2 s a 48 kHz (96 000 muestras).
   - **Eje:** frecuencia logarítmica, para ver los graves.
4. Ubicar el pico de la **fundamental**, que no siempre es el más alto: en notas graves suele dominar el 2.º o el 3.er armónico. Acercar el cursor al pico y leer el valor que muestra Audacity como pico.
5. Anotar en `audacity_hz` la frecuencia de la fundamental. Si el pico más alto era un armónico, anotarlo en `observaciones`, por ejemplo: «pico más alto: 2.º armónico, 164,8 Hz». Ese dato sirve para el análisis de errores de octava de la FFT.

## Límites que hay que discutir en el artículo

- **Resolución.** Con tamaño 65536 a 48 kHz, la separación entre bins es $\Delta f = 48000/65536 \approx 0{,}73$ Hz.
  - En Mi1 del bajo (41,2 Hz), un bin equivale a unos **31 cents**.
  - En La4 (440 Hz) equivale a unos 3 cents.

  Hay que comprobar si Audacity interpola el pico o entrega el bin más cercano, por ejemplo con un tono sintético de frecuencia conocida entre dos bins. La respuesta decide si este método sirve para afinar notas graves.
- **Elección de la fundamental.** La hace la persona, así que el método no comete errores de octava «automáticos», pero depende de quien lee el espectro. Conviene que una segunda persona repita algunas mediciones para estimar la variación entre lectores.

## Comprobación con señal conocida

Antes de medir las grabaciones, medir con este procedimiento dos tonos sintéticos de frecuencia exacta y anotar el error en cents:

- un tono de 41,20 Hz;
- un tono de 41,55 Hz, que cae entre dos bins.

Audacity puede generarlos con *Generar → Tono*.
