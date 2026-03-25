# EpiSim — Simulación Monte Carlo de Propagación de Enfermedades Contagiosas
**Punto 4 · Taller Primer 50%**
Universidad Pedagógica y Tecnológica de Colombia — Simulación por Computador

---

## Integración con el Punto 3

Este proyecto utiliza **exclusivamente** la biblioteca de generadores y
validadores construida en el Punto 3 (`generadores_p3/`) para toda la
generación de números pseudoaleatorios y validación estadística.

El archivo `p3_adapter.py` actúa como puente entre ambos puntos:
expone la interfaz que EpiSim necesita (`generar_pool_global`,
`validar_generador`, `graficar_validacion`) delegando la lógica real
al Punto 3, sin modificar ningún archivo de esa biblioteca.

**Generador empleado:** Congruencia Lineal (LCG)
- a = 1 664 525  |  c = 1 013 904 223  |  m = 2^32  (Numerical Recipes / ANSI C)
- Período completo: 2^32 aprox. 4.3e9 (muy superior al millón requerido)

**Pruebas estadísticas ejecutadas (Probador General):**
Medias, Varianza, Chi-cuadrado, Kolmogorov-Smirnov, Poker, Rachas

---

## Estructura del proyecto

```
SC-Metodo-Montecarlo-Propagacion-de-enfermedades/
├── p3_adapter.py                       # Adaptador Punto 3 -> EpiSim (puente de integracion)
├── episim_simulation.py                # Motor SEIR estocastico + PoolGlobal + sims. pareadas
├── episim.py                           # Script principal — genera todas las graficas
├── constants.py                        # Parametros del modelo (externalizados y configurables)
├── contagion_conversion.py             # Matriz S — conversores de eventos epidemiologicos
├── score.py                            # Clases de datos: SimulationResult y ScenarioResults
├── config_ejemplo.csv                  # Archivo de parametros externos (--config)
├── README.md                           # Este archivo
├── salidas/                            # Graficas generadas (creado automaticamente)
└── generadores_p3/                     # Biblioteca del Punto 3 (sin modificaciones, creo)
    ├── generador_numeros/              # LCG, Multiplicativo, Aditivo, Cuadrados Medios
    ├── distribuciones/                 # Uniforme, Normal
    ├── validadores/                    # 6 pruebas estadisticas
    ├── app_services/                   # Servicios de generacion y validacion
    └── generador_npseudoaleatorios/    # API publica del Punto 3
```

---

## Requisitos

```bash
pip install matplotlib scipy
```

---

## Ejecucion

```bash
# Con parametros por defecto
python episim.py

# Cargando parametros desde archivo externo
python episim.py --config config_ejemplo.csv
```

---

## Caracteristicas del motor

### Pool Global de numeros pseudoaleatorios
Se genera un pool de 1 000 000 de numeros U(0,1) al inicio usando el LCG
del Punto 3. Cada vez que EpiSim necesita un numero aleatorio, consume el
siguiente del pool. Cuando el pool se agota, se recarga silenciosamente con
una nueva semilla derivada de la maestra; el evento queda registrado en la
Matriz s,x.

### Probador General
Antes de iniciar las simulaciones, el pool completo se somete a las 6 pruebas
estadisticas del Punto 3. Si el generador no supera todas las pruebas, EpiSim
emite una advertencia pero continua (el LCG con los parametros estandar las
supera sistematicamente).

### Simulaciones PAREADAS sin/con vacunacion
Los parametros epidemiologicos base (beta, sigma_inv, gamma_inv, p_base) son
identicos en cada par de simulaciones sin/con vacunacion. Solo varia el factor
de vacunacion. Esto garantiza una comparacion honesta del impacto de la vacuna.

### Matriz s,x
Cada numero consumido del pool tiene trazabilidad completa: semilla inicial,
parametros del generador, ciclos de recarga y conteo total de Ri consumidos.
