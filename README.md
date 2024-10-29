# Vytváranie faktúr
Skripty pre rýchle vytváranie faktúr na STROMácke akcie.

## Návod pre vyplnenie súborov na akciu
1. Nájdi v priečinku `templates` súbory k typu akcie, na ktorú chceš faktúry vytvoriť.
2. Vyplň údaje v `.csv` všetky údaje. Ak fakturujeme na osobu, stačí vyplniť to čo uviedli. Ak fakturujeme na firmu treba uviesť všetko aj IČO. Postupuj ako v návode nižšie.
3. Vyplň nastavenia v `.yaml` súbore. Podľa návodu nižšie.
4. Pošli oba súbory na mail osobe, ktorá má povolenie spravovať faktúry.

### Vyplnenie údajov o odberateľoch (`.csv` súbor)

Popis možných stĺpcov:
 - `o_name` - Meno firmy, školy alebo rodiča, prípadne účastníka (ak už mal 18).
 - `o_street` - Ulica s číslom sídla firmy/bydlisko
 - `o_city` - Mesto sídla
 - `o_state` - Štát sídla. Zvyčajne Slovensko.
 - `o_zip` - PSČ
 - `o_ico` - IČO v prípade firmy. Ak sa jedná o rodiča/ účastníka ostáva prázdne.
 - `o_dic` - DIČ v prípade firmy. Ak sa jedná o rodiča/ účastníka ostáva prázdne.
 - `o_icdph` - 
 - `o_email` - Email (nepovinné)
 - `ucastnicky` - pocet kusov, kolkokrat danu vec uhradzaju (1)
 - `f_paid` - Suma, ktorá už bola uhradená
 - `i_date_paid` - Dátum úhrady. Je potrebné vyplniť iba ak bolo niečo vyplnené v `f_paid`.
 - `f_payment` - Možné hodnoty: `hotovost`,`prevod`,`karta`. Ak nie je uvedené, defaultne sa použije `prevod`
 - `f_original_num` - Ak vystavujeme opravnú faktúru(dobropis/ťarchopis), číslo pôvodnej faktúry, ktorú opravujeme

Ďalej je možné doplniť vlastné stĺpce a to konkrétne dva typy.
1. Prvý typ má `i_*` musíme mať teda prefix `i_`. Napríklad `i_meno_ucastnika`. Takýto stĺpec.
2. Druhý typ sú položky. Napríklad účastnícky poplatok alebo bageta. Názov stĺpca musí zodpovedať položke v nastaveniach pod kľúčom `polozky`. Tieto názvy nesmú mať prefixy `i_`, `o_`, `f_`.

Ďalej je možné aplikovať ďalšie polia podľa návodu [https://www.faktury-online.com/faktury-online-api/manual](https://www.faktury-online.com/faktury-online-api/manual)

### Vyplnenie nastavení (`.yaml` súbor)
Konfiguračný súbor obsahuje informácie spoločné pre všetky faktúry. Konkrétne:
- `vystavil` - Meno osoby, ktorá faktúru vystavila. Zvyčajne niekto zo štatutárov
- `datum_dodania` - Deň dodania služby/výrobku, prípadne deň konania akcie. Ak je akcia viacdňová jej posledný deň. Dátum je vo formáte `DD.MM.YYYY`
- `datum_vystavenia` - deň, keď faktúru vytvárame. Dátum je vo formáte `DD.MM.YYYY`
- `datum_splatnosti` - do kedy je nutné faktúru uhradiť. Zvyknú sa dávať dva týždne. Prípadne do termínu úhrady na pozvánkach na akciu
- `typ` - Nepovinné, defaultne sa použije faktúra. Možné hodnoty sú `faktura`,`dobropis`,`tarchopis`
- `poznamka` - Text, ktorý je uvedený nad položkami faktúry. Použiť napríklad pri zdôvodnení vydania opravnej faktúry
- `tagy` - Zoznam tagov pre zaradenie na portáli. Pre zoznam povolených pozri zoznam tagov na faktury-online.com . Zvyčajne sa jedná o názov súťaže bez diakritiky s prvým veľkým písmenom.
- `polozky` - Zoznam poloziek. Identifikátor (vo vzore napríklad `bageta` a `bageta_storno` sa použije na pripárovania k rovnomennému stĺpcu v csvčku). Následne každá položka má ako vlastnosti
  - `nazov_polozky` - Tak bude polozka pomenovaná na faktúre. Môže obsahovať aj formátovateľné stringy(Ťahané zo stĺpcov z prefixom `i_`). Napríklad `{i_meno_ucastnika}` bude vo fakture nahradené menom účastníka z csv 
  - `jednotka` - napríklad kus, deň ...
  - `cena` - Cena za jednotku položky. Použite destinnú bodku

Príklad:

```
vystavil: Mgr. Jožko Mrkvička
datum_dodania: 1.1.2024
datum_vystavenia: 1.1.2024
datum_splatnosti: 1.1.2024
typ: tarchopis
poznamka: Táto faktúra opravuje chybnú sumu za bagety na pôvodnej faktúre
tagy:
  - Matboj
polozky:
  bageta_storno:
    nazov_polozky: Storno bageta s chybnou cenou
    jednotka: ks
    cena: -1.50
  bageta:
    nazov_polozky: Bageta
    jednotka: ks
    cena: 1.75
```

## Návod pre prácu so scriptami

### Setup

Pre spustenie treba najprv nainštalovať dependencie:
```
pip install -r requirements.txt
```
Pre zakladanie faktúr je potrebné taktiež pridať file s názvom `api_key.txt` do priečinka `.secrets`. Do tohto súboru skopíruj API kľúč z nášho konta na faktury-online.com

### Spustenie
Pre vytvorenie faktúry použi príkaz
```
python faktury.py skontroluj sustredenie
```

```
python faktury.py vytvor sustredenie
```

Generovanie výstupu do denníka
```
python faktury.py dennik 2023-01-01 2023-01-31
```