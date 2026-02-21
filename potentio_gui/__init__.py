"""The Captura Main Module

This module contains the main entry point for the Captura application.

Captura is a templating program, that allows you to fill out LaTeX templates
from a predefined template and generate different kinds of LaTeX documents.
Due to its modular design, it is easily extensible with new templates."""

__version__: str = "0.1.0"
"""The current version of the Potentio_gui application."""

production: bool = False
"""Indicates whether the application is running in production mode or development mode."""

environment: str = "linux"
"""The current environment in which the application is running.

This can be `linux`, `windows`, or `macos`."""


import pandas as pd
import matplotlib.pyplot as plt
from potentio_gui.lib.potentiometrie import create_plot
import xlwings as xw
@xw.func
def excel_plot(vol_naoh: pd.Series, ph_werte: pd.Series) -> str:
  fig = plt.figure()
  subplots = fig.subplots()
  create_plot(vol_naoh, ph_werte, subplots)

  sheet = xw.Book().sheets[0]
  sheet.pictures.add(fig, name='Titrationskurve', update=True)
  return "Plot erfolgreich erstellt!"

