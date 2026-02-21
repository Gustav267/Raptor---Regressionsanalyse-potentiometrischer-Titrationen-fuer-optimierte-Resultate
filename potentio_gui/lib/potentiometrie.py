import matplotlib as mpl
import numpy as np
import pandas as pd
from lmfit import Model
from matplotlib.axes import Axes
from scipy.optimize import root_scalar


def create_plot(vol_naoh1: list[float], ph_wert1: list[float], ax1: Axes):
    if len(vol_naoh1) != len(ph_wert1) or len(vol_naoh1) <= 8 or len(ph_wert1) <= 8:
        return

    # Anzahl der Iterationen für den Fit (je mehr, desto genauer,maximal 10^10)
    iterationen = 100000000
    # Excel-Datei einlesen(möglichst viele und dichte Messpunkte, mindestens 9)
    # df = pd.read_excel("C:\\Users\\Gusta\\Documents\\Jugend forscht\\Datensaetze\\Potentiometrie-all-data.xlsx")
    # vol_naoh, ph_wert = df.iloc[5:, i*2].dropna(), df.iloc[5:, i*2+1].dropna()
    # cta=("%s%s" % (str(df.iloc[2, (i*2)+1]),df.iloc[3, (i*2)+1]))
    # print(f'CTA: {cta}, i: {i}')
    # Drop all pH values strictly between 4 and 10 and their corresponding vol_naoh
    # Keep only points where pH <= 4 or pH >= 10
    vol_naoh, ph_wert = pd.Series(vol_naoh1), pd.Series(ph_wert1)

    # Berechnung des Startwerts für C --> mittelwert der x-Werte an der größten Steigung
    max_diff_index = np.argmax(np.diff(ph_wert))
    # Aep_gesch ist C_start skaliert auf die Original-Volumenskala
    Aep_gesch = np.mean(vol_naoh[max_diff_index : max_diff_index + 2])

    # Erste Filterung: Drop all vol_naoh values strictly between Aep_gesch - 5 and Aep_gesch + 5 and their corresponding ph_wert
    # Keep only points where vol_naoh <= Aep_gesch - 5 or vol_naoh >= Aep_gesch + 5

    vol_max, vol_min = max(vol_naoh), min(vol_naoh)

    # Funktion zur Rücktransformation der skalierten x-Werte
    def rescale_x(x):
        return x

    # Funktion zur Skalierung der x-Werte auf [0, 1] normieren
    def skaliere_x(x):
        return x

    x_scaled = skaliere_x(vol_naoh)

    ##Definition der Funktionen##

    # Definition der 7-Parameter-Logistischen Funktion (PL7)
    def seven_pl(x, A, D, C, B, G, F):
        return D + (A - D) / ((1 + (((x / C) ** B)) ** G)) + (F * x)

    # Erste ableitung der 7-Parameter-Logistischen Funktion  (skaliert)
    def erst_abl(x, A, D, C, B, G, F):
        return (
            -B
            * G
            * (A - D)
            * ((x / C) ** B) ** G
            / (x * (((x / C) ** B) ** G + 1) ** 2)
            + F
        )

    # Zweite Ableitung der 7-Parameter-Logistischen Funktion
    def zwe_abl(x, A, D, C, B, G, F):
        return (
            B
            * G
            * (A - D)
            * (B * G * ((x / C) ** B) ** G - B * G + ((x / C) ** B) ** G + 1)
            * ((x / C) ** B) ** G
            / (x**2 * (((x / C) ** B) ** G + 1) ** 3)
        )

    ###FIT ESRSTELLUNG ###

    # Verbesserte Schätzung der Parameterwerte basierend auf skalierten Daten
    D_start, A_start = max(ph_wert), min(ph_wert)
    max_diff_index = np.argmax(np.diff(ph_wert))
    ##Berechnung des Startwerts für C--> mittelwert der x-Werte an der größten Steigung
    C_start = skaliere_x(Aep_gesch)

    param_bounds = {
        "A": (A_start - 6, A_start + 6),
        "D": (D_start - 6, D_start + 6),
        "C": (C_start * 0.6, C_start * 1.4),
        "B": (0.1, 140),
        "G": (0.1, 4),
        "F": (-1, 2),
    }

    # Gewichte für den Fit kp,ob hier optimal)
    # weights =1+0.0001 * (1/np.abs(x_scaled - C_start + 1e-10)) # Vermeidet Division durch Null
    # lmfit-Modell erstellen und Parametergrenzen setzen
    model = Model(seven_pl)
    params = model.make_params(A=A_start, D=D_start, C=C_start, B=10, G=1, F=1)
    for param, (lower, upper) in param_bounds.items():
        params[param].set(min=lower, max=upper)

    # Fit durchführen mit skalierten x-Werten
    result = model.fit(
        ph_wert, params, x=x_scaled, method="leastsq", max_nfev=iterationen
    )
    print(result.fit_report())
    print(f"Anzahl der durchgeführten Iterationen: {result.nfev}")
    ##Auswertung der Fit Ergebnisse##

    # Angepassten C Parameter extrahieren--> startwert für die Suche nach AQ punkt
    C_start = result.params["C"].value
    Aep_gesch = rescale_x(C_start)
    print(f"Parameter C (Aep_gesch) bei: {Aep_gesch:.3f} ml")
    # Extract R² from the fit report and save it as a parameter
    r_squared_from_report = result.rsquared if hasattr(result, "rsquared") else None

    ##Tangentenverfahren##
    # Bereiche für die Suche nach Steigung 1
    # bereiche = [[vol_min, Aep_gesch], [Aep_gesch, vol_max]]
    bereiche_scaled = [
        [vol_min, C_start],
        [C_start, vol_max],
    ]  # Vermeidet Probleme bei 0

    # Hilfsfunktion f(x) = erst_abl(x) - 1
    def f(x):
        return ((erst_abl(x, **result.best_values))) - 1

    # Nullstellen der Ableitung - 1 suchen im bereich
    def finde_x_bei_steigung_eins(bereich):
        res = root_scalar(
            f, bracket=bereich, fprime=lambda x: (zwe_abl(x, **result.best_values))
        )  # sucht Nullstelle in Bereich 1
        return res.root if res.converged else None

    # x-Werte mit Steigung 1 finden im Bereich und eindeutige Werte behalten
    x_steigung_eins = np.array(
        [finde_x_bei_steigung_eins(bereich) for bereich in bereiche_scaled]
    )
    x_steigung_eins = x_steigung_eins[x_steigung_eins != None]

    # Falls steigung 1 gefunden wurden, berechnen
    if len(x_steigung_eins) > 0:
        punkt_zu_steigung_eins = [
            np.array([x, seven_pl(x, **result.best_values)]) for x in x_steigung_eins
        ]
        steigung = 1  # Steigung 1 in Originalskala

        def tangente(x, x_tangentenpunkt, y_tangentenpunkt):
            return steigung * (x - x_tangentenpunkt) + y_tangentenpunkt

        x_tangentenwerte_scaled = np.linspace(vol_min, vol_max, 10)
        x_tangentenwerte_ml = np.linspace(vol_min, vol_max, 10)
        y_tangenten = [
            tangente(x_tangentenwerte_scaled, p[0], p[1])
            for p in punkt_zu_steigung_eins
        ]

        # Mittlere Gerade
        x_mittel, y_mittel = np.mean(x_steigung_eins), np.mean(
            [p[1] for p in punkt_zu_steigung_eins]
        )
        y_mittlere_tangente = tangente(x_tangentenwerte_scaled, x_mittel, y_mittel)

        def finde_aequivalenzpunkt(x_startwert):
            res = root_scalar(
                lambda x: seven_pl(x, **result.best_values)
                - tangente(x, x_mittel, y_mittel),
                x0=x_startwert,
                method="newton",
            )
            return res.root if res.converged else None

        aequivalenzpunkt_x = finde_aequivalenzpunkt(C_start)

        aequivalenzpunkt_y = seven_pl(aequivalenzpunkt_x, **result.best_values)
        aequivalenzpunkt = np.array([rescale_x(aequivalenzpunkt_x), aequivalenzpunkt_y])

    ## pH 7 Punkt berechnen

    def finde_x_bei_ph(ph_wert, x_start):
        res = root_scalar(
            lambda x: seven_pl(x, **result.best_values) - ph_wert,
            x0=x_start,
            method="newton",
            fprime=lambda x: erst_abl(x, **result.best_values),
        )
        return res.root if res.converged else None

    x_ph7 = rescale_x(finde_x_bei_ph(7, C_start))

    ### Nullstelle Zweiter Ableitung###

    # Zweite Ableitung der Fit-Kurve berechnen und Nullstellen suchen
    x_scaled_nullstellen_zweiter_ableitung = root_scalar(
        lambda x: zwe_abl(x, **result.best_values),
        x0=C_start,
        bracket=x_steigung_eins[0:2],
        method="newton",
    ).root
    vol_nullstellen_zweiter_ableitung = rescale_x(
        x_scaled_nullstellen_zweiter_ableitung
    )

    ## Plot der Titrationskurve und Ableitung##
    font = {"size": 11}

    mpl.rc("font", **font)
    cm = 1 / 2.54

    color = "#203864"
    # Fit-Kurve berechnen für grafische Darstellung
    x_linespace_scaled = np.linspace(vol_min, vol_max, num=200)
    ph_zu_linespace = seven_pl(x_linespace_scaled, **result.best_values)
    x_linespace_ml = rescale_x(x_linespace_scaled)
    ph_fit_deriv = erst_abl(x_linespace_scaled, **result.best_values)
    ph_fit_deriv2 = zwe_abl(x_linespace_scaled, **result.best_values)
    # Plot der Titrationskurve und Ableitung
    # fig, ax1 = plt.subplots(figsize=(19.37 * cm, 12.9133 * cm))
    ax2 = ax1.twinx()
    ax2.zorder = 0
    ax1.zorder = 1
    ax1.patch.set_visible(False)

    ax1.scatter(
        vol_naoh, ph_wert, color="blue", label="Messpunkte", marker="x", zorder=6, s=20
    )
    ax1.plot(
        x_linespace_ml,
        ph_zu_linespace,
        color="orange",
        label="Titrationskurve",
        linewidth=1,
        zorder=4,
    )
    ax2.plot(
        x_linespace_ml,
        ph_fit_deriv,
        color="green",
        label="1. Ableitung",
        linewidth=1,
        linestyle="dashed",
        zorder=1,
    )
    ax2.plot(
        x_linespace_ml,
        ph_fit_deriv2,
        color="gray",
        label="2. Ableitung",
        linewidth=1,
        linestyle=":",
        zorder=1,
    )

    # ax2.scatter([vol_naoh], [weights], color='green', label='gewichtung', marker='_', zorder=3, s=20)
    # ax1.scatter(Aep_gesch,seven_pl(C_start,**result.best_values) , color='gray', label=f'Parameter C bei {Aep_gesch:.3f} ml', marker='_', zorder=1, s=20)
    ax1.scatter(
        x_ph7,
        7,
        color="purple",
        label=f"f(x)=7 bei {x_ph7:.1f} ml",
        marker="_",
        zorder=7,
        s=20,
    )
    ax1.scatter(
        vol_nullstellen_zweiter_ableitung,
        seven_pl(x_scaled_nullstellen_zweiter_ableitung, **result.best_values),
        color="green",
        label=f"Wendestelle bei {vol_nullstellen_zweiter_ableitung:.1f} ml",
        marker="_",
        zorder=9,
        s=20,
    )
    if len(x_steigung_eins) > 1:
        ax1.scatter(
            aequivalenzpunkt[0],
            aequivalenzpunkt[1],
            color="red",
            label=f"Äquivalenzpunkt bei {aequivalenzpunkt[0]:.1f} ml",
            marker="_",
            zorder=8,
            s=20,
        )
        ax1.plot(
            x_tangentenwerte_ml,
            y_mittlere_tangente,
            color="red",
            linestyle=":",
            linewidth=1,
            zorder=5,
            label="Mittlere Tangente",
        )  # Mittlere Tangente
        ax1.plot(
            x_tangentenwerte_ml,
            y_tangenten[0],
            color=color,
            linestyle=":",
            linewidth=1,
            zorder=3,
            label="Tangenten bei f'(x)=1",
        )  # 1.Tangente bei 45°
        ax1.plot(
            x_tangentenwerte_ml,
            y_tangenten[1],
            color=color,
            linestyle=":",
            linewidth=1,
            zorder=2,
        )  # 2.Tangente bei -45°
    else:
        print("keine tangenten gefunden")

    # Hinzufügen von R² zur Legende
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")
    ax1.text(
        0.95,
        0.05,
        f"R² = {r_squared_from_report:.4f}",
        transform=ax1.transAxes,
        fontsize=10,
        verticalalignment="top",
        horizontalalignment="right",
        color=color,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.5),
    )
    ax1.set_ylim(0, 15.0)
    ax1.set_xlabel("Volumen NaOH in ml", color=color)
    ax1.set_ylabel("pH-Wert", color=color)
    ax2.set_ylabel("Ableitungen", color=color)
    l1 = ax1.legend(loc="upper left")
    l2 = ax2.legend(loc="upper right")
    for text in l1.get_texts():
        text.set_color(color)
    for text in l2.get_texts():
        text.set_color(color)
    # plt.tight_layout()
    for spine in ax1.spines.values():
        spine.set_color(color)
    for spine in ax2.spines.values():
        spine.set_color(color)
    # Tick-Farbe (Striche + Zahlen)
    ax1.tick_params(axis="both", colors=color)
    ax2.tick_params(axis="both", colors=color)
