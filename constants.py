"""
Parametros de configuración del modelo de simulación

Se definieron los parámetros base para garantizar la estabilidad
estadística y la replicabilidad del modelo EpiSim

Cambiar cualquiera de estos valores puede afectar el funcionamiento :)
"""
N_POPULATION    = 10_000                        # Tamaño de la población total inicial
I0_INFECTED     = 10                            # Casos índice o Infectados iniciales
BETA_MIN        = 0.3;  BETA_MAX       = 0.5    # Rango de la tasa de contacto básico
SIGMA_INV_MIN   = 2.0;  SIGMA_INV_MAX  = 5.0    # Rango del periodo de incubación (días en E)
GAMMA_INV_MIN   = 7.0;  GAMMA_INV_MAX  = 14.0   # Rango del periodo infeccioso (días en I)
P_TRANS_MIN     = 0.4;  P_TRANS_MAX    = 0.6    # Rango de prob. de contagio si hay contacto
VAC_RATE_MIN    = 0.3;  VAC_RATE_MAX   = 0.7    # Rango para tasa de vacunación (% población vacunada)
VAC_EFEC_MIN    = 0.80; VAC_EFEC_MAX   = 0.95   # Rango de efectividad de la vacuna (reducción de S)

# Constante de Escalamiento para la Generación de Contactos Estocásticos
# Es un ajuste para que los contactos no sean siempre 0 sino que estén entre (0, 2)
# Promedio esperado de contactos por día es 5 × 0.4 × 0.5 = 1.0
C_MAX           = 5

DAYS            = 365                           # Número de días a simular (1 año)
N_SIMULATIONS   = 1_000                         # Número de simulaciones independientes
SEMILLA_MAESTRA = 2024                          # Semilla inicial del generador
N_POOL          = 10_000_000                    # Cantidad de números pseudoaleatorios generados