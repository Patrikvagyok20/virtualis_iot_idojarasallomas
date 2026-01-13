#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import random
import sys
import time
from datetime import datetime, timezone

import requests


def veletlen_idojaras_adatok():
    homerseklet_c = round(random.uniform(18.0, 32.0), 2)
    paratartalom_szazalek = round(random.uniform(35.0, 80.0), 2)
    legnyomas_hpa = round(random.uniform(980.0, 1035.0), 2)
    return homerseklet_c, paratartalom_szazalek, legnyomas_hpa


def thingspeak_feltoltes(api_kulcs, homerseklet_c, paratartalom_szazalek, legnyomas_hpa, timeout_masodperc=10):
    vegpont = "https://api.thingspeak.com/update"
    parameterek = {
        "api_key": api_kulcs,
        "field1": homerseklet_c,
        "field2": paratartalom_szazalek,
        "field3": legnyomas_hpa,
    }
    valasz = requests.get(vegpont, params=parameterek, timeout=timeout_masodperc)
    try:
        szoveg = valasz.text.strip()
    except Exception:
        szoveg = ""
    if valasz.status_code != 200:
        return False, f"HTTP {valasz.status_code}"
    if not szoveg or szoveg == "0":
        return False, "ThingSpeak nem fogadta el a feltöltést (0)"
    return True, szoveg


def argumentumok():
    parser = argparse.ArgumentParser(prog="virtualis_idojarasallomas.py")
    parser.add_argument("--api-kulcs", dest="api_kulcs", default=os.getenv("THINGSPEAK_API_KULCS", ""), help="ThingSpeak Write API Key")
    parser.add_argument("--periodus", dest="periodus_masodperc", type=int, default=15, help="Feltöltési periódus másodpercben (ThingSpeak minimum 15)")
    parser.add_argument("--feltoltesek", dest="feltoltesek_szama", type=int, default=0, help="Ennyi feltöltés után leáll (0 = végtelen)")
    parser.add_argument("--csak-demo", dest="csak_demo", action="store_true", help="Nem küld felhőbe, csak kiírja az adatokat")
    return parser.parse_args()


def main():
    args = argumentumok()

    if args.periodus_masodperc < 15 and not args.csak_demo:
        print("Figyelem: ThingSpeak esetén a javasolt minimum 15 másodperc. Beállítva: 15.")
        args.periodus_masodperc = 15

    if not args.api_kulcs and not args.csak_demo:
        print("Nincs megadva API kulcs. Indítsd --csak-demo módban, vagy add meg --api-kulcs paraméterrel / THINGSPEAK_API_KULCS környezeti változóval.")
        return 2

    probalkozasok = 0
    sikeres = 0

    while True:
        probalkozasok += 1
        homerseklet_c, paratartalom_szazalek, legnyomas_hpa = veletlen_idojaras_adatok()
        idobelyeg = datetime.now(timezone.utc).isoformat(timespec="seconds")

        if args.csak_demo:
            print(f"{idobelyeg} | T={homerseklet_c}C | RH={paratartalom_szazalek}% | P={legnyomas_hpa}hPa")
            uzenet = "DEMO"
            siker = True
        else:
            siker, uzenet = thingspeak_feltoltes(args.api_kulcs, homerseklet_c, paratartalom_szazalek, legnyomas_hpa)

            if siker:
                sikeres += 1
                print(f"{idobelyeg} | Feltöltve (entry_id={uzenet}) | T={homerseklet_c}C | RH={paratartalom_szazalek}% | P={legnyomas_hpa}hPa")
            else:
                print(f"{idobelyeg} | Hiba: {uzenet} | T={homerseklet_c}C | RH={paratartalom_szazalek}% | P={legnyomas_hpa}hPa")

        if args.feltoltesek_szama and probalkozasok >= args.feltoltesek_szama:
            if args.csak_demo:
                print(f"Kész. Mérések: {probalkozasok}")
            else:
                print(f"Kész. Feltöltések: {sikeres}/{probalkozasok}")
            break

        time.sleep(max(1, args.periodus_masodperc))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
