# Afinador cromático web

Proyecto final de **Teoría de la Información y Sistemas de Comunicación** (Universidad Nacional de Colombia, 2026-2).

Afinador que corre en el navegador para guitarra, bajo, ukelele, violín y chelo, con un modo cromático automático que reconoce cualquier nota y la cuerda que se está pulsando. El núcleo del proyecto es estimar la frecuencia fundamental $f_0$ y comparar tres métodos: **pico de la FFT con interpolación parabólica**, **producto espectral de armónicos (HPS)** y **YIN**.

- Propuesta: [`propuesta/propuesta.pdf`](propuesta/propuesta.pdf) (fuente en [`propuesta/propuesta.tex`](propuesta/propuesta.tex))
- Autores: Angel Humberto Olivera Pinzón · Carlos Julian Reyes Piraligua

---

## Entregas

| Entrega | Contenido | Peso | Fecha | Estado |
|---|---|---|---|---|
| 1. Propuesta | Introducción, objetivos, marco teórico, metodología (máx. 3 páginas, IEEE + APA) | 10 % | Mié 18 nov 2026 | ✅ Borrador listo |
| 2. Artículo final | Propuesta + implementación, resultados, conclusiones, declaración de uso de IA | 30 % | _Por definir_ | ⏳ |
| 3. Sustentación | Exposición de 8–10 min y preguntas | 60 % | _Por definir_ | ⏳ |

> La nota no depende de que el código funcione, sino de lo que **los dos** demostremos entender de nuestros resultados. Cada uno debe poder explicar los tres métodos, aunque los haya programado el otro.

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

### Estructura del repositorio

```
propuesta/     Entrega 1 (LaTeX, IEEEtran + biblatex-apa)
articulo/      Entrega 2 (se crea en la fase 6)
app/           Aplicación web (TypeScript + Vite)
analisis/      Notebooks y scripts de Python
  afinador/    Implementación de referencia de los estimadores
datos/
  grabaciones/ WAV propios (48 kHz, 16 bits) + lecturas de los afinadores
  sinteticos/  Señales generadas con f0 conocida
  nsynth/      Subconjunto de NSynth (no se versiona, ver .gitignore)
sustentacion/  Diapositivas y video de respaldo de la demo
```

---

## Plan de trabajo

Hay dos frentes que avanzan en paralelo y se juntan en la evaluación:

- **Frente A, app web:** Angel (propuesta, intercambiable)
- **Frente B, análisis y datos:** Carlos (propuesta, intercambiable)

El cronograma está en semanas relativas a partir de la entrega de la propuesta. Hay que ajustarlo cuando se conozca la fecha del artículo final.

### Fase 0: Propuesta (hasta el 18 nov)

- [x] Revisión de literatura y referencias verificadas
- [x] Borrador de la propuesta (3 páginas)
- [x] Repositorio público en GitHub
- [ ] Lectura completa de la propuesta por los dos y ajustes finales
- [ ] Entregar la propuesta

### Fase 1: Datos y referencia (semana 1) · Frente B

- [ ] Protocolo de grabación (ver abajo) y grabación de guitarra, bajo y ukelele
- [ ] Anotar la lectura de GuitarTuna y DaTuner para cada grabación en `datos/grabaciones/lecturas.csv`
- [ ] Medir $f_0$ a mano en Audacity (Analizar → Trazar espectro) para cada grabación
- [ ] Descargar el subconjunto de prueba de NSynth y filtrar las notas acústicas de guitarra, bajo y cuerdas dentro del rango de la tabla de afinaciones
- [ ] Generador de señales sintéticas: tonos armónicos con $f_0$ exacta, sin fundamental, con inarmonicidad $B$ y con ruido gaussiano de SNR conocida

### Fase 2: Estimadores de referencia en Python (semanas 1–2) · Frente B

- [ ] Pico de FFT con ventana de Hann, zero-padding e interpolación parabólica
- [ ] HPS con $R$ armónicos configurable
- [ ] YIN: función de diferencia, normalización acumulada, umbral e interpolación parabólica
- [ ] Compuerta con RMS y entropía espectral normalizada $H$
- [ ] Conversión a nota MIDI y cents; tabla de afinaciones compartida (JSON) con la app
- [ ] Pruebas con señales sintéticas: error < 1 cent a SNR alta para los tres métodos

### Fase 3: App web (semanas 1–3) · Frente A

- [ ] Esqueleto con Vite + TypeScript y despliegue automático en GitHub Pages (GitHub Actions)
- [ ] Captura del micrófono con las restricciones de audio desactivadas y aviso si el navegador no las respeta
- [ ] `AudioWorklet` que acumula tramos de $N$ muestras con salto configurable
- [ ] Portar los tres estimadores a TypeScript, con selector de método en la interfaz
- [ ] Nota y cents con suavizado por mediana
- [ ] Modo por instrumento: lista de afinaciones y detección de cuerda con histéresis
- [ ] Modo cromático
- [ ] Interfaz: aguja/indicador de cents, nota, cuerda, estado afinado (±5 cents); usable en celular
- [ ] Modo depuración: espectro en vivo, $H$ y $f_0$ de los tres métodos a la vez (sirve para la demo)

### Fase 4: Validación cruzada (semana 3) · Ambos

- [ ] Script en Node que procesa WAV con el código de la app y exporta CSV
- [ ] Comparar con la salida de Python sobre los mismos archivos (diferencia < 0,1 cents)
- [ ] Corregir discrepancias y documentar qué se verificó (insumo para la declaración de IA)

### Fase 5: Evaluación y resultados (semanas 4–5) · Ambos

- [ ] Barrido de $N \in \{2048, 4096, 8192, 16384\}$ para los tres métodos
- [ ] Métricas sobre sintéticos, NSynth y grabaciones propias (ver definiciones abajo)
- [ ] Curvas de acierto frente a SNR (30 a −5 dB)
- [ ] Casos de falla: errores de octava en el bajo, efecto de quitar la fundamental, notas con ataque fuerte
- [ ] Latencia hasta la primera lectura estable en la app
- [ ] Timbre: La4 en ukelele (cuerda al aire) y guitarra (1.ª cuerda, traste 5): amplitud de los 10 primeros armónicos, centroide espectral, estimación de $B$
- [ ] Respuesta en frecuencia aproximada del micrófono usado (¿cuánto atenúa por debajo de 100 Hz?)

### Fase 6: Artículo final (semanas 5–6) · Ambos

- [ ] Copiar la propuesta a `articulo/` y añadir implementación, resultados y conclusiones
- [ ] Figuras finales desde los notebooks (mismo estilo y tamaño de columna IEEE)
- [ ] Declaración de uso de IA antes de las referencias, a partir del registro de abajo
- [ ] Revisión cruzada: cada uno lee y corrige las secciones del otro

### Fase 7: Sustentación (semanas 6–7) · Ambos

- [ ] Diapositivas para 8–10 minutos
- [ ] Demo en vivo con la app (guitarra o ukelele) y video de respaldo por si falla el audio del salón
- [ ] Al menos dos ensayos cronometrados
- [ ] Preparar respuestas a las preguntas probables (ver abajo)

### Cronograma resumido

| Semana | Frente A: app | Frente B: análisis | Juntos |
|---|---|---|---|
| 0 (→ 18 nov) | — | — | Cerrar y entregar propuesta |
| 1 | Esqueleto, captura, AudioWorklet | Grabaciones, NSynth, sintéticos | — |
| 2 | Estimadores en TS, nota y cents | Estimadores en Python + pruebas | Revisar juntos YIN y HPS |
| 3 | Presets, detección de cuerda, interfaz | Notebook de métricas | Validación cruzada TS ↔ Python |
| 4 | Modo depuración, latencia, pulido | Barrido de N, curvas de SNR | Análisis de casos de falla |
| 5 | Despliegue final | Timbre e inarmonicidad | Redacción de resultados |
| 6 | — | — | Artículo final y diapositivas |
| 7 | — | — | Ensayos y sustentación |

---

## Protocolo de grabación

- **Formato:** WAV, 48 kHz, 16 bits, mono, grabado con Audacity. Desactivar mejoras de audio y supresión de ruido del sistema operativo.
- **Lugar:** cuarto silencioso, micrófono a unos 30 cm del instrumento, siempre el mismo dispositivo (anotar cuál).
- **Notas:** cada cuerda al aire de guitarra, bajo y ukelele, más algunas notas pisadas (incluida La4 en guitarra 1.ª cuerda, traste 5). Tres repeticiones de unos 3 s por nota.
- **Referencia:** en el mismo momento, anotar la lectura (nota y cents) de GuitarTuna y DaTuner en otro celular.
- **Nombres de archivo:** `instrumento_nota_cuerda_rep.wav`, por ejemplo `bajo_E1_c4_r2.wav`.
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
| El micrófono del portátil o celular casi no capta la fundamental del bajo (41 Hz) | Es precisamente un resultado a reportar; HPS y YIN deberían compensarlo. Medir la respuesta del micrófono |
| El navegador ignora las restricciones de audio (Safari, algunos Android) | Leer `getSettings()` del track y mostrar aviso; probar en Chrome y Firefox |
| Las etiquetas de NSynth no están perfectamente afinadas | Reportar la mediana del error por instrumento y tratar el desfase sistemático aparte |
| La demo en vivo falla por ruido del salón | Video de respaldo y modo depuración para explicar lo que pasa |
| Uno de los dos no domina la parte del otro | Sesiones de revisión conjunta en las semanas 2 y 4 |

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
| 2026-11-14 | Claude Code | Revisión de literatura y borrador de la propuesta | Referencias contrastadas con fuentes en línea; _pendiente: lectura completa del texto por los dos_ |
| 2026-11-16 | Claude Code | Este README y plan de trabajo | _Pendiente: revisión del grupo_ |

## Convenciones

- Commits en español, en imperativo («Agregar…», «Corregir…»).
- Ramas por tarea (`app/detector-cuerda`, `analisis/yin`) y merge a `main` cuando funcione.
- Los datos grandes (NSynth) no se versionan; las grabaciones propias sí, porque son pequeñas.
