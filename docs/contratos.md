# Acuerdos entre frentes

Este documento fija lo que los tres frentes comparten, para que cada uno avance por su lado sin esperar al otro:

- **Frente A:** app web
- **Frente B:** estimadores de referencia en Python
- **Frente C:** datos y evaluación

Si dos implementaciones siguen exactamente lo que dice aquí, deben dar el mismo resultado. Eso es lo que se comprueba en la validación cruzada (bloque 3, mié 2 – jue 3 dic).

**Regla de cambios.** Este archivo y la carpeta `compartido/` solo se cambian por PR, con la revisión de los otros dos integrantes. Antes de abrir el PR hay que correr:

```bash
python3 compartido/verificar_compartido.py
```

---

## 1. Carpetas y responsables

Cada frente escribe solo en sus carpetas. Así los merges no chocan.

| Carpeta | Frente | Contenido |
|---|---|---|
| `compartido/` | Todos (por PR) | `afinaciones.json`, `parametros.json`, verificador |
| `app/` | A | App web y `app/scripts/` (procesamiento de WAV desde Node) |
| `analisis/afinador/` | B | Paquete Python con los estimadores |
| `analisis/pruebas/` | B | Pruebas de los estimadores |
| `analisis/sinteticos/` | B | Generador de señales sintéticas |
| `analisis/evaluacion/` | C | Notebooks de métricas, figuras y tablas |
| `analisis/resultados/` | A, B, C | CSV de resultados (sección 5.5) |
| `datos/` | C | Grabaciones e índice de NSynth |
| `datos/sinteticos/` | B | Lo escribe el generador: `indice.csv` y los WAV |

## 2. Archivos compartidos

- [`compartido/afinaciones.json`](../compartido/afinaciones.json): instrumentos, afinaciones y cuerdas.
  - El número MIDI es la fuente de verdad: $f = 440 \cdot 2^{(m-69)/12}$.
  - Las cuerdas van de la de número mayor a la cuerda 1.
  - El campo `nota` usa notación en inglés (`E2`, `Eb2`). Es la misma que se usa en los nombres de archivo.
- [`compartido/parametros.json`](../compartido/parametros.json): valores por defecto de toda la cadena.
  - Ningún valor se escribe a mano en el código: se lee de este archivo.
  - Los campos listados en `provisionales` se calibran en el bloque 3, antes de congelar los resultados el vie 4 dic.

## 3. Parámetros

| Campo | Valor | Significado |
|---|---|---|
| `rango.f_min_hz`, `rango.f_max_hz` | 25, 2000 | Rango de búsqueda de $f_0$ para todos los métodos |
| `tramo.N` | 4096 | Muestras por tramo (85 ms a 48 kHz) |
| `tramo.salto` | 512 | Avance entre tramos (10,7 ms a 48 kHz) |
| `tramo.ventana` | `hann` | Hann **periódica**: $w[n] = 0{,}5 - 0{,}5\cos(2\pi n/N)$, $n = 0,\dots,N-1$. Es la de `scipy.signal.get_window("hann", N)`; `numpy.hanning` es la simétrica y **no** sirve |
| `preprocesado.pasa_altas_hz` | 20 | Corte del pasa altas Butterworth |
| `preprocesado.pasa_altas_orden` | 2 | Orden del pasa altas |
| `preprocesado.quitar_media` | true | Restar la media de cada tramo antes de la compuerta y los estimadores |
| `compuerta.rms_min_dbfs` | −50 | RMS mínimo del tramo para considerarlo activo |
| `compuerta.entropia_max` | 0,6 | Entropía espectral máxima para considerarlo activo |
| `fft.factor_zero_padding` | 2 | $N_\text{fft} = 2N$ |
| `fft.interpolacion` | `parabolica-log` | Interpolación parabólica sobre magnitud en dB |
| `hps.R` | 5 | Número de armónicos multiplicados |
| `hps.factor_zero_padding` | 2 | $N_\text{fft} = 2N$ |
| `yin.umbral` | 0,1 | Umbral sobre la diferencia normalizada $d'$ |
| `nota.mediana_tramos` | 5 | Tramos activos que entran en la mediana de suavizado |
| `nota.afinado_cents` | 5 | Tolerancia para mostrar «afinado» |
| `deteccion_cuerda.histeresis_cents` | 30 | Ventaja mínima para cambiar de cuerda detectada |
| `evaluacion.ignorar_inicio_s` | 0,2 | Tiempo inicial descartado al resumir una nota (ataque) |
| `evaluacion.duracion_max_s` | 2,0 | Duración máxima que entra en el resumen de una nota |

## 4. Cadena de procesamiento

Los nombres en Python van en `snake_case`. En TypeScript se usa el mismo nombre en `camelCase` (`estimar_f0` → `estimarF0`). Los campos de los objetos que se devuelven son iguales en los dos lenguajes, porque terminan como columnas de CSV.

En todo lo que sigue, $f_s$ es un parámetro: nunca se supone 48 kHz. NSynth viene a 16 kHz, y el navegador puede dar 44,1 kHz.

### 4.1 Preprocesado de la señal completa

`preprocesar(x, fs, p) -> x_filtrada`

- Pasa altas Butterworth de orden 2 a 20 Hz, **causal**, aplicado a la señal continua con estado y no tramo por tramo.
- En Python: `scipy.signal.butter(2, 20, "highpass", fs=fs, output="sos")` y luego `sosfilt`.
- En TypeScript: un biquad con los mismos coeficientes, calculados por transformada bilineal con prewarping, que es lo que hace `butter`. El script de Node procesa el WAV completo con el mismo filtro que usa la app en vivo.

### 4.2 Tramos

- El tramo `k` va de la muestra `k·salto` a la muestra `k·salto + N − 1`. Solo se procesan tramos completos.
- El tiempo de cada tramo es su centro: $t = (k\cdot\text{salto} + N/2)/f_s$.
- Si `quitar_media` es verdadero, a cada tramo se le resta su media.

### 4.3 Compuerta

`compuerta(tramo, fs, p) -> {activa, rms_dbfs, entropia}`

- $\text{rms\_dbfs} = 20\log_{10}\sqrt{\tfrac1N\sum x_n^2}$, calculado sobre el tramo **sin** ventana, con escala completa = 1,0.
- La entropía se calcula sobre $|X_k|^2$ del tramo **con** ventana de Hann y $N_\text{fft} = N$, sin zero-padding. Solo entran los bins entre $k_\text{min} = \lceil f_\text{min} N/f_s\rceil$ y $k_\text{max} = \lfloor f_\text{max} N/f_s\rfloor$. Con $K$ el número de esos bins y $p_k$ las potencias normalizadas a suma 1:

  $$H = -\frac{1}{\log_2 K}\sum_k p_k\log_2 p_k$$

  Los términos con $p_k = 0$ aportan 0.
- `activa = rms_dbfs >= rms_min_dbfs and entropia <= entropia_max`.
- Si el tramo no está activo, no se llama a ningún estimador y su `f0_hz` queda vacío.

### 4.4 Estimadores

`estimar_f0(tramo, fs, metodo, p) -> {f0_hz, claridad}`

- `metodo` es `"fft"`, `"hps"` o `"yin"`.
- `f0_hz` es un número, o `None` / `null` si el método no encuentra una frecuencia.
- `claridad` está en $[0, 1]$.

**Rango efectivo.** YIN necesita que la ventana de integración $W = N - \tau_\text{max}$ sea al menos $\tau_\text{max}$. Por eso todos los métodos usan:

- $f_\text{min,ef} = \max(f_\text{min},\, 2f_s/N)$
- $\tau_\text{max} = \lfloor f_s/f_\text{min,ef}\rfloor$
- $\tau_\text{min} = \lceil f_s/f_\text{max}\rceil$

Ojo: con $N = 2048$ a 48 kHz, $f_\text{min,ef} \approx 47$ Hz, así que el Mi1 del bajo (41,2 Hz) queda fuera de alcance. Es uno de los resultados del barrido de $N$, no un error.

**`fft`, pico de la FFT con interpolación parabólica**

1. Aplicar la ventana de Hann al tramo, rellenar con ceros hasta $N_\text{fft} = 2N$ y calcular $|X_k|$.
2. Convertir a dB: $L_k = 20\log_{10}(|X_k| + 10^{-12})$.
3. Buscar el máximo de $L_k$ entre los bins de $\lceil f_\text{min,ef} N_\text{fft}/f_s\rceil$ y $\lfloor f_\text{max} N_\text{fft}/f_s\rfloor$.
4. Si el máximo no está en un borde, refinar: $\delta = \tfrac12\,\frac{L_{k-1}-L_{k+1}}{L_{k-1}-2L_k+L_{k+1}}$. En un borde, $\delta = 0$.
5. $f_0 = (k+\delta)\, f_s/N_\text{fft}$.
6. `claridad` $= 1 - H$, con la $H$ de la compuerta.

**`hps`, producto espectral de armónicos**

1. Mismo espectro $|X_k|$ que en `fft`, con $N_\text{fft} = 2N$.
2. $\log P_k = \sum_{r=1}^{R}\log(|X_{rk}| + 10^{-12})$, con $R = 5$, para los $k$ tales que $Rk < N_\text{fft}/2$.
3. Buscar el máximo de $\log P_k$ en el mismo rango que `fft`, recortado a ese límite.
4. Refinar con la misma interpolación parabólica, ahora sobre $\log P_k$.
5. `claridad` $= 1 - H$.

**`yin`**

1. Sobre el tramo **sin** ventana, calcular $d(\tau) = \sum_{j=0}^{W-1}(x_j - x_{j+\tau})^2$ para $\tau = 1,\dots,\tau_\text{max}$, con $W = N - \tau_\text{max}$.
2. Normalizar: $d'(0) = 1$ y $d'(\tau) = d(\tau)\,\big/\,\big[\tfrac1\tau\sum_{j=1}^{\tau} d(j)\big]$.
3. Buscar el primer $\tau \ge \tau_\text{min}$ con $d'(\tau) < \text{umbral}$. Desde ahí, avanzar mientras $d'(\tau+1) < d'(\tau)$, hasta llegar al mínimo local $\tau^*$.
4. Si ningún $\tau$ baja del umbral, `f0_hz` es nulo.
5. Refinar $\tau^*$ con interpolación parabólica sobre $d'$ y calcular $f_0 = f_s/\tau_\text{interp}$.
6. `claridad` $= 1 - d'(\tau^*)$, recortada a $[0, 1]$.

### 4.5 Nota, cents y suavizado

`a_nota(f0_hz, la4) -> {midi, nombre, cents}`

- $m = \operatorname{round}(69 + 12\log_2(f_0/440))$ y $\text{cents} = 1200\log_2(f_0/f(m))$.
- `nombre` es el nombre en solfeo con sostenidos y octava científica: `Do, Do♯, Re, Re♯, Mi, Fa, Fa♯, Sol, Sol♯, La, La♯, Si` + $(m \div 12) - 1$. Por ejemplo, MIDI 40 → `Mi2`.

Suavizado:

- La lectura que se muestra es la **mediana** de `f0_hz` de los últimos `mediana_tramos` tramos activos.
- La memoria se vacía en cuanto llega un tramo inactivo.

### 4.6 Modo cromático y modo por instrumento

- **Cromático:** se muestra `a_nota(f0)`. Los cents son respecto a la nota más cercana.
- **Por instrumento:** `detectar_cuerda(f0_hz, afinacion, cuerda_actual) -> cuerda`.
  - La distancia a cada cuerda es $|1200\log_2(f_0/f_\text{cuerda})|$.
  - La candidata es la cuerda más cercana.
  - Si no había cuerda (`cuerda_actual` nulo), se toma la candidata. Si había, solo se cambia cuando `dist(candidata) + histeresis_cents < dist(actual)`.
  - Los cents que se muestran son **respecto a la nota de la cuerda**, no a la nota más cercana. Por eso pueden pasar de ±50 si la cuerda está muy desafinada.
- **Afinado:** $|\text{cents}| \le$ `afinado_cents`.

## 5. Formatos de datos

Todos los CSV usan UTF-8, coma como separador, **punto** como separador decimal y una fila de encabezado. Un valor vacío significa nulo.

### 5.1 WAV

- PCM mono.
- Las grabaciones propias van a 48 kHz y 16 bits. Cada archivo se recorta por separado para que la nota empiece en $t \approx 0$.
- Cada ejecución se graba **a la vez con dos cadenas de captura**: una de referencia (interfaz de audio) y una de uso real (micrófono del portátil o del celular). Así, entre los dos archivos de una misma toma solo cambia la captura.
- Nombres: `instrumento_nota_cuerda_rep_dispositivo.wav`.
  - `instrumento` es el `id` de `afinaciones.json`.
  - `nota` usa la notación en inglés (`E1`, `A4`).
  - `cuerda` es `c` + número de cuerda.
  - `rep` es `r` + número de repetición.
  - Lo que va antes de `_dispositivo` identifica la **toma**: los archivos que comparten ese prefijo se grabaron juntos.
- Códigos de `dispositivo`:

  | Código | Cadena de captura |
  |---|---|
  | `di` | Instrumento por línea a la entrada Hi-Z de la interfaz |
  | `sm57` | Micrófono Shure SM57 a la interfaz |
  | `portatil` | Micrófono integrado del portátil |
  | `celular` | Micrófono del celular, con una app que grabe WAV sin compresión ni control automático de ganancia |

  Un código nuevo se agrega a esta tabla por PR antes de usarlo.
- Ejemplos: `bajo_E1_c4_r2_di.wav` y `bajo_E1_c4_r2_portatil.wav` son la misma toma; `guitarra_A4_c1_r1_sm57.wav` es una nota pisada (cuerda 1, traste 5).

### 5.2 `datos/grabaciones/lecturas.csv`

Lleva una fila por **archivo**. Los archivos de una misma toma repiten la lectura de los afinadores, porque esa lectura es de la ejecución y no de la captura.

```
archivo,toma,instrumento,cuerda,nota_esperada,midi_esperado,repeticion,dispositivo,detalle_captura,guitartuna_nota,guitartuna_cents,datuner_nota,datuner_cents,datuner_hz,audacity_hz,fecha,observaciones
```

- `toma` es el nombre del archivo sin `_dispositivo.wav`, por ejemplo `bajo_E1_c4_r2`.
- `dispositivo` es el código de la tabla anterior.
- `detalle_captura` es texto libre con lo que permita repetir la captura: modelo de la interfaz, distancia y posición del micrófono, ganancia. Por ejemplo: `Interfaz X, SM57 a 20 cm frente a la boca`.
- `audacity_hz` es propio de cada archivo, porque se mide sobre su espectro.

### 5.3 `datos/sinteticos/indice.csv`

```
archivo,fs_hz,duracion_s,f0_hz,n_armonicos,decaimiento_db_por_armonico,sin_fundamental,B,snr_db,semilla
```

- `sin_fundamental` vale `0` o `1`.
- `B` es el coeficiente de inarmonicidad: los parciales están en $f_k = k f_0\sqrt{1 + Bk^2}$.
- `semilla` es la semilla del ruido, para poder reproducir cada señal.
- Se versiona el índice, pero no los WAV, que se regeneran con el generador a partir del índice.

### 5.4 `datos/indice_nsynth.csv`

Este índice se versiona; los audios no, porque `datos/nsynth/` está en `.gitignore`.

NSynth viene a 16 kHz. Para que $N$ y el salto duren lo mismo en todos los conjuntos y el barrido de $N$ sea comparable, las notas elegidas se **remuestrean a 48 kHz** con `scipy.signal.resample_poly` (factor 3, con su filtro antialiasing) y se guardan en `datos/nsynth/48k/`. Por encima de 8 kHz no hay contenido, porque el original no lo tiene.

El subconjunto y el índice los genera `analisis/evaluacion/indice_nsynth.py` a partir del conjunto de prueba (`nsynth-test`):

- familias `bass`, `guitar` y `string`;
- fuentes `acoustic` y `electronic`. El conjunto de prueba no tiene bajo acústico: el bajo solo aparece como `electronic` (eléctrico grabado en directo, comparable a un bajo por línea) o `synthetic`. Se excluyen los sintéticos;
- MIDI dentro del rango de `compartido/afinaciones.json`.

```
archivo,instrumento_nsynth,familia,fuente,midi,f_ref_hz,velocidad
```

- `archivo` es el `note_str` de NSynth, por ejemplo `guitar_acoustic_010-052-100`.
- `fuente` vale `acoustic`, `electronic` o `synthetic`.
- `f_ref_hz` se calcula a partir de `midi`.

### 5.5 Resultados

**Por tramo:** `analisis/resultados/tramos/<implementacion>_<conjunto>.csv`. Estos archivos no se versionan.

```
implementacion,conjunto,archivo,metodo,N,tramo,t_s,activa,rms_dbfs,entropia,f0_hz,claridad
```

- `implementacion` vale `python`, `ts` o `librosa`.
- `conjunto` vale `sinteticos`, `nsynth` o `grabaciones`.

**Por nota:** `analisis/resultados/notas_<implementacion>_<conjunto>.csv`. Estos sí se versionan.

```
implementacion,conjunto,archivo,metodo,N,f_ref_hz,f0_hz,cents_error,tramos_activos
```

- `f0_hz` es la mediana de los tramos activos con $t$ entre `ignorar_inicio_s` y `ignorar_inicio_s + duracion_max_s`.
- `cents_error` $= 1200\log_2(f_0/f_\text{ref})$.
- Si no hay tramos activos en ese intervalo, `f0_hz` y `cents_error` quedan vacíos.

## 6. Validación cruzada (bloque 3)

Se comparan los CSV por tramo de `python` y `ts`, para el mismo archivo, método, $N$ y tramo:

- `activa` coincide en al menos el 99 % de los tramos. Las diferencias solo deberían aparecer en tramos que están justo en el umbral.
- Donde las dos tienen `f0_hz`, $|1200\log_2(f_{0,\text{ts}}/f_{0,\text{python}})| < 0{,}1$ cents.
- Cada discrepancia se investiga hasta saber cuál de las dos implementaciones está mal. Lo que se encuentre se anota en el registro de uso de IA del README.

## 7. Herramientas

- **Python ≥ 3.11:** las dependencias están en `analisis/requirements.txt`. El entorno virtual va en `analisis/.venv/`, que no se versiona:

  ```bash
  python3 -m venv analisis/.venv
  analisis/.venv/bin/pip install -r analisis/requirements.txt
  ```

  - `librosa` solo lo usa C, como estimador provisional (`librosa.yin`, con `implementacion = librosa`) mientras no existan los de B, y luego como punto de comparación.
- **Node ≥ 20 y TypeScript:** la lectura de WAV en Node queda a criterio del frente A.

## 8. Ramas y PR

- Las ramas llevan el prefijo de su carpeta: `app/…`, `analisis/…`, `datos/…`, `compartido/…`.
- Todo entra a `main` por PR con al menos una revisión. Los cambios a `compartido/` o a este documento necesitan la revisión de los otros dos.
