import matplotlib.pyplot as plt  # https://matplotlib.org/
from matplotlib import ticker  # https://matplotlib.org/stable/api/ticker_api.html
from matplotlib.collections import PolyCollection, PathCollection  # https://matplotlib.org/stable/api/collections_api.html
from matplotlib.widgets import RangeSlider, CheckButtons  # https://matplotlib.org/stable/api/widgets_api.html
from matplotlib.legend_handler import HandlerTuple  # https://matplotlib.org/stable/api/legend_handler_api.html
import colorsys  # https://docs.python.org/3/library/colorsys.html
import math  # https://docs.python.org/3/library/math.html
import numpy as np  # https://numpy.org/
import scipy as sp  # https://scipy.org/
import pandas as pd  # https://pandas.pydata.org/docs/index.html
import seaborn as sns  # https://seaborn.pydata.org/index.html
plt.rcParams['figure.dpi'] = 150  # Aumento i DPI per le visualizzazioni raster

sns.set_theme(style="darkgrid", context="talk")  # Scelta del tema di Seaborn
df_partenze = pd.read_pickle("Partenze.pickle")  # Importazione DataFrame Partenze
df_partenze['DeltaStart'] = df_partenze['GridPosition'] - df_partenze['Lap1Position']  # Calcolo Variabile Globale 1
df_partenze['DeltaEnd'] = df_partenze['GridPosition'] - df_partenze['ClassifiedPosition']  # Calcolo Variabile Globale 2

def grafico_classifica_partenze(df_partenze, dimensioni_grafico):
    """
    Crea il terzo grafico, della seconda parte di analisi.

    :param df_partenze: Pandas DataFame che contiene le informazioni sulle partenze in F1
    :param dimensioni_grafico: tupla contentente le dimensioni di larghezza e altezza da dare al grafico
    :returns: oggetti fig e ax (contenitore alto-livello del grafico e assi della figura)
    """

    df_partenze = df_partenze.groupby('DriverId').agg({'DriverAbbreviation': "last",
                                                       'DriverName': "last",
                                                       'Style': "last",
                                                       'GridPosition': "mean",
                                                       'DeltaStart': "mean",
                                                       'ClassifiedPosition': "count"
                                                       })  # Dopo aver raggrupato per piloti, applico le aggregazioni per ottenere la classifica

    lista_categorie = ["≤1 stagione", "≤3 stagioni", "4+ stagioni"]  # Definisco una lista di categorie per il count

    def assegna_categoria(numero_partenze):
        """
        Metodo che assegna la categoria al numero di partenze di un pilota.

        :param numero_partenze: numero di partenze del singolo pilota
        :returns: categoria a cui appartiene il singolo numero di partenze
        """

        if numero_partenze <= 25:  # Una stagione, circa 20 gare
            return lista_categorie[0]
        elif numero_partenze <= 80:  # Quattro stagioni, circa 80 gare
            return lista_categorie[1]
        else:  # Più di quattro stagioni
            return lista_categorie[2]

    df_partenze['CategoriaPartenze'] = df_partenze['ClassifiedPosition'].apply(assegna_categoria)  # Applico la funzione di categorizzazione

    serie_annotazioni = pd.Series(data=[])  # Creo una serie vuota dove memorizzare le annotazioni

    def plotting_scatter(df_partenze):
        """
        Metodo che crea il grafico con il plotting di marker, etichette e annotazioni

        :param df_partenze: Pandas DataFame che contiene le informazioni sulle partenze in F1, filtrato sui valori di GridPosition
        """

        for annotazione in ax.texts:
            annotazione.remove()  # Rimuovo i testi sopra i marker
        for marker in ax.collections:
            marker.remove()  # Rimuovo i marker sul grafico

        df_partenze = df_partenze[df_partenze['CategoriaPartenze'].isin(check_buttons_categoria.get_checked_labels())]  # Filtro il DataFrame secondo le categorie abilitate

        delta_min, delta_max = df_partenze['DeltaStart'].min(), df_partenze['DeltaStart'].max()  # Calcolo i valori limite dell'asse Y
        y_padding = (delta_max - delta_min) * 0.05  # Calcolo il padding dell'asse Y
        ax.set_ylim(delta_min - y_padding, delta_max + y_padding)  # Applico i nuovi limiti

        for indice, pilota in df_partenze.iterrows():

            ax.scatter(
                x=pilota['GridPosition'],
                y=pilota['DeltaStart'],
                c=pilota['Style']['color'],
                alpha=0.8,
                marker=pilota['Style']['marker'],
                facecolor=pilota['Style']['edgecolor'],
                s=200 * math.pow(delta_max - delta_min, -1),
                gid=indice
            )  # Plotting Piloti

            ax.text(
                x=pilota['GridPosition'],
                y=pilota['DeltaStart'] + math.pow(delta_max - delta_min, -0.5) * 0.1,
                s=pilota['DriverAbbreviation'],
                fontsize=14 * math.pow(delta_max - delta_min, -0.25),
                fontweight="bold",
                ha="center",
                c="black",
                transform=ax.transData
            )  # Plotting Identificatori

            annotazione = ""   # Creo il testo dell'annotazione
            annotazione += pilota['DriverName'] + "\n"
            annotazione += "P. Partenza μ = " + str(round(pilota['GridPosition'], 2)) + "\n"
            annotazione += "Δ Start μ = " + str(round(pilota['DeltaStart'], 2)) + "\n"
            annotazione += "N° Partenze = " + str(pilota['ClassifiedPosition'])

            serie_annotazioni.loc[indice] = ax.annotate(
                text=annotazione,
                xy=(pilota['GridPosition'], pilota['DeltaStart']),
                xytext=(-140, 0),
                textcoords="offset points",
                visible=False,
                zorder=10,
                fontsize=12,
                bbox=dict(boxstyle="round", facecolor="white"),
                arrowprops=dict(arrowstyle="<-", edgecolor="black")
            )  # Plotting Annotazioni Esplicative

        fig.canvas.draw_idle()  # Come ultima cosa, aggiorno la figura

    def aggiorna_check_buttons(val):
        """
        Metodo invocato ogni qual volta viene eseguita un'azione sui check buttons

        :param val: valore dei check buttons
        """

        grid_min, grid_max = ax.get_xlim()[0], ax.get_xlim()[1]  # Ricavo i limiti Asse X
        plotting_scatter(df_partenze[(df_partenze['GridPosition'] >= grid_min) &
                                     (df_partenze['GridPosition'] <= grid_max)].copy())  # Ricreo il plotting con i nuovi limiti

    def aggiorna_slider(val):
        """
        Metodo invocato ogni qual volta viene eseguita un'azione sul range slider

        :param val: valore dello slider
        """

        grid_min, grid_max = slider_posizione_partenza.val  # Ricavo i limiti Asse X
        ax.set_xlim(grid_min, grid_max)  # Applico i nuovi limiti
        plotting_scatter(df_partenze[(df_partenze['GridPosition'] >= grid_min) &
                                     (df_partenze['GridPosition'] <= grid_max)].copy())  # Ricreo il plotting con i nuovi limiti

    ultima_annotazione = None  # Variabile sentinella che punta all'ultima annotazione

    def gestisci_hover(event):
        """
        Metodo invocato ogni qual volta si passa il mouse all'interno della figura

        :param event: evento hover
        """

        nonlocal ultima_annotazione
        if ultima_annotazione is not None:
            serie_annotazioni.loc[ultima_annotazione].set_visible(False)  # Nascondo l'annotazione
            ultima_annotazione = None  # Reimposto il riferimento all'annotazione
        for child in ax.get_children():
            if isinstance(child, PathCollection):
                if child.contains(event)[0]:
                    pilota = child.get_gid()  # Ottengo l'id pilota, collegato all'annotazione
                    serie_annotazioni.loc[pilota].set_visible(True)  # Visualizzo l'annotazione
                    ultima_annotazione = pilota  # Salvo il riferimento all'annotazione

        fig.canvas.draw_idle()  # Come ultima cosa, aggiorno la figura

    fig = plt.figure(figsize=dimensioni_grafico)  # Creazione Plot Figure
    ax = plt.axes()  # Creazione Plot Axes

    fig.subplots_adjust(left=0.15)  # Aggiungo spazio a sinistra della figura
    fig.subplots_adjust(bottom=0.20)  # Aggiungo spazio al di sotto della figura

    check_buttons_ax = fig.add_axes((0.0, 0.0, 0.152, 0.202))  # Creo lo spazio per il gruppo di check buttons
    check_buttons_categoria = CheckButtons(ax=check_buttons_ax, labels=lista_categorie, actives=[True] * len(lista_categorie))  # Creo i check buttons
    check_buttons_categoria.on_clicked(aggiorna_check_buttons)  # Imposto l'azione da eseguire al click dei buttons
    for etichetta in check_buttons_categoria.labels:
        etichetta.set_fontsize(12)  # Imposto la dimensione del testo delle etichette
        etichetta.set_fontstyle("italic")  # Imposto lo stile del testo delle etichette
    fig.text(x=0.075, y=0.21, s="Filtro N° Gare", fontstyle="italic", fontsize=12, ha="center", transform=fig.transFigure)  # Titolo del gruppo

    x_min, x_max = math.floor(df_partenze['GridPosition'].min()), math.ceil(df_partenze['GridPosition'].max())
    slider_ax = fig.add_axes((0.2125, 0.04, 0.6, 0.035))  # Creo lo spazio per lo slider
    slider_ax.set_title("P. Partenza μ", fontsize=16, fontstyle='italic')  # Imposto il titolo all'asse/slider
    slider_posizione_partenza = RangeSlider(slider_ax, "", x_min, x_max, valinit=(x_min, x_max), color="dimgray", track_color="lightgray")  # Creo lo slider
    slider_posizione_partenza.on_changed(aggiorna_slider)  # Imposto l'azione da eseguire al cambio del range

    fig.canvas.mpl_connect('motion_notify_event', gestisci_hover)  # Imposto una funzione associata all'hover nel grafico

    plotting_scatter(df_partenze.copy())  # Primo Plotting

    coefficienti_regressione = np.polyfit(df_partenze['GridPosition'], df_partenze['DeltaStart'], 1)  # Calcolo i coeff. polinomiali, funzione 1° grado
    funzione_regressione = np.poly1d(coefficienti_regressione)  # Ricava la funzione polinomiale per la regressione, a partire dai coefficienti
    spazio_lineare = np.linspace(df_partenze['GridPosition'].min(), df_partenze['GridPosition'].max(), 1000)  # Creo lo spazio lineare per i "valori x"
    ax.plot(spazio_lineare, funzione_regressione(spazio_lineare), linewidth=1.0, color="dimgray")  # Rappresento la funzione di regressione

    titolo = "Classifica Partenze Piloti"
    ax.set_title(label=titolo, fontweight="bold", pad=20)  # Titolo Figure

    # ax.set_xlabel(xlabel="P. Partenza μ", fontstyle="italic", labelpad=15)  # Titolo X Axis -> Rimosso, incluso nello slider
    ax.set_ylabel(ylabel="Δ Start μ", fontstyle="italic", labelpad=15)  # Titolo Y Axis

    ax.tick_params(axis="x", labelsize=16, colors="dimgray", grid_linewidth=1.0)  # Proprietà Labels X Axis
    ax.tick_params(axis="y", labelsize=16, colors="dimgray", grid_linewidth=1.0)  # Proprietà Labels Y Axis

    return fig, ax  # Return oggetti fig e ax


sns.set_theme(style="darkgrid", context="talk")
fig, ax = grafico_classifica_partenze(df_partenze.copy(), (10, 6))
plt.show()