# Afinador cromático web

Proyecto final de **Teoría de la Información y Sistemas de Comunicación** (Universidad Nacional de Colombia, 2026-2).

Afinador que corre en el navegador para guitarra, bajo, ukelele, violín y chelo, con un modo cromático automático que reconoce cualquier nota y la cuerda que se está pulsando. El núcleo del proyecto es estimar la frecuencia fundamental $f_0$ y comparar tres métodos: **pico de la FFT con interpolación parabólica**, **producto espectral de armónicos (HPS)** y **YIN**.

- Propuesta: [`propuesta/propuesta.pdf`](propuesta/propuesta.pdf) (fuente en [`propuesta/propuesta.tex`](propuesta/propuesta.tex))
- Autores: Angel Humberto Olivera Pinzón · Carlos Julian Reyes Piraligua · Diego Alberto Romero Olmos

---

## Entregas

| Entrega | Contenido | Peso | Fecha | Estado |
|---|---|---|---|---|
| 1. Propuesta | Introducción, objetivos, marco teórico, metodología (máx. 3 páginas, IEEE + APA) | 10 % | Mié 18 nov 2026 | ✅ Borrador listo |
| 2. Artículo final | Propuesta + implementación, resultados, conclusiones, declaración de uso de IA | 30 % | **Mié 9 dic 2026** | ⏳ |
| 3. Sustentación | Exposición de 8–10 min y preguntas | 60 % | _Por definir_ | ⏳ |

> La nota no depende de que el código funcione, sino de lo que **los tres** demostremos entender de nuestros resultados. Cada uno debe poder explicar los tres métodos, aunque los haya programado otro integrante.

## Alcance

**Incluido**

- Tres estimadores de $f_0$ (FFT + interpolación parabólica, HPS, YIN), contrastados con la lectura manual del espectro en Audacity.
- Modo por instrumento con afinaciones estándar y alternativas (Drop D, medio tono abajo, Open G, DADGAD, bajo de 5 cuerdas, ukelele low G y barítono).
- Modo cromático automático: nota más cercana, desviación en cents y detección de la cuerda pulsada.
- Referencia fija La4 = 440 Hz. Una nota se considera afinada si |c| ≤ 5 cents.
- Evaluación con señales sintéticas, NSynth y grabaciones propias, comparando con GuitarTuna y DaTuner.
- Análisis de armónicos y timbre: La4 en el ukelele frente a la guitarra.

**Fuera de alcance por ahora**

- Clasificador de tipo de voz (bajo, barítono, tenor…). Queda aplazado; la arquitectura entrega $f_0$ y una medida de claridad por tramo para poder agregarlo después.
- Identificación automática del instrumento.
- Referencia de La4 ajustable y temperamentos distintos del igual.

## Arquitectura

```
Micrófono ─► Preprocesado ─► Compuerta ──────► Estimador f0 ─────► Nota y cents ─► Interfaz
(getUserMedia,  (pasa altas,   (RMS + entropía   (FFT · HPS · YIN)   (m̂, c, mediana)  (cuerda, aguja)
 48 kHz)         ventana Hann)  espectral H)
```

- **App web:** TypeScript + Vite, Web Audio API con `AudioWorklet`. Se captura con `echoCancellation`, `noiseSuppression` y `autoGainControl` desactivados. Se publica en GitHub Pages.
- **Análisis:** Python (NumPy, SciPy, Matplotlib) en notebooks; aquí salen todas las figuras y tablas del artículo.
- **Validación cruzada:** los mismos archivos WAV se procesan con la implementación en TypeScript (desde Node) y con la de Python. Las dos deben coincidir con una diferencia menor a 0,1 cents.
- **Acuerdos entre frentes:** [`docs/contratos.md`](docs/contratos.md) fija la interfaz de cada etapa, los parámetros y los formatos de datos. La tabla de afinaciones y los parámetros por defecto están en [`compartido/`](compartido/).

### Estructura del repositorio

```
propuesta/     Entrega 1 (LaTeX, IEEEtran + biblatex-apa)
articulo/      Entrega 2 (se crea el jue 3 dic)
docs/          Acuerdos entre frentes (contratos.md)
compartido/    afinaciones.json, parametros.json y su verificador
app/           Aplicación web (TypeScript + Vite)             · Frente A
analisis/
  afinador/    Implementación de referencia de los estimadores · Frente B
  pruebas/     Pruebas de los estimadores                      · Frente B
  sinteticos/  Generador de señales sintéticas                 · Frente B
  evaluacion/  Notebooks de métricas, figuras y tablas         · Frente C
  resultados/  CSV de resultados (por tramo no se versionan)
datos/                                                         · Frente C
  grabaciones/ WAV propios (48 kHz, 16 bits) + lecturas de los afinadores
  sinteticos/  Señales generadas con f0 conocida
  nsynth/      Subconjunto de NSynth (no se versiona, ver .gitignore)
sustentacion/  Diapositivas y video de respaldo de la demo
```

---

## Plan de trabajo

Hay tres frentes que avanzan en paralelo y se juntan en la validación cruzada y la evaluación. Pueden trabajar sin esperarse porque comparten los acuerdos de [`docs/contratos.md`](docs/contratos.md). Todavía no están asignados:

- **Frente A:** app web
- **Frente B:** estimadores de referencia en Python
- **Frente C:** datos y evaluación

El artículo se entrega el **miércoles 9 de diciembre**, así que hay dos semanas desde el 25 de noviembre. El plan está organizado en cuatro bloques con fecha. Cada tarea lleva su frente entre corchetes, y las marcadas con ★ son imprescindibles para el artículo. Si el tiempo no alcanza, se recorta en el orden de la lista [Qué recortar primero](#qué-recortar-primero).

### Hitos

| Fecha | Hito |
|---|---|
| Jue 26 nov | Acuerdos aprobados, los tres con acceso al repositorio, grabación piloto revisada |
| Mar 1 dic | Estimadores en Python y en TypeScript funcionando sobre señales sintéticas; grabaciones e índice de NSynth listos |
| Jue 3 dic | Validación cruzada TS ↔ Python superada |
| Vie 4 dic | **Resultados congelados**: figuras y tablas finales del artículo |
| Mar 8 dic | Artículo revisado por los tres |
| **Mié 9 dic** | **Entrega del artículo** |

### Fase 0: Propuesta (18 nov)

- [x] Revisión de literatura y referencias verificadas
- [x] Borrador de la propuesta (3 páginas)
- [x] Repositorio público en GitHub
- [x] Borrador de los acuerdos entre frentes (`docs/contratos.md`, `compartido/`)
- [ ] Lectura completa de la propuesta por los tres y ajustes finales
- [ ] Entregar la propuesta

### Bloque 1: Arranque (mié 25 – jue 26 nov)

- [ ] ★ [Todos] Revisar y aprobar `docs/contratos.md` antes de escribir código
- [ ] ★ [Todos] Agregar a los tres como colaboradores del repositorio
- [ ] ★ [Todos] Entorno de trabajo: Python ≥ 3.11 con las dependencias del contrato y Node ≥ 20
- [ ] ★ [C] Grabación piloto: Mi1 del bajo, Mi2 de la guitarra y Do4 del ukelele, con las dos cadenas de captura a la vez. Revisar en el espectro si cada cadena capta la fundamental
- [ ] ★ [A] Esqueleto con Vite + TypeScript y despliegue automático en GitHub Pages (GitHub Actions)
- [ ] ★ [B] Generador de señales sintéticas: tonos armónicos con $f_0$ exacta, sin fundamental, con inarmonicidad $B$ y con ruido gaussiano de SNR conocida; escribe `datos/sinteticos/indice.csv`

### Bloque 2: Construcción (vie 27 nov – mar 1 dic)

**Frente A, app web**

- [ ] ★ Captura del micrófono con las restricciones de audio desactivadas y aviso si el navegador no las respeta
- [ ] ★ `AudioWorklet` que acumula tramos de $N$ muestras con salto configurable
- [ ] ★ Los tres estimadores en TypeScript siguiendo `docs/contratos.md`, sin esperar al frente B
- [ ] ★ Nota y cents con suavizado por mediana; modo cromático
- [ ] ★ Script en Node (`app/scripts/`) que procesa WAV con el código de la app y escribe los CSV por tramo

**Frente B, estimadores en Python**

- [ ] ★ Pico de FFT con ventana de Hann, zero-padding e interpolación parabólica
- [ ] ★ HPS con $R$ armónicos configurable
- [ ] ★ YIN: función de diferencia, normalización acumulada, umbral e interpolación parabólica
- [ ] ★ Compuerta con RMS y entropía espectral normalizada $H$
- [ ] ★ Conversión a nota MIDI y cents, leyendo `compartido/afinaciones.json` y `compartido/parametros.json`
- [ ] ★ Script que procesa un conjunto de WAV y escribe los CSV por tramo y por nota
- [ ] ★ Pruebas con señales sintéticas: error < 1 cent a SNR alta para los tres métodos

**Frente C, datos y evaluación**

- [ ] ★ Grabaciones completas con las dos cadenas a la vez (ver [Protocolo de grabación](#protocolo-de-grabación)) y `datos/grabaciones/lecturas.csv` con las lecturas de GuitarTuna y DaTuner
- [ ] ★ Descargar el conjunto de prueba de NSynth, filtrar las notas acústicas de guitarra, bajo y cuerdas dentro del rango de la tabla de afinaciones y generar `datos/indice_nsynth.csv`
- [ ] ★ Notebook de métricas, leyendo los CSV del formato acordado, con `librosa.yin` como estimador provisional (se cambia por los de B cuando estén)

### Bloque 3: Validación y evaluación (mié 2 – vie 4 dic)

**Validación cruzada (A y B, mié 2 – jue 3)**

- [ ] ★ Procesar los mismos WAV con Python y con el script de Node y comparar: diferencia < 0,1 cents y `activa` igual en ≥ 99 % de los tramos
- [ ] ★ Corregir discrepancias y anotar qué se verificó en el registro de uso de IA

**Frente A, completar la app**

- [ ] ★ Modo por instrumento: lista de afinaciones y detección de cuerda con histéresis
- [ ] ★ Interfaz: indicador de cents, nota, cuerda y estado afinado (±5 cents); usable en celular
- [ ] Latencia hasta la primera lectura estable

**Frente C con apoyo de B, resultados**

- [ ] ★ Medir $f_0$ a mano en Audacity (Analizar → Trazar espectro) para cada grabación y documentar el procedimiento
- [ ] ★ Métricas de los tres métodos sobre sintéticos, NSynth y grabaciones propias, frente a GuitarTuna, DaTuner y Audacity
- [ ] ★ Barrido de $N \in \{2048, 4096, 8192, 16384\}$
- [ ] ★ Curvas de acierto frente a SNR (30 a −5 dB)
- [ ] ★ Casos de falla: errores de octava en el bajo, efecto de quitar la fundamental, notas con ataque fuerte
- [ ] ★ Comparación de cadenas de captura: cuántos dB hay entre la fundamental y el 2.º armónico con la interfaz y con el portátil o celular, y cómo cambia el error de cada método
- [ ] ★ Timbre: La4 en ukelele (cuerda al aire) y guitarra (1.ª cuerda, traste 5), con el mismo micrófono y posición: amplitud de los 10 primeros armónicos y centroide espectral
- [ ] Estimación del coeficiente de inarmonicidad $B$

**Artículo (Todos, desde el jue 3)**

- [ ] ★ Copiar la propuesta a `articulo/` y escribir la sección de implementación mientras se terminan los resultados

### Bloque 4: Artículo final (sáb 5 – mar 8 dic) · Todos

- [ ] ★ Resultados y conclusiones, con las figuras finales de los notebooks (tamaño de columna IEEE)
- [ ] ★ Declaración de uso de IA antes de las referencias, a partir del registro de abajo
- [ ] ★ Revisión cruzada el lunes 7: cada uno lee y corrige las secciones de los demás
- [ ] ★ Versión final y PDF el martes 8
- [ ] ★ **Entregar el miércoles 9 de diciembre**

### Después del 9 de diciembre: Sustentación · Todos

La fecha está por definir.

- [ ] Modo depuración en la app: espectro en vivo, $H$ y $f_0$ de los tres métodos a la vez
- [ ] Diapositivas para 8–10 minutos
- [ ] Demo en vivo con la app (guitarra o ukelele) y video de respaldo por si falla el audio del salón
- [ ] Al menos dos ensayos cronometrados
- [ ] Preparar respuestas a las preguntas probables (ver abajo)

### Cronograma resumido

| Fechas | Frente A: app | Frente B: estimadores | Frente C: datos y evaluación | Juntos |
|---|---|---|---|---|
| Mié 25 – jue 26 nov | Esqueleto y despliegue | Generador sintético | Grabación piloto | Aprobar `docs/contratos.md`, colaboradores |
| Vie 27 nov – mar 1 dic | Captura, AudioWorklet, estimadores en TS, script Node | Estimadores, compuerta, pruebas, script CSV | Grabaciones, índice de NSynth, notebook de métricas | Revisar juntos YIN y HPS (dom 29) |
| Mié 2 – vie 4 dic | Modo por instrumento, interfaz | Validación cruzada, apoyo en resultados | Audacity, métricas, barrido de N, SNR, cadenas, timbre | Validación cruzada; resultados congelados el vie 4 |
| Sáb 5 – mar 8 dic | — | — | — | Redacción, revisión cruzada (lun 7), versión final (mar 8) |
| Mié 9 dic | — | — | — | **Entrega del artículo** |
| Después | Modo depuración | — | — | Diapositivas, demo, ensayos |

### Qué recortar primero

Si el viernes 4 los resultados no están completos, se recorta en este orden. Nada de esto lo pide el enunciado.

1. Modo depuración de la app: ya está fuera del artículo y pasa a la sustentación.
2. Medición de latencia: se reemplaza por la cota teórica a partir de $N$, el salto y la mediana.
3. Estimación de $B$.
4. $N = 16384$ en el barrido.
5. NSynth reducido a guitarra y bajo.
6. Afinaciones alternativas en la interfaz: se deja solo la estándar de cada instrumento; la tabla completa sigue en `compartido/`.

---

## Protocolo de grabación

Los detalles de nombres y columnas están en [`docs/contratos.md`](docs/contratos.md), sección 5.

- **Dos cadenas a la vez.** Cada ejecución se graba al mismo tiempo con:
  - **Referencia:** la interfaz de audio. El bajo va por línea a la entrada Hi-Z (`di`); la guitarra y el ukelele, con el SM57 (`sm57`).
  - **Uso real:** el micrófono del portátil (`portatil`) o del celular (`celular`), con una app que grabe WAV sin compresión ni control automático de ganancia.

  Así, entre los dos archivos de una toma solo cambia la captura.
- **Formato:** WAV, 48 kHz, 16 bits, mono. Poner también la interfaz a 48 kHz y elegirla directamente en Audacity, para que el sistema no remuestree ni procese el audio. Desactivar las mejoras de audio y la supresión de ruido del sistema operativo.
- **Nivel:** picos entre −12 y −6 dBFS, sin saturar.
- **Lugar y posición:**
  - Cuarto silencioso.
  - SM57 a distancia fija, por ejemplo 20 cm frente a la boca del instrumento. Cerca aparece el efecto de proximidad, que realza los graves.
  - Portátil o celular a unos 30 cm.
  - Anotar todo en `detalle_captura`.
- **Notas:** cada cuerda al aire de guitarra, bajo y ukelele, más algunas notas pisadas (incluida La4 en guitarra, 1.ª cuerda, traste 5). Tres repeticiones de unos 3 s por nota.
- **Lectura de referencia:** en el mismo momento, anotar la lectura (nota y cents) de GuitarTuna y DaTuner. Si un solo celular no puede usar las dos apps a la vez, alternarlas por repetición y anotarlo. Para el bajo por línea, el celular debe oírlo por un amplificador o monitores.
- **Nombres de archivo:** `instrumento_nota_cuerda_rep_dispositivo.wav`, por ejemplo `bajo_E1_c4_r2_di.wav` y `bajo_E1_c4_r2_portatil.wav` para la misma toma.
- **Recorte:** cada archivo por separado, para que la nota empiece en $t \approx 0$.
- **Control:** revisar en el espectrograma de Audacity que hay contenido armónico claro y que no hay saturación.

## Métricas

Con $\hat f$ la estimación y $f_\text{ref}$ la referencia, el error en cents es $c = 1200\log_2(\hat f / f_\text{ref})$.

| Métrica | Definición |
|---|---|
| Error absoluto medio | Promedio de \|c\| sobre las notas detectadas |
| Acierto de afinación | % de estimaciones con \|c\| ≤ 5 cents |
| Acierto de nota | % de estimaciones con \|c\| ≤ 50 cents |
| Errores de octava o armónico | % de estimaciones a menos de 50 cents de ±1200 (octava), +1902 (3.er armónico) o +2400 (4.º armónico) |
| Latencia | Tiempo desde el ataque hasta la primera lectura estable |
| Robustez | Acierto de nota en función de la SNR |

## Riesgos

| Riesgo | Mitigación |
|---|---|
| El micrófono del portátil o celular casi no capta la fundamental del bajo (41 Hz) | Es precisamente un resultado a reportar; HPS y YIN deberían compensarlo. Las tomas grabadas a la vez con la interfaz permiten medir cuánto se pierde |
| El navegador ignora las restricciones de audio (Safari, algunos Android) | Leer `getSettings()` del track y mostrar aviso; probar en Chrome y Firefox |
| Las etiquetas de NSynth no están perfectamente afinadas | Reportar la mediana del error por instrumento y tratar el desfase sistemático aparte |
| La demo en vivo falla por ruido del salón | Video de respaldo y modo depuración para explicar lo que pasa |
| Alguien no domina la parte de los demás | Revisión conjunta de YIN y HPS el domingo 29 y de los resultados el viernes 4 |
| Solo hay dos semanas hasta el artículo | Resultados congelados el viernes 4 y lista de [qué recortar primero](#qué-recortar-primero) |

## Preguntas probables en la sustentación

- ¿Por qué la FFT confunde la fundamental con un armónico? ¿Por qué pasa más en el bajo?
- ¿Qué limita la resolución en frecuencia y cómo la mejora la interpolación sin alargar la ventana?
- ¿Por qué YIN normaliza la función de diferencia? ¿Qué pasaría sin esa normalización?
- ¿Qué relación tiene YIN con la autocorrelación?
- ¿Qué mide la entropía espectral y por qué sirve para saber si hay una nota?
- ¿Por qué dos instrumentos suenan distinto en la misma nota? ¿Qué es la inarmonicidad?
- ¿Cuál es el compromiso entre latencia y precisión en un afinador?
- ¿Cómo verificaron que el código (incluido el generado con IA) era correcto?

## Registro de uso de IA

El artículo final debe declarar qué herramientas de IA se usaron, para qué y cómo se verificó lo generado. Se anota aquí a medida que se usa.

| Fecha | Herramienta | Para qué | Cómo se verificó |
|---|---|---|---|
| 2026-11-14 | Claude Code | Revisión de literatura y borrador de la propuesta | Referencias contrastadas con fuentes en línea; _pendiente: lectura completa del texto por los tres_ |
| 2026-11-16 | Claude Code | Este README y plan de trabajo | _Pendiente: revisión del grupo_ |
| 2026-11-25 | Claude Code | Acuerdos entre frentes (`docs/contratos.md`, `compartido/`) | Tabla de afinaciones contrastada con `verificar_compartido.py` (nombre ↔ MIDI, rango, YIN); _pendiente: revisión del grupo_ |

## Convenciones

- Commits en español, en imperativo («Agregar…», «Corregir…»).
- Ramas por tarea con el prefijo de su carpeta (`app/detector-cuerda`, `analisis/yin`) y entrada a `main` por PR con al menos una revisión. Los cambios a `compartido/` o a `docs/contratos.md` los revisan los otros dos.
- Los parámetros no se escriben a mano en el código: se leen de `compartido/parametros.json`.
- Los datos grandes (NSynth) no se versionan; las grabaciones propias sí, porque son pequeñas.
