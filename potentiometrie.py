import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from lmfit import Model
from scipy.optimize import root_scalar
import scipy.optimize as opt

i=0
# Anzahl der Iterationen für den Fit 
iterationen = 100000000
# Excel-Datei einlesen(möglichst viele und dichte Messpunkte)
df = pd.read_excel("C:\\Users\\Gusta\\Documents\\Jugend forscht\\Datensaetze\\Potentiometrie-all-data.xlsx")
vol_naoh, ph_wert = df.iloc[5:, i*2].dropna(), df.iloc[5:, i*2+1].dropna()

print(f'CTA: {cta}, i: {i}')


# feststellung der min und max Werte für die x-Achse (Volumen NaOH)
vol_max, vol_min = max(vol_naoh), min(vol_naoh)


##Definition der Funktionen##

# Definition der Funktion (PL7)
def funktion(x, A, D, C, B, G, F):
    return (D + (A - D) / ((1 + ( ((x / C) ** B)) ** G))+ (F * x))
# Erste ableitung der Funktion
def erst_abl(x, A, D, C, B, G, F):
    return (-B*G*(A - D)*((x/C)**B)**G/(x*(((x/C)**B)**G + 1)**2) + F)
# Zweite Ableitung der Funktion
def zwe_abl(x, A, D, C, B, G,F):
    return -2*B**2*G**2*(x/C)**(B*G)*(x/C)**(B*G - 1)*(A - D)/(C*x*((x/C)**(B*G) + 1)**3) + B*G*(x/C)**(B*G - 1)*(A - D)*(B*G - 1)/(C*x*((x/C)**(B*G) + 1)**2)
##FIT ESRSTELLUNG ###

# Verbesserte Schätzung der Parameterwerte basierend auf skalierten Daten
D_start, A_start = max(ph_wert), min(ph_wert)
max_diff_index = np.argmax(np.diff(ph_wert))
# Berechnung des Startwerts für C --> mittelwert der x-Werte an der größten Steigung. Korreliert mit dem Äquivalenzpunkt.
max_diff_index = np.argmax(np.diff(ph_wert))
C_start = np.mean(vol_naoh[max_diff_index:max_diff_index + 2])


param_bounds = {
    "A": (A_start - 6, A_start + 6), 
    "D": (D_start - 6, D_start + 6),
    "C": (C_start * 0.6, C_start * 1.4),
    "B": (0.1, 140), "G": (0.1, 4),
    "F": (-1, 2),
    }


# lmfit-Modell erstellen und Parametergrenzen setzen
model = Model(funktion)
params = model.make_params(A=A_start, D=D_start, C=C_start, B=10, G=1, F=1)
for param, (lower, upper) in param_bounds.items():
    params[param].set(min=lower, max=upper)

# Fit durchführen mit skalierten x-Werten
result = model.fit(ph_wert, params, x=vol_naoh, method="leastsq", max_nfev=iterationen)
print(result.fit_report())
print(f'Anzahl der durchgeführten Iterationen: {result.nfev}')
##Auswertung der Fit Ergebnisse##

# Angepassten C Parameter extrahieren--> startwert für die Suche nach AQ punkt
C_start = result.params['C'].value

print(f'Parameter C (C_start) bei: {C_start:.3f} ml')
# Extract R² from the fit report and save it as a parameter
r_squared_from_report = result.rsquared if hasattr(result, 'rsquared') else None



### Nullstelle Zweiter Ableitung###

x_nullstellen_zweiter_ableitung = root_scalar(
    lambda x: zwe_abl(x, **result.best_values),
    x0=C_start,
    method='newton'
).root

## Plot der Titrationskurve und Ableitung##
font = {
        'size'   : 11}

mpl.rc('font', **font)
cm= 1 / 2.54
# Fit-Kurve berechnen für grafische Darstellung
ml_linespace = np.linspace(vol_min, vol_max, num=200)
ph_zu_linespace = funktion(ml_linespace, **result.best_values)

#ph_fit_deriv = erst_abl(ml_linespace, **result.best_values)
#ph_fit_deriv2 = zwe_abl(ml_linespace, **result.best_values)
# Plot der Titrationskurve und Ableitung
fig, ax1 = plt.subplots(figsize=(16*cm,12*cm))
#ax2 = ax1.twinx()
#ax2.zorder = 0
#ax1.zorder = 1
#ax1.patch.set_visible(False)

ax1.scatter(vol_naoh, ph_wert, color='blue', label='Messpunkte', marker='x', zorder=6, s=20)
ax1.plot(ml_linespace, ph_zu_linespace, color='orange', label='Regression', linewidth=1.2, zorder=4)
#ax2.plot(ml_linespace, ph_fit_deriv, color='green', label='1. Ableitung', linewidth=0.5, linestyle='dashed', zorder=1)
#ax2.plot(ml_linespace, ph_fit_deriv2, color='gray', label='2. Ableitung', linewidth=0.5, linestyle=':', zorder=1)

#ax2.scatter([vol_naoh], [weights], color='green', label='gewichtung', marker='_', zorder=3, s=20)
#ax1.scatter(C_start,funktion(C_start,**result.best_values) , color='gray', label=f'Parameter C bei {C_start:.3f} ml', marker='_', zorder=1, s=20)
#ax1.scatter(x_ph7, 7, color='green', label=f'f(x)=7 bei {x_ph7:.1f} ml', marker='_', zorder=7, s=20)
ax1.scatter(x_nullstellen_zweiter_ableitung, funktion(x_nullstellen_zweiter_ableitung, **result.best_values), color='purple', label=f'f\'\'(x)=0 bei {x_nullstellen_zweiter_ableitung:.1f} ml', marker='_', zorder=9, s=20)  


# Hinzufügen von R² zur Legende
ax1.legend(loc='upper left', title="Legend")
#ax1.text(0.75, 0.05, f"R² = {r_squared_from_report:.4f}", transform=ax1.transAxes, fontsize=10, verticalalignment='top', bbox=dict(boxstyle="round", facecolor="white", alpha=0.5))

ax1.set_xlabel("Volumen NaOH in ml")
ax1.set_ylabel("pH-Wert")
#ax2.set_ylabel("Ableitungen")
ax1.legend(loc='upper left')
#ax2.legend(loc='upper right')
plt.tight_layout()


plt.show()


